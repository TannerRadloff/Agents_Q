from flask import Flask
from app import create_app
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = create_app()

if __name__ == '__main__':
    # Get the socketio instance from the app
    socketio = app.socketio
    
    # Run the app with socketio
    # Disabled reloader and forcing single process mode for development session stability
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
