from flask import Flask
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.agent import agent_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(agent_bp, url_prefix='/api')
    
    return app
