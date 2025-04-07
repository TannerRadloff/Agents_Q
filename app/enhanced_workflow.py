from app.agents.enhanced_plan_creation_agent import EnhancedPlanCreationAgent
from app.agents.enhanced_workflow_execution_agent import EnhancedWorkflowExecutionAgent
from app.models import Step, PlanOutput, WorkflowState
from agents import Runner
import asyncio
import uuid
from typing import Dict, Any, List, Callable, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# In-memory storage for workflow states
workflow_sessions = {}

class EnhancedWorkflow:
    """Enhanced workflow manager with improved capabilities."""
    
    def __init__(self, model_name: str = "o3-mini"):
        """Initialize the enhanced workflow manager.
        
        Args:
            model_name: Name of the OpenAI model to use
        """
        self.plan_creation_agent = EnhancedPlanCreationAgent(model_name=model_name)
        self.execution_agent = EnhancedWorkflowExecutionAgent(model_name=model_name)
        logger.info(f"Enhanced Workflow initialized with model: {model_name}")
    
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
            return self.plan_creation_agent.create_plan_with_examples(user_input, examples)
        else:
            return self.plan_creation_agent.agent.run_sync(user_input)
    
    async def refine_plan(self, plan: PlanOutput, feedback: str) -> PlanOutput:
        """Refine a plan based on user feedback.
        
        Args:
            plan: The original plan
            feedback: User feedback for refinement
            
        Returns:
            Refined plan
        """
        logger.info(f"Refining plan based on feedback: {feedback[:50]}...")
        return self.plan_creation_agent.refine_plan(plan, feedback)
    
    async def analyze_plan(self, plan: PlanOutput) -> Dict[str, Any]:
        """Analyze the quality of a plan.
        
        Args:
            plan: The plan to analyze
            
        Returns:
            Analysis results
        """
        logger.info(f"Analyzing plan quality for plan with {len(plan.steps)} steps")
        return self.plan_creation_agent.analyze_plan_quality(plan)
    
    async def execute_plan(self, session_id: str, steps: List[Step], on_update: Callable[[str], None]) -> str:
        """Execute a plan step by step.
        
        Args:
            session_id: Workflow session ID
            steps: List of steps to execute
            on_update: Callback function for progress updates
            
        Returns:
            Final execution result
        """
        workflow = workflow_sessions[session_id]
        workflow.total_steps = len(steps)
        workflow.status = "in_progress"
        
        logger.info(f"Executing plan with {len(steps)} steps for session {session_id}")
        
        try:
            # Execute steps with dependency tracking
            results = []
            for i, step in enumerate(steps):
                # Update workflow state
                workflow.current_step_index = i
                update_message = f"Starting step {i+1}/{len(steps)}: {step.title}"
                workflow.updates.append(update_message)
                on_update(update_message)
                logger.info(update_message)
                
                try:
                    # Execute the step
                    context = {f"step_{j+1}_result": results[j]['result'] for j in range(i) if j < len(results)}
                    step_result = self.execution_agent.execute_step(step, context)
                    
                    # Store the result
                    results.append(step_result)
                    workflow.steps_results.append(step_result['result'])
                    
                    # Update workflow state
                    tools_used = ", ".join(step_result['tools_used']) if step_result['tools_used'] else "none"
                    completion_message = f"Completed step {i+1}: {step.title} (Tools used: {tools_used})"
                    workflow.updates.append(completion_message)
                    on_update(completion_message)
                    logger.info(completion_message)
                    
                except Exception as e:
                    error_message = f"Error in step {i+1}: {str(e)}"
                    workflow.updates.append(error_message)
                    on_update(error_message)
                    logger.error(error_message, exc_info=True)
                    results.append({
                        'step': step,
                        'result': f"Failed: {str(e)}",
                        'tools_used': [],
                        'success': False
                    })
                    workflow.steps_results.append(f"Failed: {str(e)}")
            
            # Generate final report
            final_result = self._generate_final_report(steps, results)
            
            # Update workflow state
            workflow.status = "completed"
            workflow.final_result = final_result
            completion_message = "Workflow completed successfully!"
            workflow.updates.append(completion_message)
            on_update(completion_message)
            logger.info(f"Workflow {session_id} completed successfully")
            
            return final_result
            
        except Exception as e:
            error_message = f"Workflow execution failed: {str(e)}"
            workflow.updates.append(error_message)
            workflow.status = "failed"
            on_update(error_message)
            logger.error(error_message, exc_info=True)
            return f"Workflow execution failed: {str(e)}"
    
    def _generate_final_report(self, steps: List[Step], results: List[Dict[str, Any]]) -> str:
        """Generate a final report from the execution results.
        
        Args:
            steps: List of steps executed
            results: List of execution results
            
        Returns:
            Formatted report
        """
        report = "# Workflow Execution Report\n\n"
        report += "## Summary\n\n"
        report += f"Executed {len(steps)} steps in the workflow.\n\n"
        
        success_count = sum(1 for r in results if r.get('success', False))
        report += f"- Successfully completed: {success_count}/{len(steps)} steps\n"
        report += f"- Failed: {len(steps) - success_count}/{len(steps)} steps\n\n"
        
        report += "## Detailed Results\n\n"
        
        for i, (step, result) in enumerate(zip(steps, results)):
            report += f"### Step {i+1}: {step.title}\n\n"
            report += f"**Description:** {step.description}\n\n"
            report += f"**Result:** {result['result']}\n\n"
            
            if result.get('tools_used'):
                report += f"**Tools Used:** {', '.join(result['tools_used'])}\n\n"
            
            report += "---\n\n"
        
        return report

def create_workflow_session() -> str:
    """Create a new workflow session and return its ID."""
    session_id = str(uuid.uuid4())
    workflow_sessions[session_id] = WorkflowState(session_id=session_id)
    logger.info(f"Created new workflow session: {session_id}")
    return session_id

def get_workflow_state(session_id: str) -> Optional[WorkflowState]:
    """Get the current state of a workflow session."""
    return workflow_sessions.get(session_id)

def accept_plan(session_id: str) -> bool:
    """Mark a plan as accepted and ready for execution."""
    if session_id not in workflow_sessions:
        logger.warning(f"Attempted to accept plan for non-existent session: {session_id}")
        return False
    
    workflow_sessions[session_id].accepted_plan = True
    workflow_sessions[session_id].status = "accepted"
    logger.info(f"Plan accepted for session: {session_id}")
    return True

# Create a singleton instance
enhanced_workflow = EnhancedWorkflow()
