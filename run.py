from flask import Flask
from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Get the socketio instance from the app
    socketio = app.socketio
    
    # Run the app with socketio
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
