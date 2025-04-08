import os
import time
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, ModelSettings, OpenAIResponsesModel, set_default_openai_client

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.environ.get('OPENAI_API_KEY')
print(f"API Key found and has length: {len(api_key) if api_key else 'No API key found'}")

async def test_responses_api_directly():
    """Test the Responses API directly with different timeout settings."""
    print("\n=== Testing Responses API directly ===")
    
    timeouts = [10.0, 30.0, 60.0, 120.0]
    
    for timeout in timeouts:
        print(f"\nTesting with timeout: {timeout} seconds")
        try:
            # Create client with specific timeout
            client = AsyncOpenAI(
                api_key=api_key,
                timeout=timeout
            )
            
            # Call the Responses API
            start_time = time.time()
            response = await client.responses.create(
                model="o3-mini",
                input="Say hello briefly",
                store=False
            )
            elapsed = time.time() - start_time
            
            # Extract the text from the response
            output_text = None
            for item in response.output:
                if hasattr(item, 'content') and item.content:
                    for content_item in item.content:
                        if hasattr(content_item, 'text'):
                            output_text = content_item.text
                            break
            
            print(f"✅ Success with {timeout}s timeout! Response received in {elapsed:.2f} seconds")
            print(f"  Content: {output_text}")
            
        except Exception as e:
            print(f"❌ Error with {timeout}s timeout: {str(e)}")

async def test_responses_api_via_sdk():
    """Test the Responses API via SDK with different timeout settings."""
    print("\n=== Testing Responses API via SDK ===")
    
    timeouts = [30.0, 60.0, 120.0]
    
    for timeout in timeouts:
        print(f"\nTesting with timeout: {timeout} seconds")
        try:
            # Create client with specific timeout
            client = AsyncOpenAI(
                api_key=api_key,
                timeout=timeout
            )
            set_default_openai_client(client)
            
            # Create a responses model
            responses_model = OpenAIResponsesModel(
                model="o3-mini",
                openai_client=client
            )
            
            # Create agent with the responses model
            agent = Agent(
                name="Test Agent",
                instructions="You are a helpful assistant that responds concisely.",
                model=responses_model,
                model_settings=ModelSettings()
            )
            
            # Run the agent
            print("Agent created with OpenAIResponsesModel. Running with prompt...")
            start_time = time.time()
            result = await Runner.run(agent, "Say hello briefly")
            elapsed = time.time() - start_time
            
            print(f"✅ Agent SDK with Responses API success! Response received in {elapsed:.2f} seconds")
            print(f"  Result: {result.final_output}")
            
        except Exception as e:
            print(f"❌ Agent SDK with Responses API error: {str(e)}")
            import traceback
            traceback.print_exc()

async def test_model_string():
    """Test using model string instead of model instance."""
    print("\n=== Testing with model string instead of model instance ===")
    
    try:
        # Configure default client with longer timeout
        client = AsyncOpenAI(
            api_key=api_key,
            timeout=60.0
        )
        set_default_openai_client(client)
        
        # Create agent with model string
        agent = Agent(
            name="Test Agent",
            instructions="You are a helpful assistant that responds concisely.",
            model="o3-mini"
        )
        
        print("Agent created with model string 'o3-mini'. Running with prompt...")
        start_time = time.time()
        result = await Runner.run(agent, "Say hello briefly")
        elapsed = time.time() - start_time
        
        print(f"✅ Agent with model string success! Response received in {elapsed:.2f} seconds")
        print(f"  Result: {result.final_output}")
        
    except Exception as e:
        print(f"❌ Agent with model string error: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    print("Starting targeted Responses API tests...")
    
    await test_responses_api_directly()
    await test_responses_api_via_sdk()
    await test_model_string()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 