from flask import request, current_app
from flask_socketio import emit, join_room, SocketIO
import asyncio
import logging
import time
from typing import Optional, Dict
import os
import re

# Import necessary components from the app
# Remove direct import of enhanced_workflow module itself
# import app.enhanced_workflow as enhanced_workflow
from app.enhanced_workflow import EnhancedWorkflow
# Import models needed for type hinting
from app.models import TasksOutput # Updated import
# Import repository functions directly
from app.workflow_repository import create_workflow_session, get_workflow_state, load_workflow_state, save_workflow_state, accept_plan

logger = logging.getLogger(__name__)

# Define background tasks first as they are referenced by handlers
# These need access to app.app_context() and socketio instance

def generate_plan_task(app, socketio, session_id, user_input):
    with app.app_context():
        try:
            workflow_manager = EnhancedWorkflow()
            # The create_plan method now returns TasksOutput
            plan: TasksOutput = asyncio.run(workflow_manager.create_plan(user_input))
            logger.info(f"Plan created for session {session_id}. Loading state from DB.")
            # Use repository function
            workflow = load_workflow_state(session_id)

            if not workflow:
                logger.error(f"CRITICAL: Session {session_id} not found in DB *after* plan creation.")
                socketio.emit('error', {'message': 'Critical Error: Session state lost unexpectedly. Please try again.'}, room=session_id)
                return

            logger.info(f"Successfully loaded session state for {session_id} from DB.")
            workflow.plan = plan # Assign the TasksOutput object
            workflow.user_query = user_input # Store the user query
            # Use repository function
            if save_workflow_state(workflow):
                logger.info(f"Successfully persisted plan and user query for session {session_id} to DB.")
                socketio.emit('plan_created', {
                    'session_id': session_id,
                    'plan': plan.dict() # Serialize the TasksOutput
                }, room=session_id)
            else:
                logger.error(f"Failed to persist updated plan for session {session_id} to DB")
                socketio.emit('error', {'message': 'Failed to save plan update. Please try again.'}, room=session_id)

        except Exception as e:
            logger.error(f"Error in generate_plan_task: {e}", exc_info=True)
            socketio.emit('error', {'message': f'Error creating plan: {str(e)}'}, room=session_id)

def refine_plan_task(app, socketio, session_id, plan: TasksOutput, feedback: str):
    with app.app_context():
        try:
            workflow_manager = EnhancedWorkflow()
            # refine_plan now expects and returns TasksOutput
            refined_plan: TasksOutput = asyncio.run(
                workflow_manager.refine_plan(plan, feedback)
            )
            # Use repository function
            workflow = load_workflow_state(session_id)
            if workflow:
                workflow.plan = refined_plan # Assign the TasksOutput object
                # Use repository function
                if save_workflow_state(workflow):
                    socketio.emit('plan_created', {
                        'session_id': session_id,
                        'plan': refined_plan.dict() # Serialize the TasksOutput
                    }, room=session_id)
                else:
                    socketio.emit('error', {'message': 'Failed to save refined plan.'}, room=session_id)
            else:
                socketio.emit('error', {'message': 'Session expired before refined plan could be saved.'}, room=session_id)

        except Exception as e:
            logger.error(f"Error in refine_plan_task: {e}", exc_info=True)
            socketio.emit('error', {'message': f'Error refining plan: {str(e)}'}, room=session_id)

def execute_plan_task(app, socketio, session_id):
    with app.app_context():
        def send_update(message: str, state: Optional[Dict] = None):
            update_data = {
                'session_id': session_id,
                'message': message
            }
            if state:
                update_data['state'] = {
                    'status': state.get('status'),
                    'step_statuses': state.get('step_statuses')
                }
                if 'final_result' in state:
                    update_data['state']['final_result'] = state.get('final_result')
            logger.info(f"--- Emitting 'workflow_update' to room: {session_id} - Msg: {message[:50]}... State: {bool(state)}")
            socketio.emit('workflow_update', update_data, room=session_id)
            socketio.sleep(0)

        try:
            workflow_manager = EnhancedWorkflow()
            # Pass socketio instance to execute_plan
            result = asyncio.run(
                workflow_manager.execute_plan(session_id, socketio, send_update)
            )
        except Exception as e:
            logger.error(f"Error in execute_plan_task: {e}", exc_info=True)
            logger.info(f"--- Emitting 'error' due to exception to room: {session_id}")
            error_state = {'status': 'failed', 'step_statuses': {}}
            send_update(f'Error executing plan: {str(e)}', error_state)

def analyze_plan_task(app, socketio, session_id, plan: TasksOutput):
    with app.app_context():
        try:
            workflow_manager = EnhancedWorkflow()
            # analyze_plan now expects TasksOutput
            analysis = asyncio.run(
                workflow_manager.analyze_plan(plan)
            )
            socketio.emit('plan_analysis', {
                'session_id': session_id,
                # Assuming analysis structure remains similar, adjust if needed
                'analysis': analysis # Send the whole analysis dict
            }, room=session_id)
        except Exception as e:
            logger.error(f"Error in analyze_plan_task: {e}", exc_info=True)
            socketio.emit('error', {'message': f'Error analyzing plan: {str(e)}'}, room=session_id)


def register_socketio_events(socketio: SocketIO):
    """Registers Socket.IO event handlers."""

    # Need access to the app instance for background tasks and logging
    app = current_app._get_current_object()

    @socketio.on('connect')
    def handle_connect():
        emit('status', {'message': f'Connected to server with sid: {request.sid}'})
        
        # Debug function to scan for text files in instance folder
        try:
            WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            INSTANCE_FOLDER = os.path.join(WORKSPACE_ROOT, 'instance')
            debug_files = []
            
            if os.path.exists(INSTANCE_FOLDER):
                logger.info("DEBUGGING: Scanning instance folder for text files on connect")
                for file in os.listdir(INSTANCE_FOLDER):
                    if file.endswith('.txt'):
                        file_path = os.path.join(INSTANCE_FOLDER, file)
                        if os.path.isfile(file_path):
                            try:
                                file_size = os.path.getsize(file_path)
                                debug_files.append(f"{file} ({file_size} bytes)")
                            except:
                                debug_files.append(f"{file} (size unknown)")
                
                if debug_files:
                    logger.info(f"DEBUGGING: Found text files in instance folder: {', '.join(debug_files)}")
                else:
                    logger.info("DEBUGGING: No text files found in instance folder")
            else:
                logger.info(f"DEBUGGING: Instance folder does not exist: {INSTANCE_FOLDER}")
        except Exception as e:
            logger.error(f"DEBUGGING: Error scanning instance folder: {e}")

    @socketio.on('create_plan')
    def handle_create_plan(data):
        user_input = data.get('message', '')
        session_id = data.get('session_id', '')
        client_sid = request.sid
        new_session_created = False # Keep track if we created one

        if not session_id:
            try:
                # Use repository function
                session_id = create_workflow_session()
                logger.info(f"Created new session via DB: {session_id}")
                new_session_created = True
            except Exception as e:
                 logger.error(f"Failed to create initial workflow session: {e}", exc_info=True)
                 emit('error', {'message': 'Failed to initialize session. Please try again.'}, to=client_sid)
                 return
        else:
            # Use repository function
            existing_state = get_workflow_state(session_id)
            if not existing_state:
                logger.warning(f"Provided session_id {session_id} not found in DB. Creating a new one.")
                try:
                    # Use repository function
                    session_id = create_workflow_session()
                    logger.info(f"Created new session via DB: {session_id}")
                    new_session_created = True
                except Exception as e:
                    logger.error(f"Failed to create fallback workflow session for missing ID {session_id}: {e}", exc_info=True)
                    emit('error', {'message': 'Failed to re-initialize session. Please try again.'}, to=client_sid)
                    return
            else:
                 logger.info(f"Using existing session_id from DB: {session_id}")

        if not session_id: # Should not happen if exceptions were caught
             logger.error("Failed to obtain a valid session ID.")
             emit('error', {'message': 'Failed to initialize session. Please try again.'}, to=client_sid)
             return

        logger.info(f"Client {client_sid} joining room {session_id}")
        join_room(session_id)

        # Emit session ID back if it was newly created
        if new_session_created:
            emit('session_created', {'session_id': session_id}, to=client_sid)

        # Pass app and socketio to background task
        socketio.start_background_task(generate_plan_task, app, socketio, session_id, user_input)

    @socketio.on('refine_plan')
    def handle_refine_plan(data):
        session_id = data.get('session_id', '')
        feedback = data.get('feedback', '')
        client_sid = request.sid

        # Use repository function
        workflow = load_workflow_state(session_id)
        if not workflow:
            emit('error', {'message': 'Invalid or expired session ID'}, to=client_sid)
            return
        if not workflow.plan:
            emit('error', {'message': 'No plan exists to refine'}, to=client_sid)
            return

        logger.info(f"Client {client_sid} joining room {session_id} for refinement")
        join_room(session_id)
        # Pass app and socketio to background task
        socketio.start_background_task(refine_plan_task, app, socketio, session_id, workflow.plan, feedback)

    @socketio.on('accept_plan')
    def handle_accept_plan(data):
        session_id = data.get('session_id', '')
        client_sid = request.sid

        logger.info(f"Received accept_plan for session_id: {session_id} from sid: {client_sid}")
        logger.info(f"Client {client_sid} joining room {session_id} for acceptance")
        join_room(session_id)

        # Use repository function
        if accept_plan(session_id):
            logger.info(f"Plan accepted state saved for session: {session_id}. Emitting 'plan_accepted'.")
            emit('plan_accepted', {'session_id': session_id}, room=session_id)
            time.sleep(0.1)
            logger.info(f"Starting execution task for session: {session_id}.")
            # Pass app and socketio to background task
            socketio.start_background_task(execute_plan_task, app, socketio, session_id)
        else:
            emit('error', {'message': 'Failed to accept plan state. Please check logs or try again.'}, to=client_sid)

    @socketio.on('analyze_plan')
    def handle_analyze_plan(data):
        session_id = data.get('session_id', '')
        client_sid = request.sid

        # Use repository function
        workflow = load_workflow_state(session_id)
        if not workflow:
            emit('error', {'message': 'Invalid or expired session ID'}, to=client_sid)
            return
        if not workflow.plan:
            emit('error', {'message': 'No plan exists to analyze'}, to=client_sid)
            return

        logger.info(f"Client {client_sid} joining room {session_id} for analysis")
        join_room(session_id)
        # Pass app and socketio to background task
        socketio.start_background_task(analyze_plan_task, app, socketio, session_id, workflow.plan)

    @socketio.on('check_artifacts')
    def handle_check_artifacts(data):
        session_id = data.get('session_id', '')
        client_sid = request.sid
        current_session_only = data.get('current_session_only', False)
        
        if not session_id:
            emit('error', {'message': 'No session ID provided'}, to=client_sid)
            return
        
        logger.info(f"Received check_artifacts request for session {session_id} (current_session_only: {current_session_only})")
        join_room(session_id)
        
        # Load workflow state
        workflow = load_workflow_state(session_id)
        if not workflow:
            emit('error', {'message': 'Invalid or expired session ID'}, to=client_sid)
            return
        
        # Get instance folder path
        try:
            WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            INSTANCE_FOLDER = os.path.join(WORKSPACE_ROOT, 'instance')
            
            # Scan for artifacts in workflow results
            artifact_count = 0
            logger.info(f"Scanning step results for artifacts in session {session_id}")
            
            # Extract any file artifacts explicitly recorded in workflow results
            for step_id, result in workflow.steps_results.items():
                if isinstance(result, dict) and result.get('type') == 'file_artifact' and result.get('filename'):
                    filename = result.get('filename')
                    artifact_path = os.path.abspath(os.path.join(INSTANCE_FOLDER, filename))
                    
                    if os.path.exists(artifact_path):
                        logger.info(f"Found artifact file in workflow steps: {filename}")
                        try:
                            with open(artifact_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                                emit('file_artifact_update', {
                                    'session_id': session_id,
                                    'filename': filename,
                                    'file_content': file_content
                                }, room=session_id)
                                artifact_count += 1
                        except Exception as e:
                            logger.error(f"Error reading artifact file {filename}: {e}")
            
            # If no artifacts found in step results and we have a final result, check it for mentions
            if artifact_count == 0 and workflow.final_result:
                logger.info(f"Checking final result for file mentions: {workflow.final_result[:100]}...")
                # Common patterns:
                file_patterns = [
                    r'file:?\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)',
                    r'in\s+the\s+file\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)',
                    r'find\s+it\s+in\s+the\s+file\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)',
                    r'access\s+it\s+in\s+the\s+file\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)',
                    r'titled\s+"([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)"',
                    r'file\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)',
                    r'\.txt[:\.]?\s*([a-zA-Z0-9_\-.]+\.txt)'
                ]
                
                # First, try to parse an exact filename from the result text
                for pattern in file_patterns:
                    matches = re.findall(pattern, workflow.final_result, re.IGNORECASE)
                    for filename in matches:
                        logger.info(f"Found potential file reference in final result: {filename}")
                        artifact_path = os.path.abspath(os.path.join(INSTANCE_FOLDER, filename))
                        if os.path.exists(artifact_path):
                            logger.info(f"File exists! Reading and sending: {filename}")
                            try:
                                with open(artifact_path, 'r', encoding='utf-8') as f:
                                    file_content = f.read()
                                    emit('file_artifact_update', {
                                        'session_id': session_id,
                                        'filename': filename,
                                        'file_content': file_content
                                    }, room=session_id)
                                    artifact_count += 1
                            except Exception as e:
                                logger.error(f"Error reading file mentioned in result {filename}: {e}")
                
                # If still no artifacts found, try to find files with keywords from the final result
                if artifact_count == 0 and not current_session_only:
                    try:
                        # Extract keywords from the final result text
                        words = re.findall(r'\b[a-zA-Z]{4,}\b', workflow.final_result.lower())
                        keywords = set([word for word in words if len(word) >= 4 and word not in 
                                      ['from', 'with', 'that', 'have', 'this', 'will', 'your', 'file', 'poem']])
                        
                        logger.info(f"Extracting keywords from result: {', '.join(keywords)}")
                        
                        # Look for files containing these keywords
                        for filename in os.listdir(INSTANCE_FOLDER):
                            if filename.endswith('.txt'):
                                file_lower = filename.lower()
                                if any(keyword in file_lower for keyword in keywords):
                                    logger.info(f"Found file matching keywords: {filename}")
                                    try:
                                        with open(os.path.join(INSTANCE_FOLDER, filename), 'r', encoding='utf-8') as f:
                                            file_content = f.read()
                                            emit('file_artifact_update', {
                                                'session_id': session_id,
                                                'filename': filename,
                                                'file_content': file_content
                                            }, room=session_id)
                                            artifact_count += 1
                                    except Exception as e:
                                        logger.error(f"Error reading keyword-matched file {filename}: {e}")
                    except Exception as e:
                        logger.error(f"Error in keyword extraction: {e}")
            
            # Send a confirmation message
            emit('artifacts_check_complete', {
                'session_id': session_id,
                'artifact_count': artifact_count,
                'message': f'Found and sent {artifact_count} artifacts from your workflow'
            }, room=session_id)
            
        except Exception as e:
            logger.error(f"Error during artifact check: {e}")
            emit('error', {'message': f'Error checking for artifacts: {str(e)}'}, to=client_sid)

    @socketio.on('request_specific_file')
    def handle_request_specific_file(data):
        session_id = data.get('session_id', '')
        filename = data.get('filename', '')
        client_sid = request.sid
        current_session_only = data.get('current_session_only', False)
        
        if not session_id or not filename:
            emit('error', {'message': 'Missing session_id or filename'}, to=client_sid)
            return
        
        logger.info(f"Received request for specific file: {filename} for session {session_id} (current_session_only: {current_session_only})")
        join_room(session_id)
        
        try:
            WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            INSTANCE_FOLDER = os.path.join(WORKSPACE_ROOT, 'instance')
            
            # First check if the exact filename exists
            artifact_path = os.path.abspath(os.path.join(INSTANCE_FOLDER, filename))
            if os.path.exists(artifact_path) and os.path.isfile(artifact_path):
                logger.info(f"Found requested file: {filename}")
                try:
                    with open(artifact_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        emit('file_artifact_update', {
                            'session_id': session_id,
                            'filename': filename,
                            'file_content': file_content
                        }, room=session_id)
                        emit('artifacts_check_complete', {
                            'session_id': session_id,
                            'artifact_count': 1,
                            'message': f'Found and sent requested file: {filename}'
                        }, room=session_id)
                        return
                except Exception as e:
                    logger.error(f"Error reading requested file {filename}: {e}")
                    emit('error', {'message': f'Error reading file: {str(e)}'}, to=client_sid)
            
            # If exact file not found, try to locate the most suitable match
            logger.warning(f"Requested file not found: {filename}")
            
            # Get workflow data to help with matching
            workflow = load_workflow_state(session_id)
            if not workflow:
                emit('error', {'message': 'Invalid session ID'}, to=client_sid)
                return
            
            # Extract keywords from the requested filename and workflow final result
            filename_parts = re.findall(r'[a-zA-Z]{3,}', filename.lower())
            
            # If we have a final result, extract keywords from it too
            result_keywords = set()
            if workflow.final_result:
                result_words = re.findall(r'\b[a-zA-Z]{4,}\b', workflow.final_result.lower())
                result_keywords = set([word for word in result_words if len(word) >= 4 and word not in 
                                     ['from', 'with', 'that', 'have', 'this', 'will', 'your', 'file', 'poem']])
            
            # The combined keywords to search for
            all_keywords = set(filename_parts) | result_keywords
            logger.info(f"Searching for files matching keywords: {', '.join(all_keywords)}")
            
            # Scan directory for matching files, looking for the best match
            found = False
            try:
                # First pass - exact matches
                for file in os.listdir(INSTANCE_FOLDER):
                    if os.path.isfile(os.path.join(INSTANCE_FOLDER, file)) and file.lower().endswith('.txt'):
                        if file.lower() == filename.lower():
                            logger.info(f"Found exact match (case-insensitive): {file}")
                            try:
                                with open(os.path.join(INSTANCE_FOLDER, file), 'r', encoding='utf-8') as f:
                                    file_content = f.read()
                                    emit('file_artifact_update', {
                                        'session_id': session_id,
                                        'filename': file,
                                        'file_content': file_content
                                    }, room=session_id)
                                    found = True
                                    emit('artifacts_check_complete', {
                                        'session_id': session_id,
                                        'artifact_count': 1,
                                        'message': f'Found and sent matching file: {file}'
                                    }, room=session_id)
                                    return
                            except Exception as e:
                                logger.error(f"Error reading matching file {file}: {e}")
                
                # Second pass - keyword-based matches
                best_file = None
                best_match_score = 0
                
                for file in os.listdir(INSTANCE_FOLDER):
                    if os.path.isfile(os.path.join(INSTANCE_FOLDER, file)) and file.lower().endswith('.txt'):
                        file_lower = file.lower()
                        
                        # Count how many keywords match
                        match_score = sum(1 for keyword in all_keywords if keyword in file_lower)
                        
                        # Boost score for files that likely match the session's task
                        if match_score > 0 and match_score >= best_match_score:
                            best_match_score = match_score
                            best_file = file
                
                # Use the best matching file
                if best_file:
                    logger.info(f"Found best matching file: {best_file} (score: {best_match_score})")
                    try:
                        with open(os.path.join(INSTANCE_FOLDER, best_file), 'r', encoding='utf-8') as f:
                            file_content = f.read()
                            emit('file_artifact_update', {
                                'session_id': session_id,
                                'filename': best_file,
                                'file_content': file_content
                            }, room=session_id)
                            found = True
                            emit('artifacts_check_complete', {
                                'session_id': session_id,
                                'artifact_count': 1,
                                'message': f'Found and sent best matching file: {best_file}'
                            }, room=session_id)
                            return
                    except Exception as e:
                        logger.error(f"Error reading best matching file {best_file}: {e}")
            except Exception as e:
                logger.error(f"Error searching for similar files: {e}")
            
            # If no similar file found, send a no-file message
            if not found:
                emit('artifacts_check_complete', {
                    'session_id': session_id,
                    'artifact_count': 0,
                    'message': f'Could not find the artifact mentioned in your results'
                }, room=session_id)
                
        except Exception as e:
            logger.error(f"Error processing specific file request: {e}")
            emit('error', {'message': f'Error processing file request: {str(e)}'}, to=client_sid)

    @socketio.on('get_workflow_status')
    def handle_get_workflow_status(data):
        session_id = data.get('session_id', '')
        client_sid = request.sid

        # Use repository function
        workflow = get_workflow_state(session_id)

        if workflow:
            logger.info(f"Client {client_sid} joining room {session_id} for status check")
            join_room(session_id) # Join only if workflow exists

        if not workflow:
            emit('workflow_status', {
                'session_id': session_id,
                'error': 'Workflow not found'
            }, to=client_sid)
            return

        # workflow.plan will be TasksOutput, but we only serialize specific fields
        state_to_send = {
            'session_id': workflow.session_id,
            'status': workflow.status,
            'accepted_plan': workflow.accepted_plan,
            'step_statuses': workflow.step_statuses,
            'final_result': workflow.final_result,
            'updates': workflow.updates[-10:] # Send recent updates
        }
        # Send plan summary and task titles/ids/status, not full plan details
        if workflow.plan:
            state_to_send['plan_summary'] = workflow.plan.summary
            state_to_send['plan_tasks_overview'] = [
                {
                    'id': task.id,
                    'title': task.title,
                    'status': workflow.step_statuses.get(task.id, 'pending')
                }
                for task in workflow.plan.tasks
            ]
        emit('workflow_status', state_to_send, to=client_sid)

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f'Client disconnected: {request.sid}') 