from app.agent_definitions.enhanced_plan_creation_agent import EnhancedPlanCreationAgent
from app.models import Task, TasksOutput, WorkflowState
from app.agent_registry import get_agent
from agents import Runner, RunResult
import asyncio
import uuid
from typing import Dict, Any, List, Callable, Optional, Set
import logging
import json
import time
import os
from flask_socketio import SocketIO

# Import repository functions
from .workflow_repository import load_workflow_state, save_workflow_state, get_workflow_state, accept_plan, create_workflow_session

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants for Statuses ---
STATUS_PENDING = "pending"
STATUS_READY = "ready"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped" # If dependencies fail

class EnhancedWorkflow:
    """Enhanced workflow manager with dependency-aware execution."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        """Initialize the enhanced workflow manager.
        
        Args:
            model_name: Name of the OpenAI model to use
        """
        self.plan_creation_agent = EnhancedPlanCreationAgent(model_name=model_name)
        logger.info(f"Enhanced Workflow initialized with model: {model_name}. State managed by repository.")
    
    async def create_plan(self, user_input: str, examples: List[Dict[str, Any]] = None) -> TasksOutput:
        """Create a plan for the user's request.
        
        Args:
            user_input: The user's request
            examples: Optional list of example plans to use as reference
            
        Returns:
            Generated plan (TasksOutput)
        """
        logger.info(f"Creating plan for user input: {user_input[:50]}...")
        
        # Call the consolidated method on the agent instance
        plan = await self.plan_creation_agent.generate_plan(user_input, examples)

        logger.info(f"Generated plan with {len(plan.tasks)} tasks.")
        # Basic validation
        if not plan or not plan.tasks:
             raise ValueError("Plan generation failed or produced an empty plan.")
        task_ids = {task.id for task in plan.tasks}
        for task in plan.tasks:
             if not task.id: raise ValueError("Plan contains task with missing ID.")
             if any(dep not in task_ids for dep in task.dependencies):
                 raise ValueError(f"Task {task.id} has invalid dependencies: {task.dependencies}")
        return plan
    
    async def refine_plan(self, plan: TasksOutput, feedback: str) -> TasksOutput:
        """Refine a plan based on user feedback.
        
        Args:
            plan: The original plan (TasksOutput)
            feedback: User feedback for refinement
            
        Returns:
            Refined plan (TasksOutput)
        """
        logger.info(f"Refining plan based on feedback: {feedback[:50]}...")
        # Note: The refine_plan method in the agent itself might need updates
        # to correctly parse/regenerate the new plan structure including dependencies/roles.
        # Assuming for now it handles it.
        return await self.plan_creation_agent.refine_plan(plan, feedback)
    
    async def analyze_plan(self, plan: TasksOutput) -> Dict[str, Any]:
        """Analyze the quality of a plan.
        
        Args:
            plan: The plan to analyze (TasksOutput)
            
        Returns:
            Analysis results
        """
        logger.info(f"Analyzing plan quality for plan with {len(plan.tasks)} tasks")
        # Note: The analyze_plan_quality method might need updates for new structure.
        return await self.plan_creation_agent.analyze_plan_quality(plan)
    
    async def execute_plan(self, session_id: str, socketio: SocketIO, on_update: Callable[[str, Optional[Dict]], None]) -> str:
        """Executes the accepted plan for the session using dependency graph logic.
        
        Args:
            session_id: Workflow session ID.
            socketio: The SocketIO instance for emitting artifact events.
            on_update: Callback function for progress updates.
            
        Returns:
            Final execution result summary.
        """
        # Use repository function to load state
        workflow = load_workflow_state(session_id)
        if not workflow or not workflow.plan or not workflow.accepted_plan:
            error_msg = f"Session {session_id} not found, has no plan, or plan not accepted."
            logger.error(error_msg)
            on_update(error_msg, None)
            return f"Workflow execution failed: {error_msg}"

        plan = workflow.plan
        tasks_map = {task.id: task for task in plan.tasks}
        total_tasks = len(tasks_map)
        completed_tasks: Set[str] = set()
        failed_tasks: Set[str] = set()
        running_async_tasks: Dict[str, asyncio.Task] = {}

        # Initialize statuses if not already present (e.g., first run)
        # Note: accept_plan in repository now handles initial status setup
        # if not workflow.step_statuses:
        #      workflow.step_statuses = {step_id: STATUS_PENDING for step_id in steps}

        # Resume: Update completed/failed sets based on loaded state
        for task_id, status in workflow.step_statuses.items():
            if status == STATUS_COMPLETED:
                completed_tasks.add(task_id)
            elif status == STATUS_FAILED:
                failed_tasks.add(task_id)
            elif status == STATUS_SKIPPED: # Treat skipped as failed for dependency checking
                 failed_tasks.add(task_id)
             # Reset running tasks from previous interrupted runs back to pending
            elif status == STATUS_RUNNING:
                 workflow.step_statuses[task_id] = STATUS_PENDING

        workflow.status = "in_progress"
        initial_update = f"Starting workflow execution for session {session_id} with {total_tasks} tasks."
        workflow.updates.append(initial_update)
        logger.info(initial_update)
        # Use repository function to save state
        save_workflow_state(workflow)
        on_update(initial_update, workflow.dict(include={'session_id', 'status', 'step_statuses'}))

        # Determine workspace root for reading artifact files
        try:
            WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            INSTANCE_FOLDER = os.path.join(WORKSPACE_ROOT, 'instance')
            if not os.path.exists(INSTANCE_FOLDER):
                os.makedirs(INSTANCE_FOLDER)
        except Exception as e:
            logger.error(f"Failed to determine or create instance folder path: {e}", exc_info=True)
            # Potentially fail the workflow early if instance folder is critical
            on_update(f"Error: Cannot access instance folder. {e}", None)
            return f"Workflow execution failed: Cannot access instance folder."

        while len(completed_tasks) + len(failed_tasks) < total_tasks:
            ready_tasks: List[str] = []
            for task_id, task_obj in tasks_map.items():
                # Check if task is pending and dependencies met
                if workflow.step_statuses.get(task_id) == STATUS_PENDING:
                    # Check if all dependencies are completed
                    if all(dep_id in completed_tasks for dep_id in task_obj.dependencies):
                         ready_tasks.append(task_id)
                    # Check if any dependency has failed -> skip this task
                    elif any(dep_id in failed_tasks for dep_id in task_obj.dependencies):
                         logger.warning(f"Skipping task {task_id} because dependency failed.")
                         workflow.step_statuses[task_id] = STATUS_SKIPPED
                         workflow.updates.append(f"Skipped task {task_obj.title} (ID: {task_id}) due to failed dependency.")
                         failed_tasks.add(task_id) # Treat skipped as failure for downstream checks
                         # Use repository function to save state
                         save_workflow_state(workflow)
                         on_update(f"Task '{task_obj.title}' skipped", workflow.dict(include={'session_id', 'status', 'step_statuses'}))

            if not ready_tasks and not running_async_tasks:
                # Should not happen if there are still pending tasks unless circular dependency or error
                pending_count = total_tasks - len(completed_tasks) - len(failed_tasks)
                if pending_count > 0:
                     error_msg = f"Workflow stalled: {pending_count} tasks pending but none are ready and no tasks running."
                     logger.error(error_msg)
                     # Mark remaining pending as failed?
                     for task_id, status in workflow.step_statuses.items():
                          if status == STATUS_PENDING:
                               workflow.step_statuses[task_id] = STATUS_FAILED
                               failed_tasks.add(task_id)
                     workflow.status = STATUS_FAILED
                     workflow.updates.append(error_msg)
                     # Use repository function to save state
                     save_workflow_state(workflow)
                     on_update(error_msg, workflow.dict(include={'session_id', 'status', 'step_statuses'}))
                     break # Exit main loop
                else:
                     # All tasks accounted for, loop should terminate naturally
                     pass

            # Launch ready tasks
            for task_id in ready_tasks:
                if task_id not in running_async_tasks:
                    task_obj = tasks_map[task_id]
                    logger.info(f"Launching task {task_obj.id}: {task_obj.title} (Role: {task_obj.agent_role})")
                    workflow.step_statuses[task_id] = STATUS_RUNNING
                    workflow.updates.append(f"Starting task: {task_obj.title} (ID: {task_id})")
                    save_workflow_state(workflow)
                    on_update(f"Starting task '{task_obj.title}'", workflow.dict(include={'session_id', 'status', 'step_statuses'}))

                    # Create and run task, passing the user query
                    async_task = asyncio.create_task(
                        self._execute_single_step(task_obj, workflow.steps_results, workflow.user_query)
                    )
                    running_async_tasks[task_id] = async_task

            # Wait for remaining tasks if any are still finishing (should be quick)
            if running_async_tasks:
                done, pending = await asyncio.wait(running_async_tasks.values(), timeout=60)
                for async_task_done in done:
                    task_id = next((tid for tid, t in running_async_tasks.items() if t == async_task_done), None)
                    if not task_id: 
                         logger.warning(f"Could not find task_id for completed async task {async_task_done}. Skipping.")
                         continue 
                         
                    try:
                         result = async_task_done.result()
                         logger.info(f"Async task for task {task_id} completed successfully.")

                         # Get the actual output data from the agent run
                         output_data = result.final_output

                         # Store the raw output_data (string or dict) as the step result for dependencies
                         workflow.steps_results[task_id] = output_data
                         workflow.step_statuses[task_id] = STATUS_COMPLETED
                         completed_tasks.add(task_id)
                         update_msg = f"Completed task: {tasks_map[task_id].title} (ID: {task_id})"
                         workflow.updates.append(update_msg)
                         save_workflow_state(workflow) # Save state immediately after storing result
                         on_update(f"Completed task: {tasks_map[task_id].title} (ID: {task_id[:10]}...)", workflow.dict(include={'session_id', 'status', 'step_statuses'}))

                         # Check if the output indicates a file artifact was created
                         if isinstance(output_data, dict) and output_data.get('type') == 'file_artifact':
                             filename = output_data.get('filename')
                             if filename:
                                 logger.info(f"Task {task_id} resulted in file artifact: {filename}")
                                 try:
                                     # Construct full path within the secured instance folder
                                     artifact_path = os.path.abspath(os.path.join(INSTANCE_FOLDER, filename))

                                     # Security check: Ensure the final path is still within INSTANCE_FOLDER
                                     if os.path.commonpath([INSTANCE_FOLDER]) != os.path.commonpath([INSTANCE_FOLDER, artifact_path]):
                                         logger.error(f"Security Error: Artifact path {artifact_path} resolved outside instance folder {INSTANCE_FOLDER}.")
                                     elif os.path.exists(artifact_path):
                                         with open(artifact_path, 'r', encoding='utf-8') as f:
                                             file_content = f.read()
                                             # Optional: Add size limit for content sent via socket
                                             MAX_SOCKET_CONTENT_SIZE = 50 * 1024 # 50KB limit
                                             if len(file_content.encode('utf-8')) > MAX_SOCKET_CONTENT_SIZE:
                                                 file_content = file_content[:MAX_SOCKET_CONTENT_SIZE] + "\n... [Content Truncated for UI Display] ..."
                                                 logger.warning(f"Truncated content of {filename} for UI display.")

                                             # Emit the new event with filename and content
                                             logger.info(f"Emitting file_artifact_update for {filename}")
                                             socketio.emit('file_artifact_update', {
                                                 'session_id': session_id,
                                                 'filename': filename,
                                                 'file_content': file_content
                                             }, room=session_id)
                                             socketio.sleep(0) # Allow event to be sent
                                     else:
                                         logger.warning(f"File artifact {filename} reported by task {task_id}, but not found at {artifact_path}.")
                                 except Exception as read_err:
                                     logger.error(f"Error reading or emitting artifact file {filename} for task {task_id}: {read_err}", exc_info=True)

                    except Exception as e:
                        logger.error(f"Async task for task {task_id} failed: {e}", exc_info=True)
                        workflow.step_statuses[task_id] = STATUS_FAILED
                        failed_tasks.add(task_id)
                        update_msg = f"Failed task: {tasks_map[task_id].title} (ID: {task_id}) - Error: {e}"
                        workflow.updates.append(update_msg)
                        # Save state after failed task completion
                        save_workflow_state(workflow)
                        on_update(f"Failed task '{tasks_map[task_id].title}' - Error: {e}", workflow.dict(include={'session_id', 'status', 'step_statuses'}))
                    finally:
                        # Remove task from running list regardless of outcome
                        if task_id in running_async_tasks:
                             del running_async_tasks[task_id]
                
                # Handle tasks that timed out
                if pending:
                     logger.error(f"{len(pending)} async tasks timed out during final wait.")
                     for async_task_pending in pending:
                         # Find task ID for timed out async task
                         task_id = next((tid for tid, t in running_async_tasks.items() if t == async_task_pending), None)
                         if task_id:
                             logger.error(f"Task {task_id} timed out.")
                             workflow.step_statuses[task_id] = STATUS_FAILED
                             failed_tasks.add(task_id)
                             workflow.updates.append(f"Failed task (timeout): {tasks_map[task_id].title} (ID: {task_id})")
                             on_update(f"Failed task '{tasks_map[task_id].title}' (timeout)", workflow.dict(include={'session_id', 'status', 'step_statuses'}))
                             async_task_pending.cancel() # Attempt to cancel

        # --- Final Workflow Result Handling --- 
        final_status = STATUS_FAILED if failed_tasks else STATUS_COMPLETED
        workflow.status = final_status
        
        # Retrieve final result (likely from the synthesis task)
        # Assuming 'synthesize_final_report' is the standard ID
        final_report_id = "synthesize_final_report"
        if final_status == STATUS_COMPLETED and final_report_id in workflow.steps_results:
            final_output_data = workflow.steps_results[final_report_id]
            # Extract text content if the synthesizer saved a file and returned the artifact dict
            if isinstance(final_output_data, dict) and final_output_data.get('type') == 'file_artifact':
                final_filename = final_output_data.get('filename')
                if final_filename:
                    try:
                        final_artifact_path = os.path.abspath(os.path.join(INSTANCE_FOLDER, final_filename))
                        logger.info(f"Attempting to read final result from artifact file: {final_artifact_path}")
                        # Simplified check: Assume decorator enforced location, just check existence
                        if os.path.exists(final_artifact_path):
                             with open(final_artifact_path, 'r', encoding='utf-8') as f:
                                 workflow.final_result = f.read()
                             logger.info(f"Successfully read final result from artifact file '{final_filename}'.")
                             
                             # Also emit the final result as a file artifact to ensure it's displayed in the UI
                             try:
                                 logger.info(f"Emitting file_artifact_update for final result file {final_filename}")
                                 socketio.emit('file_artifact_update', {
                                     'session_id': session_id,
                                     'filename': final_filename,
                                     'file_content': workflow.final_result
                                 }, room=session_id)
                                 socketio.sleep(0) # Allow event to be sent
                                 
                                 # Send a follow-up dummy event to ensure UI refresh
                                 socketio.emit('artifact_post_update', {
                                     'session_id': session_id,
                                     'message': 'Artifacts updated'
                                 }, room=session_id)
                                 socketio.sleep(0)
                             except Exception as emit_err:
                                 logger.error(f"Error emitting final artifact {final_filename}: {emit_err}", exc_info=True)
                        else:
                             workflow.final_result = f"[Final report file '{final_filename}' not found at expected location: {final_artifact_path}]"
                             logger.warning(f"Final report file '{final_filename}' not found at {final_artifact_path}.")
                    except Exception as final_read_err:
                        workflow.final_result = f"[Error reading final report file '{final_filename}': {final_read_err}]"
                        logger.error(f"Error reading final report file {final_filename}: {final_read_err}", exc_info=True)
                else:
                    workflow.final_result = "[Synthesizer indicated a file artifact but filename was missing.]"
                    logger.warning("Synthesizer returned file artifact dictionary without a filename.")
            elif isinstance(final_output_data, str):
                 workflow.final_result = final_output_data # Standard case: result is text
            else:
                 workflow.final_result = str(final_output_data) # Fallback conversion
            final_msg = f"Workflow {session_id} completed successfully."
        elif final_status == STATUS_COMPLETED:
            logger.warning(f"Synthesis task '{final_report_id}' result not found or failed processing artifact. Generating basic summary.")
            workflow.final_result = self._generate_final_report(list(tasks_map.values()), workflow.steps_results, workflow.step_statuses)
            final_msg = f"Workflow {session_id} completed, but final synthesis might be missing. Generated basic summary."
        else:
             workflow.final_result = f"Workflow failed. See logs for details. Failed tasks: {', '.join(failed_tasks)}"
             final_msg = f"Workflow {session_id} failed."

        workflow.updates.append(final_msg)
        logger.info(final_msg)
        # Save final state
        save_workflow_state(workflow)
        on_update(final_msg, workflow.dict(include={'session_id', 'status', 'final_result', 'step_statuses'}))

        # FINAL FIX: Scan the instance folder for all potential artifact files and emit them
        try:
            logger.info("Scanning instance folder for artifacts to ensure they're emitted")
            for step_id, result in workflow.steps_results.items():
                if isinstance(result, dict) and result.get('type') == 'file_artifact' and result.get('filename'):
                    filename = result.get('filename')
                    artifact_path = os.path.abspath(os.path.join(INSTANCE_FOLDER, filename))
                    if os.path.exists(artifact_path):
                        logger.info(f"Found artifact file: {filename}, re-emitting")
                        try:
                            with open(artifact_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                                socketio.emit('file_artifact_update', {
                                    'session_id': session_id,
                                    'filename': filename,
                                    'file_content': file_content
                                }, room=session_id)
                                socketio.sleep(0)
                        except Exception as e:
                            logger.error(f"Error re-emitting artifact file {filename}: {e}")
            
            # Force a final UI refresh
            socketio.emit('artifact_post_update', {
                'session_id': session_id,
                'message': 'Final artifacts update'
            }, room=session_id)
            socketio.sleep(0)
        except Exception as e:
            logger.error(f"Error during final artifact scan: {e}")

        return workflow.final_result

    async def _execute_single_step(self, step: Task, all_results: Dict[str, Any], user_query: Optional[str]) -> RunResult:
        """Executes a single task/step using the appropriate agent.

        Args:
            step: The Task object to execute.
            all_results: Dictionary of results from completed dependency tasks.
            user_query: The original user query for context.

        Returns:
            The RunResult object from the agent execution.
        """
        logger.info(f"Executing task {step.id}: {step.title} (Role: {step.agent_role})")
        
        agent = get_agent(step.agent_role)
        if not agent:
            logger.error(f"No agent found for role: {step.agent_role} for task {step.id}")
            raise ValueError(f"Agent role '{step.agent_role}' not found.")

        # Prepare input for the agent, including the original user query
        input_prompt = f"--- Original User Query ---\n{user_query or '[Original query not available]'}\n\n"
        input_prompt += f"--- Current Task ---\nTitle: {step.title}\nDescription: {step.description}\n\n"
        
        if step.dependencies:
            input_prompt += "--- Relevant Information from Previous Tasks ---\n"
            input_prompt += "(Note: Results might be text summaries or filenames for content saved by previous steps)\n"
            for dep_id in step.dependencies:
                if dep_id in all_results:
                    # Display potentially long results concisely in log
                    result_preview = str(all_results[dep_id])
                    if len(result_preview) > 100:
                        result_preview = result_preview[:100] + "..."
                    input_prompt += f"Result from task '{dep_id}':\n{all_results[dep_id]}\n---\n"
                else:
                    logger.warning(f"Dependency result for '{dep_id}' not found for task '{step.id}'. It might have failed or been skipped.")
                    input_prompt += f"Result from task '{dep_id}': [Not Available (likely failed or skipped)]\n---\n"
            input_prompt += "\nExecute your assigned task based on its description, the original user query, and the provided context from previous tasks.\n"
        else:
            input_prompt += "This task has no dependencies. Execute your assigned task based on its description and the original user query.\n"

        logger.debug(f"Input prompt for agent {agent.name} (Task {step.id}):\n{input_prompt[:500]}...")
        
        try:
            result = await Runner.run(agent, input_prompt)
            logger.info(f"Agent {agent.name} finished task {step.id} successfully.")
            return result
        except Exception as e:
            logger.error(f"Agent {agent.name} failed during execution of task {step.id}: {e}", exc_info=True)
            raise

    def _generate_final_report(self, tasks: List[Task], results: Dict[str, Any], statuses: Dict[str, str]) -> str:
        """Generates a basic final report if the synthesis step fails or is missing.
        
        Args:
            tasks: List of all Task objects in the plan.
            results: Dictionary of results for completed tasks.
            statuses: Dictionary of statuses for all tasks.
            
        Returns:
            A string containing the basic report.
        """
        report = "Workflow Execution Summary:\n\n"
        report += "Task Statuses:\n"
        for task in tasks:
            status = statuses.get(task.id, "Unknown")
            report += f"- {task.title} (ID: {task.id}): {status}\n"
            
        report += "\nCompleted Task Results:\n"
        has_results = False
        for task_id, result in results.items():
             # Find task title
            task_title = next((t.title for t in tasks if t.id == task_id), task_id) 
            report += f"--- Result for '{task_title}' (ID: {task_id}) ---\n"
            report += f"{result}\n\n"
            has_results = True
            
        if not has_results:
             report += "No task results were successfully recorded.\n"

        return report

# --- Utility Functions --- (If needed, e.g., for session management)
async def run_workflow(session_id: str, user_input: str, on_update: Callable[[str, Optional[Dict]], None]):
    """High-level function to run the entire workflow for a given input."""
    workflow_manager = EnhancedWorkflow()
    
    try:
        # Check if a plan already exists and is accepted
        state = get_workflow_state(session_id)
        if state and state.accepted_plan:
            logger.info(f"Resuming execution for accepted plan in session {session_id}")
            on_update(f"Resuming execution for accepted plan...", state.dict(include={'session_id', 'status', 'step_statuses'}))
        else:
            logger.info(f"Creating a new plan for session {session_id}")
            plan = await workflow_manager.create_plan(user_input)
            workflow_state = WorkflowState(session_id=session_id, plan=plan, status="plan_created")
            save_workflow_state(workflow_state)
            on_update("Plan created, awaiting acceptance.", workflow_state.dict(exclude={'steps_results'}))
            # Need to wait for acceptance via another mechanism (e.g., accept_plan call)
            return # Stop here, execution will be triggered after acceptance

        # Execute the accepted plan
        final_result = await workflow_manager.execute_plan(session_id, on_update)
        logger.info(f"Workflow {session_id} finished with result: {final_result[:100]}...")
        
    except Exception as e:
        logger.error(f"Workflow execution failed for session {session_id}: {e}", exc_info=True)
        on_update(f"Workflow error: {e}", {"session_id": session_id, "status": "error"})
