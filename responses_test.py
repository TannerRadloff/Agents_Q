import os
from dotenv import load_dotenv
from openai import OpenAI
import time
import json

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.environ.get('OPENAI_API_KEY')
print(f"API Key found and has length: {len(api_key) if api_key else 'No API key found'}")

try:
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    print("Testing the Responses API directly with gpt-4o...")
    start_time = time.time()
    
    # Call the Responses API with gpt-4o
    response = client.responses.create(
        model="gpt-4o",
        input="What's the weather like in New York?",
        tools=[{"type": "web_search_preview"}]
    )
    
    elapsed = time.time() - start_time
    print(f"Response received in {elapsed:.2f} seconds")
    print(f"Response ID: {response.id}")
    
    # The Responses API format is different
    if hasattr(response, 'content'):
        for content_block in response.content:
            if content_block.type == 'text':
                print(f"Content: {content_block.text}")
    
    # Check if any tools were used
    if hasattr(response, 'tool_uses'):
        print(f"\nTool uses: {len(response.tool_uses)}")
        for tool_use in response.tool_uses:
            print(f"Tool: {tool_use.type}")
            if hasattr(tool_use, 'retrieved_results'):
                print(f"Results: {tool_use.retrieved_results}")
    else:
        print("\nNo tools were used")
    
    # Print the full response for analysis
    print("\nFull response structure:")
    for attr in dir(response):
        if not attr.startswith('_') and not callable(getattr(response, attr)):
            value = getattr(response, attr)
            print(f"{attr}: {value}")
    
except Exception as e:
    print(f"Error: {str(e)}") 