from agents import Agent, Runner, WebSearchTool, FileSearchTool, ComputerTool, function_tool, ModelSettings
from app.responses_api import ResponsesAPIManager
import os
from typing import List, Dict, Any
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentsQCore:
    """Core functionality for the Agents_Q application."""
    
    def __init__(self):
        """Initialize the AgentsQCore with default tools and configuration."""
        # Initialize the ResponsesAPIManager
        api_key = os.getenv('OPENAI_API_KEY')
        self.responses_api = ResponsesAPIManager(api_key)
        
        self.available_tools = {
            'web_search': WebSearchTool(),
            # FileSearchTool requires vector_store_ids, so we'll skip it for testing
            # 'file_search': FileSearchTool(vector_store_ids=["test_store"]),
            # ComputerTool requires a computer parameter, so we'll skip it for testing
            # 'computer': ComputerTool(computer="test_computer")
        }
        
        # Add custom function tools
        self.available_tools.update(self._register_custom_tools())
    
    def _register_custom_tools(self) -> Dict[str, Any]:
        """Register custom function tools."""
        custom_tools = {}
        
        @function_tool
        def summarize_text(text: str) -> str:
            """Summarize a piece of text.
            
            Args:
                text: The text to summarize.
            
            Returns:
                A summary of the provided text.
            """
            # This is a placeholder. The actual implementation will use the agent itself
            # to generate a summary through a separate agent call.
            return f"Summary of text: {text[:100]}..."
        
        custom_tools['summarize'] = summarize_text
        
        return custom_tools
    
    def create_agent(self, instructions: str = None, tools: List[str] = None, model_name: str = "o3-mini") -> Agent:
        """Create an agent with specified instructions and tools.
        
        Args:
            instructions: Custom instructions for the agent.
            tools: List of tool names to include.
            model_name: Name of the OpenAI model to use.
            
        Returns:
            An initialized Agent object.
        """
        # Default instructions if none provided
        if not instructions:
            instructions = (
                "You are a helpful assistant that can use various tools to help users complete tasks. "
                "Use the appropriate tools based on the user's request. "
                "Always provide clear explanations of your actions and findings."
            )
        
        # Select tools based on provided list or use all available tools
        selected_tools = []
        if tools:
            for tool_name in tools:
                if tool_name in self.available_tools:
                    selected_tools.append(self.available_tools[tool_name])
                else:
                    logger.warning(f"Tool '{tool_name}' not found in available tools.")
        else:
            selected_tools = list(self.available_tools.values())
        
        # Create model settings
        model_settings = ModelSettings(
            **self.responses_api.configure_model_settings()
        )
        
        # Create and return the agent using the Responses API model
        try:
            responses_model = self.responses_api.create_responses_model(model_name)
            
            agent = Agent(
                name="Agents_Q Assistant",
                instructions=instructions,
                tools=selected_tools,
                model=responses_model,
                model_settings=model_settings
            )
            
            logger.info(f"Created agent with model: {model_name} and {len(selected_tools)} tools")
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent with Responses API: {str(e)}")
            # Fallback to default model if Responses API fails
            logger.info("Falling back to default model")
            agent = Agent(
                name="Agents_Q Assistant",
                instructions=instructions,
                tools=selected_tools,
                model=model_name,
                model_settings=model_settings
            )
            return agent
    
    async def process_message(self, message: str, custom_instructions: str = None, tools: List[str] = None, model_name: str = "o3-mini") -> Dict[str, Any]:
        """Process a user message through an agent.
        
        Args:
            message: The user's message.
            custom_instructions: Optional custom instructions for the agent.
            tools: Optional list of specific tools to use.
            model_name: Name of the OpenAI model to use.
            
        Returns:
            A dictionary containing the agent's response and metadata.
        """
        try:
            # Create an agent with specified or default configuration
            agent = self.create_agent(
                instructions=custom_instructions, 
                tools=tools,
                model_name=model_name
            )
            
            # Run the agent
            logger.info(f"Processing message: {message[:50]}...")
            result = await Runner.run(agent, message)
            
            # Extract tools used
            tools_used = []
            for msg in result.messages:
                if msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tools_used.append(tool_call.name)
            
            # Return the result
            return {
                'response': result.final_output,
                'tools_used': tools_used,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                'response': f"I encountered an error while processing your request: {str(e)}",
                'tools_used': [],
                'success': False,
                'error': str(e)
            }
    
    def process_message_sync(self, message: str, custom_instructions: str = None, tools: List[str] = None, model_name: str = "o3-mini") -> Dict[str, Any]:
        """Synchronous wrapper for process_message.
        
        Args:
            message: The user's message.
            custom_instructions: Optional custom instructions for the agent.
            tools: Optional list of specific tools to use.
            model_name: Name of the OpenAI model to use.
            
        Returns:
            A dictionary containing the agent's response and metadata.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.process_message(message, custom_instructions, tools, model_name))
        loop.close()
        return result
