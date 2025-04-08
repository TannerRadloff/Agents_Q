import os
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, WebSearchTool, function_tool

# Load environment variables from .env file
load_dotenv()

@function_tool
def hello_world(name: str) -> str:
    """Say hello to someone.
    
    Args:
        name: The name of the person to greet.
    """
    return f"Hello, {name}!"

async def main():
    print("Testing the OpenAI Agents SDK...")
    
    try:
        # Create a simple agent
        agent = Agent(
            name="Test Agent",
            instructions="You are a helpful assistant that responds concisely.",
            tools=[hello_world],
            model="gpt-3.5-turbo"  # Using 3.5 turbo first as it's faster/cheaper
        )
        
        print("Agent created successfully")
        
        # Test running the agent
        print("\nRunning agent with basic query...")
        result = await Runner.run(agent, "Say hello to Claude")
        print(f"Result: {result.final_output}")
        
        # Now test with a web search agent (gpt-4o required)
        print("\nCreating agent with web search tool...")
        search_agent = Agent(
            name="Web Search Agent",
            instructions="You are a helpful assistant that searches the web for information.",
            tools=[WebSearchTool()],
            model="gpt-4o"  # gpt-4o is required for WebSearchTool
        )
        
        # Test running the search agent with a simple query
        print("\nRunning web search agent...")
        search_result = await Runner.run(search_agent, "What day of the week was March 15, 2025?")
        print(f"Web search result: {search_result.final_output}")
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 