import os
import time
import asyncio
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
import httpx
from agents import Agent, Runner, set_default_openai_client

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.environ.get('OPENAI_API_KEY')
print(f"API Key found and has length: {len(api_key) if api_key else 'No API key found'}")

async def test_with_timeouts():
    """Test OpenAI API with different timeout settings."""
    print("\n=== Testing with different timeout settings ===")
    
    timeouts = [5.0, 10.0, 30.0, 60.0]
    
    for timeout in timeouts:
        print(f"\nTesting with timeout: {timeout} seconds")
        try:
            # Create client with specific timeout
            client = AsyncOpenAI(
                api_key=api_key,
                timeout=timeout
            )
            
            start_time = time.time()
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            elapsed = time.time() - start_time
            
            print(f"✅ Success with {timeout}s timeout! Response received in {elapsed:.2f} seconds")
            print(f"  Content: {response.choices[0].message.content}")
            
        except Exception as e:
            print(f"❌ Error with {timeout}s timeout: {str(e)}")

async def test_with_proxy():
    """Test OpenAI API with and without proxy settings."""
    print("\n=== Testing with proxy settings ===")
    
    # Test without proxy (direct connection)
    print("\nTesting without proxy:")
    try:
        client = AsyncOpenAI(api_key=api_key)
        start_time = time.time()
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        elapsed = time.time() - start_time
        print(f"✅ Success without proxy! Response received in {elapsed:.2f} seconds")
    except Exception as e:
        print(f"❌ Error without proxy: {str(e)}")
    
    # Common proxy environment variables
    proxies = {
        "http://": os.environ.get("HTTP_PROXY"),
        "https://": os.environ.get("HTTPS_PROXY")
    }
    
    if any(proxies.values()):
        print(f"\nFound proxy settings in environment: {proxies}")
        try:
            # Create httpx client with proxies
            transport = httpx.AsyncHTTPTransport(proxy=proxies["http://"] or proxies["https://"])
            httpx_client = httpx.AsyncClient(transport=transport)
            
            # Create OpenAI client with custom httpx client
            client = AsyncOpenAI(api_key=api_key, http_client=httpx_client)
            
            start_time = time.time()
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            elapsed = time.time() - start_time
            print(f"✅ Success with proxy! Response received in {elapsed:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Error with proxy: {str(e)}")
    else:
        print("No proxy settings found in environment variables.")

async def test_agent_sdk():
    """Test the OpenAI Agents SDK with o3-mini model."""
    print("\n=== Testing Agents SDK with o3-mini ===")
    
    try:
        # Configure a custom client with longer timeout
        custom_client = AsyncOpenAI(
            api_key=api_key,
            timeout=60.0
        )
        set_default_openai_client(custom_client)
        
        # Create simple agent
        agent = Agent(
            name="Test Agent",
            instructions="You are a helpful assistant that responds concisely.",
            model="o3-mini"
        )
        
        print("Agent created. Running with prompt...")
        start_time = time.time()
        result = await Runner.run(agent, "Say hello")
        elapsed = time.time() - start_time
        
        print(f"✅ Agent SDK success! Response received in {elapsed:.2f} seconds")
        print(f"  Result: {result.final_output}")
        
    except Exception as e:
        print(f"❌ Agent SDK error: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    print("Starting OpenAI connectivity tests...")
    
    # Test direct API access
    try:
        print("\n=== Testing direct API access ===")
        client = OpenAI(api_key=api_key)
        start_time = time.time()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        elapsed = time.time() - start_time
        print(f"✅ Direct API test successful! Response received in {elapsed:.2f} seconds")
        print(f"  Content: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Direct API test failed: {str(e)}")
    
    # Run more detailed tests
    await test_with_timeouts()
    await test_with_proxy()
    await test_agent_sdk()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 