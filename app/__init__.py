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
from typing import Optional, Dict
from app.socket_events import register_socketio_events

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
    
    # Register Socket.IO event handlers from the separate module
    # We need the app context for the registration function to access current_app
    with app.app_context():
        register_socketio_events(socketio)

    return app
