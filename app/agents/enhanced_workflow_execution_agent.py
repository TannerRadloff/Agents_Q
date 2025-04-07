from agents import Agent, ModelSettings, function_tool
from app.models import Step
from typing import Dict, Any, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedWorkflowExecutionAgent:
    """Enhanced workflow execution agent with improved capabilities."""
    
    def __init__(self, model_name: str = "o3-mini", temperature: float = 0.7):
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
        from agents import WebSearchTool
        tools['web_search'] = WebSearchTool()
        
        # Mock FileSearchTool
        class MockFileSearchTool:
            def __init__(self, max_num_results=3, vector_store_ids=None):
                self.max_num_results = max_num_results
                self.vector_store_ids = vector_store_ids or ["mock_store_id"]
                self.name = "file_search"
                self.description = "Search through files for relevant information"
            
            def __call__(self, query: str) -> str:
                logger.info(f"Mock file search for: {query}")
                return f"Found information related to '{query}' in files (mock implementation)"
        
        tools['file_search'] = MockFileSearchTool(max_num_results=3, vector_store_ids=["mock_store_id"])
        
        # Mock ComputerTool
        class MockComputerTool:
            def __init__(self, computer=None):
                self.computer = computer or "mock_computer"
                self.name = "computer"
                self.description = "Perform operations on the computer"
            
            def __call__(self, command: str) -> str:
                logger.info(f"Mock computer command: {command}")
                return f"Executed command '{command}' on computer (mock implementation)"
        
        tools['computer'] = MockComputerTool(computer="mock_computer")
        
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
        def format_data(data: str, format_type: str = "json") -> str:
            """Format data into the specified format.
            
            Args:
                data: The data to format
                format_type: The format to convert to (json, xml, yaml)
                
            Returns:
                Formatted data as a string
            """
            if format_type.lower() == "json":
                return f"{{\"data\": \"{data}\"}}"
            elif format_type.lower() == "xml":
                return f"<data>{data}</data>"
            elif format_type.lower() == "yaml":
                return f"data: {data}"
            else:
                return data
        
        tools['format_data'] = format_data
        
        @function_tool
        def analyze_text(text: str) -> Dict[str, Any]:
            """Analyze text and extract key information.
            
            Args:
                text: The text to analyze
                
            Returns:
                Dictionary with analysis results
            """
            # This would normally use NLP or other analysis methods
            # For now, we'll return a mock analysis
            word_count = len(text.split())
            
            return {
                "word_count": word_count,
                "sentiment": "positive" if "good" in text.lower() or "great" in text.lower() else "neutral",
                "contains_question": "?" in text,
                "key_phrases": text.split(".")[:2]  # First two sentences as key phrases
            }
        
        tools['analyze_text'] = analyze_text
        
        @function_tool
        def generate_report(title: str, sections: List[Dict[str, str]]) -> str:
            """Generate a formatted report.
            
            Args:
                title: Report title
                sections: List of section dictionaries with 'heading' and 'content' keys
                
            Returns:
                Formatted report as a string
            """
            report = f"# {title}\n\n"
            
            for section in sections:
                heading = section.get('heading', 'Untitled Section')
                content = section.get('content', '')
                report += f"## {heading}\n\n{content}\n\n"
            
            return report
        
        tools['generate_report'] = generate_report
        
        logger.info(f"Initialized {len(tools)} tools for the execution agent")
        return tools
    
    def execute_step(self, step: Step, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a single step in the workflow.
        
        Args:
            step: The step to execute
            context: Optional context from previous steps
            
        Returns:
            Dictionary with execution results
        """
        # Prepare the input for the agent
        input_text = step.description
        
        # Add context if provided
        if context:
            context_str = "\nContext from previous steps:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            input_text += context_str
        
        # Execute the step
        logger.info(f"Executing step: {step.title}")
        result = self.agent.run_sync(input_text)
        
        # Extract tools used
        tools_used = []
        for action in result.actions:
            if hasattr(action, 'tool_name'):
                tools_used.append(action.tool_name)
        
        # Return the results
        return {
            'step': step,
            'result': result.final_output,
            'tools_used': tools_used,
            'success': True
        }
    
    def execute_steps_with_dependencies(self, steps: List[Step]) -> List[Dict[str, Any]]:
        """Execute a series of steps with dependency tracking.
        
        Args:
            steps: List of steps to execute
            
        Returns:
            List of execution results
        """
        results = []
        context = {}
        
        for i, step in enumerate(steps):
            logger.info(f"Executing step {i+1}/{len(steps)}: {step.title}")
            
            # Execute the step with context from previous steps
            step_result = self.execute_step(step, context)
            results.append(step_result)
            
            # Update context with this step's result
            context[f"step_{i+1}_result"] = step_result['result']
            context[f"step_{i+1}_title"] = step.title
        
        return results
