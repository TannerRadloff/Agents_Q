# Agents_Q

A Python application that leverages OpenAI's Agents SDK and Responses API to create an agentic workflow experience.

## Overview

Agents_Q allows users to submit tasks through a chat interface, creates a structured plan, allows for plan refinement, and executes the workflow with various tools. The system provides real-time updates via WebSockets and supports a variety of agent tools for completing complex tasks.

## Key Features

- **AI-powered Plan Creation**: Break down complex tasks into actionable steps
- **Plan Refinement**: Provide feedback to improve generated plans
- **Plan Analysis**: Get quality metrics and improvement suggestions
- **Real-time Workflow Execution**: Execute plans with step-by-step progress updates
- **Tool Integration**: Web search, file operations, and custom function tools
- **Interactive UI**: User-friendly interface with real-time updates

## Quick Start

1. Clone the repository
   ```bash
   git clone https://github.com/TannerRadloff/Agents_Q.git
   cd Agents_Q
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

5. Set up your `.env` file with your OpenAI API key
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

6. Run the application
   ```bash
   python run.py
   ```

7. Open your browser and navigate to `http://localhost:5000`

## Usage

### Workflow Interface

1. Navigate to the main workflow interface at `http://localhost:5000`
2. Enter your task description in the input field
3. The system will create a structured plan for your task
4. Review, refine, or analyze the plan as needed
5. Accept the plan to begin execution
6. Monitor real-time progress and view the final results

### Simple Chat Interface

1. Navigate to the chat interface at `http://localhost:5000/chat`
2. Type your query or task in the chat input field
3. The agent will process your request using the OpenAI Agents SDK
4. The agent can use various tools to complete tasks, including web search

## API Endpoints

### WebSocket Events

- `create_plan`: Create a new plan from a user request
- `refine_plan`: Refine an existing plan based on feedback
- `analyze_plan`: Analyze the quality of a plan
- `accept_plan`: Accept a plan and begin execution
- `get_workflow_status`: Get the current status of a workflow

### REST API

- `GET /`: Main workflow interface
- `GET /chat`: Simple chat interface
- `POST /api/chat`: Send a message to the agent

## Testing

Run the automated test suite:
```bash
python test_runner.py
```

## Documentation

For detailed documentation, see [ENHANCED_DOCUMENTATION.md](ENHANCED_DOCUMENTATION.md)
