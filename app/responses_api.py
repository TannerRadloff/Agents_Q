from agents import OpenAIResponsesModel
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
        logger.info("ResponsesAPIManager initialized")
    
    def create_responses_model(self, model_name: str = "o3-mini") -> OpenAIResponsesModel:
        """Create an OpenAIResponsesModel instance.
        
        Args:
            model_name: Name of the OpenAI model to use.
            
        Returns:
            An initialized OpenAIResponsesModel object.
        """
        try:
            model = OpenAIResponsesModel(model=model_name)
            logger.info(f"Created OpenAIResponsesModel with model: {model_name}")
            return model
        except Exception as e:
            logger.error(f"Error creating OpenAIResponsesModel: {str(e)}")
            raise
    
    def configure_model_settings(self, 
                                temperature: float = 0.7, 
                                top_p: float = 0.9,
                                tool_choice: str = "auto") -> Dict[str, Any]:
        """Configure model settings for the Responses API.
        
        Args:
            temperature: Controls randomness in the model's output.
            top_p: Controls diversity via nucleus sampling.
            tool_choice: How the model chooses to call tools.
            
        Returns:
            Dictionary of model settings.
        """
        settings = {
            "temperature": temperature,
            "top_p": top_p,
            "tool_choice": tool_choice
        }
        logger.info(f"Configured model settings: {settings}")
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
