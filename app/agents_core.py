from agents import Agent, Runner, WebSearchTool, FileSearchTool, ComputerTool, ModelSettings, function_tool
# Import ResponsesAPIManager if needed, but agent creation will use registry
# from app.responses_api import ResponsesAPIManager
from app.agent_registry import get_agent # Use the central agent retrieval function
from flask import current_app
import os
from typing import List, Dict, Any
import asyncio
import logging

# Import centralized tools if needed directly (though registry should handle this)
# from .tools import summarize_text_agent, all_tools

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentsQCore:
    """Core functionality for the Agents_Q application, focusing on direct chat."""

    def __init__(self):
        """Initialize the AgentsQCore."""
        # No need to initialize tools or ResponsesAPI here if using registry
        logger.info("AgentsQCore initialized. Relies on agent_registry for agent creation.")

    # Removed _register_custom_tools method

    # Removed create_agent method - Will use agent_registry.get_agent

    async def process_message(self, message: str, custom_instructions: str = None, tools: List[str] = None, model_name: str = None) -> Dict[str, Any]:
        """Process a user message through a dynamically configured or default agent.

        Args:
            message: The user's message.
            custom_instructions: Optional custom instructions for the agent.
            tools: Optional list of specific tool names to enable (uses registry tools).
            model_name: Optional name of the OpenAI model to use.

        Returns:
            A dictionary containing the agent's response and metadata.
        """
        try:
            # Determine target agent role (e.g., a default chat agent)
            # For now, let's assume a default role or configure one if needed
            # If custom_instructions are provided, we might need a mechanism
            # to create a temporary agent config or use a flexible default one.
            # Using "DefaultExecutor" as a simple starting point.
            agent_role = "DefaultExecutor"
            logger.info(f"Processing chat message using role: {agent_role}")

            # Get the agent instance from the registry
            agent = get_agent(agent_role)

            if not agent:
                raise ValueError(f"Could not retrieve agent for role '{agent_role}' from registry.")

            # --- Dynamic configuration (Optional - more complex) ---
            # If we needed to *override* the registry config based on API call:
            # effective_model = model_name or agent.model
            # effective_instructions = custom_instructions or agent.instructions
            # selected_tools_objs = []
            # if tools:
            #     # Map names to tool objects (requires access to tool mapping)
            #     # This implies needing access to `app.tools.all_tools` or similar
            #     # For simplicity, this example doesn't implement dynamic tool selection
            #     # based on names passed in the API call if they differ from the registry config.
            #     logger.warning("Dynamic tool selection via API not fully implemented, using registry config.")
            #     selected_tools_objs = agent.tools # Use registry tools for now
            # else:
            #     selected_tools_objs = agent.tools
            #
            # # Create a potentially temporary agent instance if overrides exist
            # if effective_model != agent.model or effective_instructions != agent.instructions:
            #     logger.info("Creating ad-hoc agent instance based on API parameters.")
            #     agent = Agent(
            #         name=f"Dynamic Chat Agent",
            #         instructions=effective_instructions,
            #         model=effective_model,
            #         tools=selected_tools_objs, # Needs careful handling
            #         model_settings=agent.model_settings # Or adjust settings too
            #     )
            # --- End Dynamic Configuration Example --- 

            # Run the agent obtained from the registry
            logger.info(f"Running agent '{agent.name}' for chat message: {message[:50]}...")
            result = await Runner.run(agent, message)

            tools_used = []
            if hasattr(result, 'messages'):
                for msg in result.messages:
                    if msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            # Ensure we handle potential ToolCall object structure
                            tool_name = getattr(tool_call, 'name', str(tool_call))
                            tools_used.append(tool_name)

            final_output = getattr(result, 'final_output', "Agent did not produce final output.")

            return {
                'response': final_output,
                'tools_used': list(set(tools_used)), # Unique tool names
                'success': True
            }

        except Exception as e:
            logger.error(f"Error processing chat message: {e}", exc_info=True)
            error_str = str(e) if e else "Unknown error"
            return {
                'response': f"I encountered an error processing your request: {error_str}",
                'tools_used': [],
                'success': False,
                'error': error_str
            }

# Removed the process_message_sync function 