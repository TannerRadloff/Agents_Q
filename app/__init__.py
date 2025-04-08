from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import asyncio
import os
import uuid
import logging
import time
from app.config import Config
from .extensions import db
import app.enhanced_workflow as enhanced_workflow
from app.enhanced_workflow import EnhancedWorkflow # Import the class

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # Already exists

    # Initialize extensions
    db.init_app(app)

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    # Use Flask's built-in logger
    if not app.debug:
        # Configure logging only if not in debug mode (Werkzeug might handle it)
        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.INFO)
        log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_handler.setFormatter(log_formatter)
        app.logger.addHandler(log_handler)
        app.logger.setLevel(logging.INFO)
    else:
        # In debug mode, ensure logger level is appropriate if needed
        app.logger.setLevel(logging.INFO) 
    
    # Initialize SocketIO with increased timeouts
    socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=300, ping_interval=60)
    app.socketio = socketio
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.agent import agent_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(agent_bp, url_prefix='/api')
    
    # Socket.IO event handlers
    @socketio.on('connect')
    def handle_connect():
        emit('status', {'message': f'Connected to server with sid: {request.sid}'})
    
    @socketio.on('create_plan')
    def handle_create_plan(data):
        user_input = data.get('message', '')
        session_id = data.get('session_id', '')
        client_sid = request.sid
        new_session_created = False

        # Use DB-aware functions
        if not session_id:
            session_id = enhanced_workflow.create_workflow_session() # Creates and saves initial state to DB
            app.logger.info(f"Created new session via DB: {session_id}")
            new_session_created = True
        else:
            # Verify session exists in DB
            existing_state = enhanced_workflow.get_workflow_state(session_id) # Loads from DB
            if not existing_state:
                app.logger.warning(f"Provided session_id {session_id} not found in DB. Creating a new one.")
                session_id = enhanced_workflow.create_workflow_session()
                app.logger.info(f"Created new session via DB: {session_id}")
                new_session_created = True
            else:
                 app.logger.info(f"Using existing session_id from DB: {session_id}")

        # Ensure we have a valid session ID before starting the task
        if not session_id:
             app.logger.error("Failed to obtain a valid session ID (DB interaction failed?).")
             emit('error', {'message': 'Failed to initialize session. Please try again.'}, to=client_sid)
             return
        
        # Join the room associated with the session ID
        app.logger.info(f"Client {client_sid} joining room {session_id}")
        join_room(session_id)

        # Pass only necessary data to background task
        socketio.start_background_task(generate_plan_task, session_id, user_input)

    def generate_plan_task(session_id, user_input):
        # Ensure background task runs within application context for DB access
        with app.app_context():
            try:
                # Instantiate the workflow manager
                workflow_manager = EnhancedWorkflow()

                # create_plan is now called on the instance using asyncio.run
                plan = asyncio.run(workflow_manager.create_plan(user_input))
                app.logger.info(f"Plan created for session {session_id}. Loading state from DB.")

                # Load state reliably from DB
                workflow = enhanced_workflow.load_workflow_state(session_id) # Use DB load

                if not workflow:
                    app.logger.error(f"CRITICAL: Session {session_id} not found in DB *after* plan creation.")
                    socketio.emit('error', {'message': 'Critical Error: Session state lost unexpectedly. Please try again.'}, room=session_id)
                    return

                app.logger.info(f"Successfully loaded session state for {session_id} from DB.")

                # Update workflow object (Pydantic model) and save back to DB
                workflow.plan = plan
                if enhanced_workflow.save_workflow_state(workflow): # Use DB save
                    app.logger.info(f"Successfully persisted plan for session {session_id} to DB.")
                    socketio.emit('plan_created', {
                        'session_id': session_id,
                        'plan': plan.dict() # Send the plan data
                    }, room=session_id)
                else:
                    app.logger.error(f"Failed to persist updated plan for session {session_id} to DB")
                    socketio.emit('error', {'message': 'Failed to save plan update. Please try again.'}, room=session_id)

            except Exception as e:
                app.logger.error(f"Error in generate_plan_task: {e}", exc_info=True)
                socketio.emit('error', {'message': f'Error creating plan: {str(e)}'}, room=session_id)
    
    @socketio.on('refine_plan')
    def handle_refine_plan(data):
        session_id = data.get('session_id', '')
        feedback = data.get('feedback', '')
        client_sid = request.sid

        # Load state from DB
        workflow = enhanced_workflow.load_workflow_state(session_id)
        if not workflow:
            socketio.emit('error', {'message': 'Invalid or expired session ID'}, to=client_sid)
            return

        if not workflow.plan:
            socketio.emit('error', {'message': 'No plan exists to refine'}, to=client_sid)
            return
        
        # Ensure client is in the room (might have reconnected)
        app.logger.info(f"Client {client_sid} joining room {session_id} for refinement")
        join_room(session_id)

        # Pass necessary data to background task
        socketio.start_background_task(refine_plan_task, session_id, workflow.plan, feedback)

    def refine_plan_task(session_id, plan, feedback):
        # Ensure background task runs within application context for DB access
        with app.app_context():
            try:
                # Instantiate the workflow manager
                workflow_manager = EnhancedWorkflow()

                # refine_plan is agent interaction - called on instance using asyncio.run
                refined_plan = asyncio.run(
                    workflow_manager.refine_plan(plan, feedback)
                )
                # Load the state again to update it
                workflow = enhanced_workflow.load_workflow_state(session_id)
                if workflow:
                    workflow.plan = refined_plan
                    if enhanced_workflow.save_workflow_state(workflow):
                        socketio.emit('plan_created', {
                            'session_id': session_id,
                            'plan': refined_plan.dict()
                        }, room=session_id)
                    else:
                         socketio.emit('error', {'message': 'Failed to save refined plan.'}, room=session_id)
                else:
                     socketio.emit('error', {'message': 'Session expired before refined plan could be saved.'}, room=session_id)

            except Exception as e:
                socketio.emit('error', {'message': f'Error refining plan: {str(e)}'}, room=session_id)
    
    @socketio.on('accept_plan')
    def handle_accept_plan(data):
        session_id = data.get('session_id', '')
        client_sid = request.sid

        app.logger.info(f"Received accept_plan for session_id: {session_id} from sid: {client_sid}")
        
        # Ensure client is in the room (important before starting task)
        app.logger.info(f"Client {client_sid} joining room {session_id} for acceptance")
        join_room(session_id)

        # Use the DB-aware accept_plan function which handles loading and saving
        if enhanced_workflow.accept_plan(session_id):
            app.logger.info(f"Plan accepted state saved for session: {session_id}. Emitting 'plan_accepted'.")
            # --- Emit immediately after successful DB update --- 
            socketio.emit('plan_accepted', {'session_id': session_id}, room=session_id)
            
            # --- Add small delay for SQLite timing diagnosis --- 
            time.sleep(0.1) 

            # Now, proceed with reloading state and starting the task
            workflow = enhanced_workflow.load_workflow_state(session_id)
            if workflow and workflow.plan:
                app.logger.info(f"Starting execution task for session: {session_id}.")
                socketio.start_background_task(execute_plan_task, session_id, workflow.plan.steps)
                # The emit was moved up
            else:
                 # Should ideally not happen if accept_plan succeeded, but handle defensively
                 app.logger.error(f"Accept plan anomaly: Emitted 'plan_accepted' but couldn't reload plan for execution session {session_id}")
                 # Optionally emit a specific error here, though the UI might already be in 'Executing' state
                 # socketio.emit('error', {'message': f'Internal error starting plan execution after acceptance for session {session_id}.'}, room=session_id) # Sending to room
        else:
            # accept_plan function already logged the specific error
            socketio.emit('error', {'message': 'Failed to accept plan state. Please check logs or try again.'}, to=client_sid)

    def execute_plan_task(session_id, steps):
         # Ensure background task runs within application context for DB access
        with app.app_context():
            def send_update(message):
                # Emit updates to the room
                app.logger.info(f"--- Emitting 'workflow_update' to room: {session_id} - Msg: {message[:50]}...")
                socketio.emit('workflow_update', {
                    'session_id': session_id,
                    'message': message
                }, room=session_id)
                # --- Yield control to allow message dispatch --- 
                socketio.sleep(0)

            try:
                # Instantiate the workflow manager
                workflow_manager = EnhancedWorkflow()

                # Call the execute_plan method on the instance using asyncio.run
                result = asyncio.run(
                    workflow_manager.execute_plan(session_id, steps, send_update)
                )
                app.logger.info(f"--- Emitting 'workflow_completed' to room: {session_id}")
                socketio.emit('workflow_completed', {
                    'session_id': session_id,
                    'result': result
                }, room=session_id)
            except Exception as e:
                app.logger.error(f"Error in execute_plan_task: {e}", exc_info=True)
                app.logger.info(f"--- Emitting 'error' due to exception to room: {session_id}")
                socketio.emit('error', {'message': f'Error executing plan: {str(e)}'}, room=session_id)
    
    @socketio.on('analyze_plan')
    def handle_analyze_plan(data):
        session_id = data.get('session_id', '')
        client_sid = request.sid

        # Load state from DB
        workflow = enhanced_workflow.load_workflow_state(session_id)
        if not workflow:
            socketio.emit('error', {'message': 'Invalid or expired session ID'}, to=client_sid)
            return

        if not workflow.plan:
            socketio.emit('error', {'message': 'No plan exists to analyze'}, to=client_sid)
            return
        
        # Ensure client is in the room
        app.logger.info(f"Client {client_sid} joining room {session_id} for analysis")
        join_room(session_id)

        socketio.start_background_task(analyze_plan_task, session_id, workflow.plan)

    def analyze_plan_task(session_id, plan):
         # Ensure background task runs within application context for DB access (though not strictly needed here)
        with app.app_context():
            try:
                # Instantiate the workflow manager
                workflow_manager = EnhancedWorkflow()

                # analyze_plan is agent interaction - called on instance using asyncio.run
                analysis = asyncio.run(
                    workflow_manager.analyze_plan(plan)
                )
                # Emit analysis to the room
                socketio.emit('plan_analysis', {
                    'session_id': session_id,
                    'analysis': analysis.get('analysis', 'Analysis data not found')
                }, room=session_id)
            except Exception as e:
                socketio.emit('error', {'message': f'Error analyzing plan: {str(e)}'}, room=session_id)
    
    @socketio.on('get_workflow_status')
    def handle_get_workflow_status(data):
        session_id = data.get('session_id', '')
        client_sid = request.sid

        # Use the DB-aware get_workflow_state
        workflow = enhanced_workflow.get_workflow_state(session_id)
        
        # Ensure client is in the room to receive status
        if workflow:
            app.logger.info(f"Client {client_sid} joining room {session_id} for status check")
            join_room(session_id)

        if not workflow:
            socketio.emit('workflow_status', {
                'session_id': session_id,
                'error': 'Workflow not found'
            }, to=client_sid)
            return

        socketio.emit('workflow_status', {
            'session_id': session_id,
            'status': workflow.status,
            'current_step': workflow.current_step_index,
            'total_steps': workflow.total_steps,
            'updates': workflow.updates,
            'final_result': workflow.final_result
            # Optionally add plan details if needed
            # 'plan': workflow.plan.dict() if workflow.plan else None
        }, room=session_id)
    
    return app
