import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.environ.get('OPENAI_API_KEY')
print(f"API Key found and has length: {len(api_key) if api_key else 'No API key found'}")

try:
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Make a simple API call
    models = client.models.list()
    print("Models API call successful")
    print(f"Number of models available: {len(models.data)}")
    print(f"First few models: {[model.id for model in models.data[:5]]}")
    
    # Test a basic completion
    print("\nTesting chat completion...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello world!"}
        ]
    )
    print(f"Chat completion successful: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"Error: {str(e)}") 