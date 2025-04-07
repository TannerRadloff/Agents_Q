import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# App configuration
class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SECRET_KEY = os.urandom(24)
    DEBUG = True
