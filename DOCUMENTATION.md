# Agents_Q Documentation

## Overview

Agents_Q is a Python application that leverages OpenAI's Agents SDK and Responses API to create an agentic experience. Users can submit tasks through a chat interface, and the application will deploy agents with various tools to complete these tasks.

## Architecture

The application consists of:

1. **Backend**: Python-based backend using Flask and the OpenAI Agents SDK
2. **Frontend**: Simple chat interface built with HTML, CSS, and JavaScript
3. **Core Components**:
   - `agents_core.py`: Core functionality for agent creation and management
   - `responses_api.py`: Integration with OpenAI's Responses API
   - Flask routes for handling HTTP requests

## Installation

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/TannerRadloff/Agents_Q.git
   cd Agents_Q
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Running the Application

1. Activate the virtual environment (if not already activated)
2. Run the application:
   ```bash
   python run.py
   ```
3. Open your browser and navigate to `http://localhost:5000`

## Usage

1. **Chat Interface**: Type your query or task in the chat input field and press Enter or click Send
2. **Agent Response**: The agent will process your request and respond in the chat
3. **Tool Usage**: The agent can use various tools to complete tasks, including:
   - Web search
   - (File search and Computer tools are available in the code but disabled for testing)

## API Endpoints

### POST /api/chat

Sends a message to the agent and receives a response.

**Request Body**:
```json
{
  "message": "Your message here",
  "instructions": "Optional custom instructions",
  "tools": ["optional", "list", "of", "tool", "names"],
  "model": "o3-mini"
}
```

**Response**:
```json
{
  "response": "Agent's response",
  "tools_used": ["list", "of", "tools", "used"]
}
```

## Customization

### Adding Custom Tools

You can add custom tools by modifying the `_register_custom_tools` method in `app/agents_core.py`:

```python
def _register_custom_tools(self) -> Dict[str, Any]:
    """Register custom function tools."""
    custom_tools = {}
    
    @function_tool
    def your_custom_tool(param1: str, param2: int) -> str:
        """Description of your tool.
        
        Args:
            param1: Description of param1.
            param2: Description of param2.
        
        Returns:
            Description of return value.
        """
        # Implementation
        return "Result"
    
    custom_tools['your_tool_name'] = your_custom_tool
    
    return custom_tools
```

### Changing Agent Instructions

You can modify the default agent instructions in the `create_agent` method in `app/agents_core.py`.

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure you've activated the virtual environment and installed all dependencies
2. **API Key Issues**: Check that your `.env` file contains the correct OpenAI API key
3. **Tool Initialization Errors**: Some tools require specific parameters; check the error message for details

### Logging

The application uses Python's logging module. Check the console output for error messages and information.

## Future Enhancements

1. Implement WebSocket for real-time communication
2. Add user authentication
3. Enable file upload for document analysis
4. Implement conversation history storage
5. Add more custom tools

## License

This project is open source and available under the MIT License.
