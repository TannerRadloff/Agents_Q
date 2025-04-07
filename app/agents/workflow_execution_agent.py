from agents import Agent, ModelSettings, WebSearchTool, function_tool
from typing import Dict, Any, List

# Create a mock FileSearchTool since we don't have a real vector store
class MockFileSearchTool:
    def __init__(self, max_num_results=3, vector_store_ids=None):
        self.max_num_results = max_num_results
        self.vector_store_ids = vector_store_ids or ["mock_store_id"]
        self.name = "file_search"
        self.description = "Search through files for relevant information"
    
    def __call__(self, query: str) -> str:
        return f"Found information related to '{query}' in files (mock implementation)"

# Create a mock ComputerTool since we don't have a real computer interface
class MockComputerTool:
    def __init__(self, computer=None):
        self.computer = computer or "mock_computer"
        self.name = "computer"
        self.description = "Perform operations on the computer"
    
    def __call__(self, command: str) -> str:
        return f"Executed command '{command}' on computer (mock implementation)"

# Initialize tools
web_search_tool = WebSearchTool()
file_search_tool = MockFileSearchTool(max_num_results=3, vector_store_ids=["mock_store_id"])
computer_tool = MockComputerTool(computer="mock_computer")

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

# Create the execution agent
execution_agent = Agent(
    name="Execution Agent",
    instructions=(
        "You are an execution agent responsible for completing specific steps in a workflow. "
        "You have access to various tools that can help you complete these tasks. "
        "Use the appropriate tools based on the step description and requirements. "
        "Provide clear and concise results for each step you complete."
    ),
    model="o3-mini",
    tools=[
        web_search_tool,
        file_search_tool,
        computer_tool,
        calculate_sum,
        format_data
    ],
    model_settings=ModelSettings(
        temperature=0.7,
        tool_choice="auto"
    )
)
