from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import asyncio
import os
import uuid
from app.config import Config
from app.enhanced_workflow import enhanced_workflow, create_workflow_session, get_workflow_state, accept_plan, workflow_sessions

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.agent import agent_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(agent_bp, url_prefix='/api')
    
    # Socket.IO event handlers
    @socketio.on('connect')
    def handle_connect():
        emit('status', {'message': 'Connected to server'})
    
    @socketio.on('create_plan')
    def handle_create_plan(data):
        user_input = data.get('message', '')
        session_id = data.get('session_id', '')
        
        if not session_id:
            session_id = create_workflow_session()
        
        # Create a background task to generate the plan
        @socketio.start_background_task
        def generate_plan_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                plan = loop.run_until_complete(enhanced_workflow.create_plan(user_input))
                workflow_sessions[session_id].plan = plan
                emit('plan_created', {
                    'session_id': session_id,
                    'plan': plan.dict()
                })
            except Exception as e:
                emit('error', {
                    'message': f'Error creating plan: {str(e)}'
                })
            finally:
                loop.close()
    
    @socketio.on('refine_plan')
    def handle_refine_plan(data):
        session_id = data.get('session_id', '')
        feedback = data.get('feedback', '')
        
        if not session_id or session_id not in workflow_sessions:
            emit('error', {'message': 'Invalid session ID'})
            return
        
        workflow = workflow_sessions[session_id]
        if not hasattr(workflow, 'plan'):
            emit('error', {'message': 'No plan exists to refine'})
            return
        
        # Create a background task to refine the plan
        @socketio.start_background_task
        def refine_plan_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                refined_plan = loop.run_until_complete(
                    enhanced_workflow.refine_plan(workflow.plan, feedback)
                )
                workflow_sessions[session_id].plan = refined_plan
                emit('plan_created', {
                    'session_id': session_id,
                    'plan': refined_plan.dict()
                })
            except Exception as e:
                emit('error', {
                    'message': f'Error refining plan: {str(e)}'
                })
            finally:
                loop.close()
    
    @socketio.on('accept_plan')
    def handle_accept_plan(data):
        session_id = data.get('session_id', '')
        
        if not session_id or session_id not in workflow_sessions:
            emit('error', {'message': 'Invalid session ID'})
            return
        
        if accept_plan(session_id):
            workflow = workflow_sessions[session_id]
            
            # Create a background task to execute the plan
            @socketio.start_background_task
            def execute_plan_task():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                def send_update(message):
                    emit('workflow_update', {
                        'session_id': session_id,
                        'message': message
                    })
                
                try:
                    result = loop.run_until_complete(
                        enhanced_workflow.execute_plan(session_id, workflow.plan.steps, send_update)
                    )
                    emit('workflow_completed', {
                        'session_id': session_id,
                        'result': result
                    })
                except Exception as e:
                    emit('error', {
                        'message': f'Error executing plan: {str(e)}'
                    })
                finally:
                    loop.close()
            
            emit('plan_accepted', {'session_id': session_id})
        else:
            emit('error', {'message': 'Failed to accept plan'})
    
    @socketio.on('analyze_plan')
    def handle_analyze_plan(data):
        session_id = data.get('session_id', '')
        
        if not session_id or session_id not in workflow_sessions:
            emit('error', {'message': 'Invalid session ID'})
            return
        
        workflow = workflow_sessions[session_id]
        if not hasattr(workflow, 'plan'):
            emit('error', {'message': 'No plan exists to analyze'})
            return
        
        # Create a background task to analyze the plan
        @socketio.start_background_task
        def analyze_plan_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                analysis = loop.run_until_complete(
                    enhanced_workflow.analyze_plan(workflow.plan)
                )
                emit('plan_analysis', {
                    'session_id': session_id,
                    'analysis': analysis['analysis']
                })
            except Exception as e:
                emit('error', {
                    'message': f'Error analyzing plan: {str(e)}'
                })
            finally:
                loop.close()
    
    @socketio.on('get_workflow_status')
    def handle_get_workflow_status(data):
        session_id = data.get('session_id', '')
        
        if not session_id or session_id not in workflow_sessions:
            emit('error', {'message': 'Invalid session ID'})
            return
        
        workflow = workflow_sessions[session_id]
        emit('workflow_status', {
            'session_id': session_id,
            'status': workflow.status,
            'current_step': workflow.current_step_index,
            'total_steps': workflow.total_steps,
            'updates': workflow.updates,
            'final_result': workflow.final_result
        })
    
    app.socketio = socketio
    return app
