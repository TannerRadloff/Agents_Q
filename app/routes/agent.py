from flask import Blueprint, request, jsonify
import os
from app.agents_core import AgentsQCore

agent_bp = Blueprint('agent', __name__)
agents_core = AgentsQCore()

@agent_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests to the agent."""
    data = request.json
    user_message = data.get('message', '')
    custom_instructions = data.get('instructions', None)
    tools = data.get('tools', None)
    model_name = data.get('model', 'o3-mini')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Process the message using the AgentsQCore
    result = agents_core.process_message_sync(
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
