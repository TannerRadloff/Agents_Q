from agents import Runner
from app.models import Step, PlanOutput, WorkflowState
from app.agents.plan_creation_agent import plan_creation_agent
from app.agents.workflow_execution_agent import execution_agent
import asyncio
import uuid
from typing import Dict, Any, List, Callable, Optional

# In-memory storage for workflow states
workflow_sessions = {}

async def create_plan(user_input: str) -> PlanOutput:
    """Call the plan creation agent to produce a structured plan."""
    result = await Runner.run(plan_creation_agent, user_input)
    return result.final_output_as(PlanOutput)

async def run_plan(session_id: str, steps: List[Step], on_update: Callable[[str], None]) -> str:
    """Execute each step in the plan using the Execution Agent."""
    workflow = workflow_sessions[session_id]
    workflow.total_steps = len(steps)
    workflow.status = "in_progress"
    
    final_results = []
    
    for i, step in enumerate(steps):
        # Update workflow state
        workflow.current_step_index = i
        update_message = f"Starting step {i+1}/{len(steps)}: {step.title}"
        workflow.updates.append(update_message)
        on_update(update_message)
        
        try:
            # Provide the step description to the Execution Agent
            exec_result = await Runner.run(execution_agent, step.description)
            
            # Store the result
            step_result = exec_result.final_output
            final_results.append(step_result)
            workflow.steps_results.append(step_result)
            
            # Update workflow state
            completion_message = f"Completed step {i+1}: {step.title}"
            workflow.updates.append(completion_message)
            on_update(completion_message)
            
        except Exception as e:
            error_message = f"Error in step {i+1}: {str(e)}"
            workflow.updates.append(error_message)
            on_update(error_message)
            final_results.append(f"Failed: {str(e)}")
            workflow.steps_results.append(f"Failed: {str(e)}")
    
    # Summarize final results
    final_result = "\n\n".join([
        f"Step {i+1}: {step.title}\n{result}" 
        for i, (step, result) in enumerate(zip(steps, final_results))
    ])
    
    # Update workflow state
    workflow.status = "completed"
    workflow.final_result = final_result
    completion_message = "Workflow completed successfully!"
    workflow.updates.append(completion_message)
    on_update(completion_message)
    
    return final_result

def create_workflow_session() -> str:
    """Create a new workflow session and return its ID."""
    session_id = str(uuid.uuid4())
    workflow_sessions[session_id] = WorkflowState(session_id=session_id)
    return session_id

def get_workflow_state(session_id: str) -> Optional[WorkflowState]:
    """Get the current state of a workflow session."""
    return workflow_sessions.get(session_id)

def accept_plan(session_id: str) -> bool:
    """Mark a plan as accepted and ready for execution."""
    if session_id not in workflow_sessions:
        return False
    
    workflow_sessions[session_id].accepted_plan = True
    workflow_sessions[session_id].status = "accepted"
    return True
