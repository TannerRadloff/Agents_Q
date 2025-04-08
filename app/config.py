import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

# App configuration
class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    DEBUG = True
    # Add SQLite Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEFAULT_MODEL_NAME = os.environ.get('DEFAULT_MODEL_NAME') or 'gpt-4o'

    # Optional: Other configurations if needed
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
