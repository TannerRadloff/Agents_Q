from app.agents.enhanced_plan_creation_agent import EnhancedPlanCreationAgent
from app.agents.enhanced_workflow_execution_agent import EnhancedWorkflowExecutionAgent
from app.models import Step, PlanOutput, WorkflowState
from agents import Runner
import asyncio
import uuid
from typing import Dict, Any, List, Callable, Optional
import logging
from .extensions import db
from .database_models import WorkflowSessionDB
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_workflow_db(session_id: str) -> Optional[WorkflowSessionDB]:
    """Gets the WorkflowSessionDB object from the database."""
    return WorkflowSessionDB.query.get(session_id)

def load_workflow_state(session_id: str) -> Optional[WorkflowState]:
    """Loads the workflow state from the database and returns a Pydantic model."""
    session_db = get_workflow_db(session_id)
    if not session_db:
        logger.warning(f"Workflow session {session_id} not found in DB.")
        return None

    # Convert DB model to Pydantic model
    try:
        state = WorkflowState(
            session_id=session_db.id,
            plan=session_db.plan, # Uses the @property getter
            accepted_plan=session_db.accepted_plan,
            current_step_index=session_db.current_step_index,
            total_steps=session_db.total_steps,
            steps_results=session_db.steps_results, # Uses the @property getter
            status=session_db.status,
            updates=session_db.updates, # Uses the @property getter
            final_result=session_db.final_result
        )
        # logger.info(f"Successfully loaded session state {session_id} from DB.")
        return state
    except Exception as e:
        logger.error(f"Error converting DB model to Pydantic for session {session_id}: {e}", exc_info=True)
        return None

def save_workflow_state(workflow: WorkflowState) -> bool:
    """Saves the Pydantic WorkflowState model to the database."""
    try:
        session_db = get_workflow_db(workflow.session_id)
        if not session_db:
            # Create new DB entry
            session_db = WorkflowSessionDB(id=workflow.session_id)
            db.session.add(session_db) # Add to session before setting attributes
            logger.info(f"Creating new DB entry for session {workflow.session_id}")

        # Update DB model fields from Pydantic model
        session_db.plan = workflow.plan # Uses the @plan.setter
        session_db.accepted_plan = workflow.accepted_plan
        session_db.current_step_index = workflow.current_step_index
        session_db.total_steps = workflow.total_steps
        session_db.steps_results = workflow.steps_results # Uses the @steps_results.setter
        session_db.status = workflow.status
        session_db.updates = workflow.updates # Uses the @updates.setter
        session_db.final_result = workflow.final_result

        db.session.commit() # Commit changes to the database
        # logger.info(f"Successfully saved session state {workflow.session_id} to DB.")
        return True
    except Exception as e:
        logger.error(f"Failed to save session state {workflow.session_id} to DB: {e}", exc_info=True)
        db.session.rollback() # Rollback in case of error
        return False

class EnhancedWorkflow:
    """Enhanced workflow manager with improved capabilities."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        """Initialize the enhanced workflow manager.
        
        Args:
            model_name: Name of the OpenAI model to use
        """
        self.plan_creation_agent = EnhancedPlanCreationAgent(model_name=model_name)
        self.execution_agent = EnhancedWorkflowExecutionAgent(model_name=model_name)
        logger.info(f"Enhanced Workflow initialized with model: {model_name}. State managed by DB.")
    
    async def create_plan(self, user_input: str, examples: List[Dict[str, Any]] = None) -> PlanOutput:
        """Create a plan for the user's request.
        
        Args:
            user_input: The user's request
            examples: Optional list of example plans to use as reference
            
        Returns:
            Generated plan
        """
        logger.info(f"Creating plan for user input: {user_input[:50]}...")
        
        if examples:
            return await self.plan_creation_agent.create_plan_with_examples(user_input, examples)
        else:
            # Use Runner.run to execute the agent
            result = await Runner.run(self.plan_creation_agent.agent, user_input)
            # Extract the PlanOutput from the result
            return result.final_output_as(PlanOutput)
    
    async def refine_plan(self, plan: PlanOutput, feedback: str) -> PlanOutput:
        """Refine a plan based on user feedback.
        
        Args:
            plan: The original plan
            feedback: User feedback for refinement
            
        Returns:
            Refined plan
        """
        logger.info(f"Refining plan based on feedback: {feedback[:50]}...")
        return await self.plan_creation_agent.refine_plan(plan, feedback)
    
    async def analyze_plan(self, plan: PlanOutput) -> Dict[str, Any]:
        """Analyze the quality of a plan.
        
        Args:
            plan: The plan to analyze
            
        Returns:
            Analysis results
        """
        logger.info(f"Analyzing plan quality for plan with {len(plan.steps)} steps")
        return await self.plan_creation_agent.analyze_plan_quality(plan)
    
    async def execute_plan(self, session_id: str, steps: List[Step], on_update: Callable[[str], None]) -> str:
        """Execute a plan step by step.
        
        Args:
            session_id: Workflow session ID
            steps: List of steps to execute
            on_update: Callback function for progress updates
            
        Returns:
            Final execution result
        """
        # Load state from DB using the standalone function
        workflow = load_workflow_state(session_id)
        if not workflow:
            error_msg = f"Session {session_id} not found in execute_plan (DB load failed)"
            logger.error(error_msg)
            # Attempt to update status in DB if possible, though unlikely to succeed
            error_state = WorkflowState(session_id=session_id, status="failed", updates=[error_msg])
            save_workflow_state(error_state)
            on_update(error_msg)
            return f"Workflow execution failed: {error_msg}"

        # Ensure we have steps from the loaded plan if steps arg is empty (robustness)
        if not steps and workflow.plan:
            steps = workflow.plan.steps
        elif not steps:
             error_msg = f"No steps provided and no plan found in session {session_id} to execute."
             logger.error(error_msg)
             workflow.status="failed"
             workflow.updates.append(error_msg)
             save_workflow_state(workflow)
             on_update(error_msg)
             return f"Workflow execution failed: {error_msg}"

        workflow.total_steps = len(steps)
        workflow.status = "in_progress"
        # Clear previous results if re-running? For now, let's assume it appends or starts fresh based on loop
        # workflow.steps_results = []
        # workflow.updates = [] # Optionally clear updates too
        save_workflow_state(workflow)  # Save initial in_progress state

        logger.info(f"Executing plan with {len(steps)} steps for session {session_id} (DB state)")

        try:
            # Use the loaded workflow.steps_results to build context
            results_so_far = workflow.steps_results[:] # Copy for context building

            for i, step in enumerate(steps):
                # Check if step was already completed in a previous run (optional)
                if i < workflow.current_step_index and i < len(workflow.steps_results) and not workflow.steps_results[i].startswith("Failed:"):
                     logger.info(f"Skipping already completed step {i+1} for session {session_id}")
                     continue # Or load existing result

                workflow.current_step_index = i
                update_message = f"Starting step {i+1}/{len(steps)}: {step.title}"
                workflow.updates.append(update_message)
                on_update(update_message)
                logger.info(update_message)
                save_workflow_state(workflow)  # Save state before step execution

                try:
                    # Build context from results *actually* stored in the state up to this point
                    context = {f"step_{j+1}_result": res for j, res in enumerate(workflow.steps_results) if j < i}

                    # Use Runner.run for the execution agent directly
                    # Ensure the execution agent is accessible or initialized correctly
                    exec_result = await Runner.run(self.execution_agent.agent, step.description, context=context) # Pass context if Runner supports it
                    step_output = exec_result.final_output # Assuming final_output is the string result

                    # Append result - Handle potential overwrite if resuming
                    if i < len(workflow.steps_results):
                         workflow.steps_results[i] = step_output
                    else:
                         workflow.steps_results.append(step_output)

                    # Extract tool usage if available (Runner result might have this info)
                    tools_used_list = []
                    # Safely check for messages attribute before iterating
                    if hasattr(exec_result, 'messages') and exec_result.messages:
                        for msg in exec_result.messages:
                            if msg.tool_calls:
                                tools_used_list.extend([tc.name for tc in msg.tool_calls])
                    
                    tools_used_str = ", ".join(tools_used_list) if tools_used_list else "none"

                    completion_message = f"Completed step {i+1}: {step.title} (Tools used: {tools_used_str})"
                    workflow.updates.append(completion_message)
                    on_update(completion_message)
                    logger.info(completion_message)
                    save_workflow_state(workflow)  # Save state after step completion

                except Exception as e:
                    error_message = f"Error in step {i+1}: {str(e)}"
                    workflow.updates.append(error_message)
                    on_update(error_message)
                    logger.error(error_message, exc_info=True)

                    # Append failure result - Handle potential overwrite if resuming
                    failure_output = f"Failed: {str(e)}"
                    if i < len(workflow.steps_results):
                         workflow.steps_results[i] = failure_output
                    else:
                         workflow.steps_results.append(failure_output)

                    save_workflow_state(workflow)  # Save state after step failure

            # Regenerate final report based on potentially updated steps_results
            final_result_text = self._generate_final_report(steps, workflow.steps_results) # Pass raw results list

            workflow.status = "completed"
            workflow.final_result = final_result_text
            completion_message = "Workflow completed successfully!"
            workflow.updates.append(completion_message)
            on_update(completion_message)
            logger.info(f"Workflow {session_id} completed successfully (DB state)")
            save_workflow_state(workflow)  # Save final state

            return final_result_text

        except Exception as e:
            error_message = f"Workflow execution failed unexpectedly: {str(e)}"
            logger.error(error_message, exc_info=True)
             # Try to load state one last time to save error
            workflow = load_workflow_state(session_id)
            if workflow:
                workflow.updates.append(error_message)
                workflow.status = "failed"
                save_workflow_state(workflow) # Save error state
            on_update(error_message)
            return f"Workflow execution failed: {str(e)}"

    def _generate_final_report(self, steps: List[Step], results: List[str]) -> str:
        """Generate a final report from the execution results.
        
        Args:
            steps: List of steps executed
            results: List of execution results
            
        Returns:
            Formatted report
        """
        report = "# Workflow Execution Report\\n\\n"
        report += "## Summary\\n\\n"
        report += f"Attempted {len(steps)} steps in the workflow.\\n\\n"
        
        success_count = sum(1 for r in results if not r.startswith("Failed:"))
        report += f"- Successfully completed: {success_count}/{len(steps)} steps\\n"
        report += f"- Failed: {len(steps) - success_count}/{len(steps)} steps\\n\\n"
        
        report += "## Detailed Results\\n\\n"
        
        for i, (step, result) in enumerate(zip(steps, results)):
            report += f"### Step {i+1}: {step.title}\\n\\n"
            report += f"**Description:** {step.description}\\n\\n"
            report += f"**Result:** {result}\\n\\n" # Directly use the string result
            # Note: Tool usage info is lost here unless stored separately or parsed from result string
            report += "---\\n\\n"
        
        return report

def create_workflow_session() -> str:
    """Create a new workflow session and save its initial state to DB."""
    session_id = str(uuid.uuid4())
    logger.info(f"Creating new workflow session: {session_id}")
    initial_state = WorkflowState(session_id=session_id) # Pydantic model
    if save_workflow_state(initial_state): # Save to DB
        logger.info(f"Successfully created and saved initial state for session {session_id}")
    else:
        logger.error(f"Failed to save initial state for session {session_id}")
        # Depending on requirements, might want to raise an error here
    return session_id

def get_workflow_state(session_id: str) -> Optional[WorkflowState]:
     """Get the current state of a workflow session (Pydantic model) from DB."""
     # logger.info(f"Attempting to load workflow state for session: {session_id}")
     return load_workflow_state(session_id)

def accept_plan(session_id: str) -> bool:
    """Mark a plan as accepted and ready for execution in the DB."""
    workflow = load_workflow_state(session_id)
    if not workflow:
        logger.error(f"Accept plan failed: Session {session_id} not found.")
        return False

    # Check if plan exists (Pydantic model handles attribute checks)
    if not workflow.plan or not workflow.plan.steps:
         logger.error(f"Accept plan failed: Plan or plan steps missing for session {session_id}.")
         return False

    workflow.accepted_plan = True
    workflow.status = "accepted"
    if save_workflow_state(workflow):
        logger.info(f"Session {session_id}: Plan accepted and saved to DB.")
        return True
    else:
        logger.error(f"Accept plan failed: Could not save accepted state for session {session_id}")
        return False
