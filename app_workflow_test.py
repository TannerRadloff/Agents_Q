import os
import asyncio
import time
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, ModelSettings, OpenAIResponsesModel, set_default_openai_client
from pydantic import BaseModel
from typing import List, Optional

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.environ.get('OPENAI_API_KEY')
print(f"API Key found and has length: {len(api_key) if api_key else 'No API key found'}")

# Mock classes that mirror our application's structure
class Step(BaseModel):
    title: str
    description: str
    status: Optional[str] = None
    result: Optional[str] = None

class PlanOutput(BaseModel):
    steps: List[Step]
    summary: str

class EnhancedPlanCreationAgent:
    """Simplified version of our app's plan creation agent."""
    
    def __init__(self, model_name: str = "o3-mini"):
        # Configure client with extended timeout
        client = AsyncOpenAI(
            api_key=api_key,
            timeout=60.0  # Extended timeout
        )
        set_default_openai_client(client)
        
        self.agent = Agent(
            name="Enhanced Plan Creation Agent",
            instructions=(
                "You are a sophisticated planning agent. Your task is to break down a user's request into a series of clear, actionable steps. "
                "Analyze the user's request carefully. "
                "If the request requires generating a structured document like a report, analysis, or detailed summary, ensure the **final step** is titled exactly: **'Synthesize Findings and Generate Final Report'**. This step will be handled by a specialized writing agent. "
                "For all other requests (e.g., simple questions, calculations), create only the necessary execution steps without the special final synthesis step. "
                "Define each step with a concise title and a clear description of the task. "
                "Provide a brief overall summary of the plan."
                "Output the plan as a structured list of steps according to the required format."
            ),
            model=model_name,
            model_settings=ModelSettings(),
            output_type=PlanOutput
        )
        print(f"Enhanced Plan Creation Agent initialized with model: {model_name}")
    
    async def create_plan(self, user_input: str) -> PlanOutput:
        """Create a plan based on user input."""
        print(f"Creating plan for input: '{user_input[:100]}...'")
        
        try:
            print(f"Calling Runner.run with input: '{user_input[:100]}...'")
            result = await Runner.run(self.agent, user_input)
            
            plan_output = result.final_output_as(PlanOutput)
            print(f"Successfully created plan with {len(plan_output.steps)} steps")
            
            return plan_output
        except Exception as e:
            print(f"Error during plan creation: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

async def test_with_different_prompts():
    """Test plan creation with different prompts."""
    agent = EnhancedPlanCreationAgent(model_name="o3-mini")
    
    prompts = [
        "Write a brief summary of climate change",
        "Create a marketing plan for a new product",
        "Analyze the pros and cons of remote work",
        "Generate a meal plan for a week",
        "Research the latest advancements in renewable energy"
    ]
    
    for i, prompt in enumerate(prompts):
        print(f"\n\nTest {i+1}: '{prompt}'")
        
        try:
            start_time = time.time()
            plan = await agent.create_plan(prompt)
            elapsed = time.time() - start_time
            
            print(f"✅ Success! Plan created in {elapsed:.2f} seconds")
            print(f"Summary: {plan.summary}")
            print("Steps:")
            for j, step in enumerate(plan.steps):
                print(f"  {j+1}. {step.title}")
        except Exception as e:
            print(f"❌ Failed: {str(e)}")

async def main():
    print("Starting application workflow test...")
    
    await test_with_different_prompts()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 