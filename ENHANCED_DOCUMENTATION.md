# Agents_Q Enhanced Documentation

## Overview

Agents_Q is a Python application that leverages OpenAI's Agents SDK and Responses API to create an agentic workflow experience. The system allows users to submit tasks through a chat interface, creates a structured plan, allows for plan refinement, and executes the workflow with various tools.

## Architecture

The application consists of:

1. **Backend**: Python-based backend using Flask and the OpenAI Agents SDK
2. **Frontend**: Interactive web interface with WebSocket support for real-time updates
3. **Core Components**:
   - `enhanced_workflow.py`: Core workflow management with plan creation, refinement, and execution
   - `enhanced_plan_creation_agent.py`: Advanced plan creation with refinement and analysis capabilities
   - `enhanced_workflow_execution_agent.py`: Execution agent with tool integration and dependency tracking
   - `models.py`: Data models for workflow state management
   - Flask routes and WebSocket handlers for real-time communication

## Key Features

### Plan Creation and Refinement
- AI-powered plan creation based on user requests
- Plan refinement based on user feedback
- Plan quality analysis with improvement suggestions

### Workflow Execution
- Step-by-step execution of plans
- Real-time progress updates via WebSockets
- Context tracking between steps for dependency management
- Detailed execution reports

### Tool Integration
- Web search capabilities
- File search (mock implementation)
- Computer operations (mock implementation)
- Custom function tools for calculations and data formatting

### User Interface
- Interactive workflow creation and management
- Real-time progress tracking
- Plan feedback and refinement interface
- Plan analysis visualization

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

## Usage Guide

### Creating a Workflow

1. Navigate to the main workflow interface at `http://localhost:5000`
2. Enter your task description in the input field
3. Click "Create Plan" to generate a structured plan
4. Review the proposed plan

### Refining a Plan

1. After a plan is created, click "Revise Plan"
2. Enter your feedback in the feedback form
3. Submit your feedback to generate a refined plan
4. Repeat until satisfied with the plan

### Analyzing a Plan

1. After a plan is created, click "Analyze Plan"
2. Review the analysis results, including quality metrics and improvement suggestions

### Executing a Workflow

1. Once satisfied with the plan, click "Accept Plan"
2. The system will execute each step in the plan
3. Monitor real-time progress updates
4. Review the final results when execution completes

## Testing

The application includes comprehensive testing tools:

1. **test_workflow.py**: Simulates user interaction with the workflow system
   ```bash
   python test_workflow.py
   ```

2. **test_runner.py**: Manages the server lifecycle during testing
   ```bash
   python test_runner.py
   ```

## API Reference

### WebSocket Events

#### Client to Server

- `create_plan`: Create a new plan from a user request
  ```javascript
  socket.emit('create_plan', {
    message: 'Your task description',
    session_id: 'optional-session-id'
  });
  ```

- `refine_plan`: Refine an existing plan based on feedback
  ```javascript
  socket.emit('refine_plan', {
    session_id: 'your-session-id',
    feedback: 'Your feedback on the plan'
  });
  ```

- `analyze_plan`: Analyze the quality of a plan
  ```javascript
  socket.emit('analyze_plan', {
    session_id: 'your-session-id'
  });
  ```

- `accept_plan`: Accept a plan and begin execution
  ```javascript
  socket.emit('accept_plan', {
    session_id: 'your-session-id'
  });
  ```

- `get_workflow_status`: Get the current status of a workflow
  ```javascript
  socket.emit('get_workflow_status', {
    session_id: 'your-session-id'
  });
  ```

#### Server to Client

- `plan_created`: Emitted when a plan is created
- `plan_accepted`: Emitted when a plan is accepted
- `workflow_update`: Emitted during workflow execution with progress updates
- `workflow_completed`: Emitted when a workflow is completed
- `plan_analysis`: Emitted with plan analysis results
- `error`: Emitted when an error occurs

### REST API

- `GET /`: Main workflow interface
- `GET /chat`: Simple chat interface
- `POST /api/chat`: Send a message to the agent
- `GET /api/workflow/<session_id>`: Get the current state of a workflow

## Customization

### Adding Custom Tools

You can add custom tools by modifying the `_initialize_tools` method in `app/agents/enhanced_workflow_execution_agent.py`:

```python
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

tools['your_tool_name'] = your_custom_tool
```

### Modifying Agent Instructions

You can modify the agent instructions in the respective agent initialization files:

- `app/agents/enhanced_plan_creation_agent.py` for plan creation
- `app/agents/enhanced_workflow_execution_agent.py` for workflow execution

## Troubleshooting

### Common Issues

1. **WebSocket Connection Errors**: Ensure you're using a compatible browser and that no firewall is blocking WebSocket connections.

2. **Plan Creation Timeout**: If plan creation takes too long, try simplifying your request or breaking it into smaller tasks.

3. **Tool Execution Errors**: Check the logs for specific error messages related to tool execution.

### Logging

The application uses Python's logging module. Check the console output for error messages and information.

## Future Enhancements

1. Persistent storage for workflow sessions and results
2. User authentication and multi-user support
3. Integration with real file search and computer tools
4. Advanced visualization of workflow execution
5. Parallel execution of independent workflow steps

## License

This project is open source and available under the MIT License.
