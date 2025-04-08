import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
from agents import Agent, Runner, set_default_openai_client, ModelSettings

# Load environment variables
load_dotenv()
api_key = os.environ.get('OPENAI_API_KEY')

# Define our fixed models
class Step(BaseModel):
    title: str
    description: str
    status: Optional[str] = None  # Removed default value
    result: Optional[str] = None

class PlanOutput(BaseModel):
    steps: List[Step]
    summary: str

async def test_model_with_responses_api():
    """Test our fixed models with the Responses API."""
    print("Testing fixed model with Responses API...")
    
    # Configure client with extended timeout
    client = AsyncOpenAI(
        api_key=api_key,
        timeout=60.0
    )
    set_default_openai_client(client)
    
    # Create agent with our fixed model
    agent = Agent(
        name="Plan Creation Agent",
        instructions=(
            "You are a planning agent. Create a plan with steps for the user's request. "
            "Each step should have a title and description."
        ),
        model="o3-mini",
        model_settings=ModelSettings(),
        output_type=PlanOutput
    )
    
    # Run the agent
    try:
        result = await Runner.run(agent, "Write a short essay about climate change")
        plan = result.final_output_as(PlanOutput)
        
        print(f"✅ Success! Created plan with {len(plan.steps)} steps")
        print(f"Summary: {plan.summary}")
        print("Steps:")
        for i, step in enumerate(plan.steps):
            print(f"  {i+1}. {step.title}: {step.description[:50]}...")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    await test_model_with_responses_api()

if __name__ == "__main__":
    asyncio.run(main()) 