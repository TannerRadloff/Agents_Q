from flask import Blueprint, request, jsonify
import os
from app.agents_core import AgentsQCore
from app.workflow import get_workflow_state
import asyncio

agent_bp = Blueprint('agent', __name__)
agents_core = AgentsQCore()

@agent_bp.route('/chat', methods=['POST'])
async def chat():
    """Handle chat requests to the agent."""
    data = request.json
    user_message = data.get('message', '')
    custom_instructions = data.get('instructions', None)
    tools = data.get('tools', None)
    model_name = data.get('model', 'o3-mini')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Process the message using the AgentsQCore asynchronously
    result = await agents_core.process_message(
        message=user_message,
        custom_instructions=custom_instructions,
        tools=tools,
        model_name=model_name
    )
    
    # Return the response
    if result['success']:
        return jsonify({
            'response': result['response'],
            'tools_used': result['tools_used']
        })
    else:
        return jsonify({
            'error': result['error'],
            'response': result['response']
        }), 500

@agent_bp.route('/workflow/<session_id>', methods=['GET'])
def get_workflow(session_id):
    """Get the current state of a workflow."""
    workflow = get_workflow_state(session_id)
    
    if not workflow:
        return jsonify({'error': 'Workflow not found'}), 404
    
    return jsonify({
        'session_id': workflow.session_id,
        'status': workflow.status,
        'current_step': workflow.current_step_index,
        'total_steps': workflow.total_steps,
        'updates': workflow.updates,
        'final_result': workflow.final_result
    })
