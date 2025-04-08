import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from typing import List, Optional
from agents import Agent, Runner, set_default_openai_client, ModelSettings

# Load environment variables
load_dotenv()
api_key = os.environ.get('OPENAI_API_KEY')

# Define the fixed Step model (explicit status field without default)
class Step(BaseModel):
    title: str
    description: str
    status: Optional[str] = None  # No default value
    result: Optional[str] = None

# Define the plan output model
class PlanOutput(BaseModel):
    steps: List[Step]
    summary: str

async def test_step_model():
    """Test our fixed Step model with the Responses API."""
    print("Testing fixed Step model...")
    
    # Configure client with extended timeout
    client = AsyncOpenAI(
        api_key=api_key,
        timeout=60.0
    )
    set_default_openai_client(client)
    
    # Create agent with our fixed model
    agent = Agent(
        name="Step Test Agent",
        instructions=(
            "You are a planning agent. Create steps for the user's request.\n"
            "For each step, include a title and description.\n"
            "Make sure there are at least 3 steps in the plan.\n"
        ),
        model="o3-mini",
        model_settings=ModelSettings(),
        output_type=PlanOutput
    )
    
    # Test with a simple prompt
    prompt = "Create a plan to organize a small dinner party"
    print(f"Testing with prompt: '{prompt}'")
    
    # Run the agent
    try:
        result = await Runner.run(agent, prompt)
        plan = result.final_output_as(PlanOutput)
        
        print(f"✅ Success! Created plan with {len(plan.steps)} steps")
        print(f"Summary: {plan.summary}")
        print("Steps:")
        for i, step in enumerate(plan.steps):
            print(f"  {i+1}. {step.title}")
            print(f"     Description: {step.description[:50]}...")
            print(f"     Status: {step.status or 'None'}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    await test_step_model()

if __name__ == "__main__":
    asyncio.run(main()) 