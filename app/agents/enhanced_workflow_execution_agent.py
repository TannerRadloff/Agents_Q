from agents import Agent, ModelSettings, function_tool, Runner, WebSearchTool
from app.models import Step
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define Pydantic model for report sections
class ReportSection(BaseModel):
    heading: str
    content: str

# Define Pydantic model for text analysis output
class TextAnalysisOutput(BaseModel):
    sentiment: str
    key_phrases: List[str]
    summary: str
    word_count: int

class EnhancedWorkflowExecutionAgent:
    """Enhanced workflow execution agent with improved capabilities."""
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.7):
        """Initialize the enhanced workflow execution agent.
        
        Args:
            model_name: Name of the OpenAI model to use
            temperature: Temperature setting for the model
        """
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Create the execution agent
        self.agent = Agent(
            name="Enhanced Execution Agent",
            instructions=(
                "You are an execution agent responsible for completing specific steps in a workflow. "
                "You have access to various tools that can help you complete these tasks. "
                "Use the appropriate tools based on the step description and requirements. "
                "Provide clear and concise results for each step you complete.\n\n"
                "For each step, follow this process:\n"
                "1. Understand the objective of the step\n"
                "2. Determine which tools are needed to complete the step\n"
                "3. Use the tools in the correct sequence\n"
                "4. Verify the results before finalizing\n"
                "5. Provide a detailed report of what was done and the outcome\n\n"
                "Be thorough in your execution and provide detailed explanations of your actions."
            ),
            model=model_name,
            tools=list(self.tools.values()),
            model_settings=ModelSettings(
                temperature=temperature,
                tool_choice="auto"
            )
        )
        logger.info(f"Enhanced Workflow Execution Agent initialized with model: {model_name}")
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize all available tools.
        
        Returns:
            Dictionary of tools
        """
        tools = {}
        
        # Web search tool
        tools['web_search'] = WebSearchTool()
        
        # Custom function tools
        @function_tool
        def calculate_sum(a: float, b: float) -> float:
            """Calculate the sum of two numbers.
            
            Args:
                a: First number
                b: Second number
                
            Returns:
                The sum of a and b
            """
            return a + b
        
        tools['calculate_sum'] = calculate_sum
        
        @function_tool
        def format_data(data: str, format_type: str) -> str:
            """Format data into the specified format.
            
            Args:
                data: The data to format
                format_type: The format to convert to (json, xml, yaml)
                
            Returns:
                Formatted data as a string
            """
            # Handle case where format_type might not be provided by LLM, default internally
            effective_format_type = format_type.lower() if format_type else "json"

            if effective_format_type == "json":
                return f"{{\"data\": \"{data}\"}}"
            elif effective_format_type == "xml":
                return f"<data>{data}</data>"
            elif effective_format_type == "yaml":
                return f"data: {data}"
            else:
                # Fallback if an unknown format is requested
                return data
        
        tools['format_data'] = format_data
        
        @function_tool
        async def analyze_text(text: str) -> Dict[str, Any]:
            """Analyze text for sentiment, key phrases, and summary using an internal agent.
            
            Args:
                text: The text to analyze
                
            Returns:
                Dictionary with analysis results (sentiment, key_phrases, summary, word_count)
            """
            logger.info(f"Running internal analysis agent on text (length: {len(text)})...")
            try:
                # Use the same model as the parent agent for consistency, or choose a specific one
                analyzer_model = self.agent.model 

                # Create a dedicated agent for text analysis
                analysis_agent = Agent(
                    name="Text Analysis Agent",
                    instructions=(
                        "Analyze the following text. Determine the overall sentiment (positive, negative, neutral), "
                        "extract the top 3-5 key phrases, provide a concise one-sentence summary, "
                        "and count the total number of words. Output the results in the specified format."
                    ),
                    model=analyzer_model,
                    output_type=TextAnalysisOutput, # Use the defined Pydantic model
                    tools=[], # No tools needed for analysis
                    model_settings=ModelSettings(tool_choice="none")
                )

                # Run the analysis agent (use await as this function is now async)
                result = await Runner.run(analysis_agent, text)
                
                # Extract the structured output
                analysis_output = result.final_output_as(TextAnalysisOutput)
                logger.info("Internal analysis agent finished.")
                # Return the Pydantic model as a dictionary
                return analysis_output.dict()
            
            except Exception as e:
                logger.error(f"Error in analyze_text tool: {e}", exc_info=True)
                return {
                    "error": "Failed to analyze text due to an internal error.",
                    "sentiment": "unknown",
                    "key_phrases": [],
                    "summary": "Analysis failed.",
                    "word_count": len(text.split()) # Provide basic word count even on failure
                }
        
        tools['analyze_text'] = analyze_text
        
        @function_tool
        def generate_report(title: str, sections: List[ReportSection]) -> str:
            """Generate a formatted report.
            
            Args:
                title: Report title
                sections: List of section objects with 'heading' and 'content' attributes
                
            Returns:
                Formatted report as a string
            """
            report = f"# {title}\n\n"
            
            for section in sections:
                # Access attributes directly from Pydantic model
                report += f"## {section.heading}\n\n{section.content}\n\n"
            
            return report
        
        tools['generate_report'] = generate_report
        
        logger.info(f"Initialized {len(tools)} tools for the execution agent")
        return tools
