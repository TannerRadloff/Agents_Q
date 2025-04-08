from agents import OpenAIResponsesModel
from openai import OpenAI
from typing import Dict, Any, Optional, List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResponsesAPIManager:
    """Manager class for OpenAI Responses API integration."""
    
    def __init__(self, api_key: str):
        """Initialize the ResponsesAPIManager.
        
        Args:
            api_key: OpenAI API key for authentication.
        """
        self.api_key = api_key
        self.openai_client = OpenAI(api_key=self.api_key)
        logger.info("ResponsesAPIManager initialized")
    
    def configure_model_settings(self, 
                                model_name: str,
                                temperature: float = 0.7, 
                                top_p: float = 0.9,
                                tool_choice: str = "auto") -> Dict[str, Any]:
        """Configure model settings for the Responses API.
        
        Args:
            model_name: Name of the OpenAI model being used.
            temperature: Controls randomness in the model's output.
            top_p: Controls diversity via nucleus sampling.
            tool_choice: How the model chooses to call tools.
            
        Returns:
            Dictionary of model settings.
        """
        settings = {
            "tool_choice": tool_choice
        }
        
        # Only include temperature and top_p if not using o3-mini
        if model_name != "o3-mini":
            settings["temperature"] = temperature
            settings["top_p"] = top_p

        logger.info(f"Configured model settings for {model_name}: {settings}")
        return settings
    
    def handle_streaming_response(self, stream_handler: Optional[callable] = None) -> callable:
        """Create a handler for streaming responses.
        
        Args:
            stream_handler: Optional custom handler function for stream events.
            
        Returns:
            A function that can process streaming events.
        """
        def default_stream_handler(event):
            """Default handler for streaming events."""
            if event.type == "content_block_delta":
                return {"type": "content", "content": event.delta}
            elif event.type == "tool_call":
                return {"type": "tool_call", "name": event.tool_call.name}
            elif event.type == "tool_result":
                return {"type": "tool_result", "result": event.result}
            return {"type": "other", "event": str(event.type)}
        
        return stream_handler if stream_handler else default_stream_handler
