"""Test script for OpenAI API with dictionary-based Step model"""

import asyncio
import os
import logging
from openai import AsyncOpenAI
from agents import Agent, ModelSettings, Runner, set_default_openai_client
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dictionary-based schema instead of Pydantic model
STEP_SCHEMA = {
    "type": "object",
    "properties": {
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["title", "description"]
            }
        },
        "summary": {"type": "string"}
    },
    "required": ["steps", "summary"]
}

async def main():
    try:
        # Load environment variables
        load_dotenv()
        api_key = os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            return

        # Initialize OpenAI client with extended timeout
        client = AsyncOpenAI(
            api_key=api_key,
            timeout=60.0  # Extended timeout
        )
        set_default_openai_client(client)
        
        # Create agent with dictionary schema
        agent = Agent(
            name="Test Plan Agent",
            instructions=(
                "Create a plan with the following steps:\n"
                "1. Research the topic\n"
                "2. Analyze data\n"
                "3. Generate report\n"
                "\nMake sure to include a title and description for each step."
            ),
            model="o3-mini",
            model_settings=ModelSettings(),
            output_schema=STEP_SCHEMA
        )
        
        # Run the agent
        logger.info("Running the agent test with dictionary schema...")
        result = await Runner.run(agent, "Create a plan for researching dinosaurs")
        
        # Get the raw dictionary result
        plan_dict = result.final_output
        
        # Display the result
        logger.info("Test completed successfully!")
        logger.info(f"Summary: {plan_dict['summary']}")
        logger.info("Steps:")
        for i, step in enumerate(plan_dict['steps']):
            logger.info(f"  {i+1}. {step['title']}: {step['description'][:50]}...")
            
    except Exception as e:
        logger.error(f"Error in dictionary test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main()) 