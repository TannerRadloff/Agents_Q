import uuid
import logging
import json
from typing import Optional

from .extensions import db
from .database_models import WorkflowSessionDB
from .models import WorkflowState, TasksOutput, Task # Updated imports

logger = logging.getLogger(__name__)

# --- Constants for Statuses (needed for initialization) ---
STATUS_PENDING = "pending"


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
        # Assuming WorkflowSessionDB properties correctly handle JSON serialization/deserialization
        # of the renamed TasksOutput and Task types implicitly via getters/setters.
        state = WorkflowState(
            session_id=session_db.id,
            user_query=session_db.user_query, # Load user query
            plan=session_db.plan, # Should now return TasksOutput or None
            accepted_plan=session_db.accepted_plan,
            steps_results=session_db.steps_results, # Keeps name, DB stores results dict
            step_statuses=session_db.step_statuses, # Keeps name, DB stores status dict
            status=session_db.status,
            updates=session_db.updates, # Uses the @property getter
            final_result=session_db.final_result
        )
        
        # Initialize statuses if loading an accepted plan without statuses yet
        if state.plan and state.accepted_plan and not state.step_statuses:
             # Use state.plan.tasks (renamed from steps)
             state.step_statuses = {task.id: STATUS_PENDING for task in state.plan.tasks}
             logger.info(f"Initialized task statuses for accepted session {session_id} during load.")

        return state
    except Exception as e:
        logger.error(f"Error converting DB model to Pydantic for session {session_id}: {e}", exc_info=True)
        return None

def save_workflow_state(workflow: WorkflowState) -> bool:
    """Saves the Pydantic WorkflowState model to the database."""
    try:
        session_db = get_workflow_db(workflow.session_id)
        if not session_db:
            session_db = WorkflowSessionDB(id=workflow.session_id)
            db.session.add(session_db)
            logger.info(f"Creating new DB entry for session {workflow.session_id} during save.")

        # Update DB model fields from Pydantic model
        # Assuming setters handle serialization of TasksOutput correctly
        session_db.user_query = workflow.user_query # Save user query
        session_db.plan = workflow.plan # Setter receives TasksOutput
        session_db.accepted_plan = workflow.accepted_plan
        session_db.steps_results = workflow.steps_results # Setter receives results dict
        session_db.step_statuses = workflow.step_statuses # Setter receives status dict
        session_db.status = workflow.status
        session_db.updates = workflow.updates # Setter receives updates list
        session_db.final_result = workflow.final_result

        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to save session state {workflow.session_id} to DB: {e}", exc_info=True)
        db.session.rollback()
        return False

def create_workflow_session() -> str:
    """Creates a new workflow session entry in the database and returns the session ID."""
    session_id = uuid.uuid4().hex
    new_session = WorkflowSessionDB(id=session_id, status=STATUS_PENDING)
    db.session.add(new_session)
    try:
        db.session.commit()
        logger.info(f"Created new workflow session entry: {session_id}")
        return session_id
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create workflow session entry: {e}", exc_info=True)
        raise

def get_workflow_state(session_id: str) -> Optional[WorkflowState]:
    """Retrieves the current state of a workflow session from the database."""
    return load_workflow_state(session_id)

def accept_plan(session_id: str) -> bool:
    """Loads a workflow, marks its plan as accepted, initializes statuses, and saves back to DB."""
    workflow = load_workflow_state(session_id)
    if not workflow:
        logger.warning(f"Cannot accept plan for session {session_id}: Workflow state not found.")
        return False
    if not workflow.plan:
        logger.warning(f"Cannot accept plan for session {session_id}: No plan found in state.")
        return False

    workflow.accepted_plan = True
    workflow.status = "accepted"
    # Initialize task statuses upon acceptance, using plan.tasks
    workflow.step_statuses = {task.id: STATUS_PENDING for task in workflow.plan.tasks}
    workflow.steps_results = {} # Clear previous results
    workflow.updates.append("Plan accepted by user. Ready for execution.")

    logger.info(f"Marking plan accepted for session {session_id}. Initialized task statuses.")
    return save_workflow_state(workflow) 