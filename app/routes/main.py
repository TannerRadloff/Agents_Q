from flask import Blueprint, render_template, request, jsonify
from app.enhanced_workflow import create_workflow_session

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main workflow interface."""
    # Create a new session ID for the workflow
    session_id = create_workflow_session()
    return render_template('index.html', session_id=session_id)

@main_bp.route('/chat')
def chat():
    """Render the original chat interface."""
    return render_template('chat.html')
