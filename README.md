# Agents_Q

A Python application using OpenAI's Agents SDK and Responses API to create an agentic experience where users can submit tasks through a chat interface.

## Features

- Python backend using the OpenAI Agents SDK
- Integration of available hosted tools from the Agents SDK
- Simple frontend interface with chat functionality
- Ability for users to submit tasks and have agents respond and complete them

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

1. Type your query or task in the chat input field
2. Press Enter or click Send
3. The agent will process your request using the OpenAI Agents SDK
4. The agent can use various tools to complete tasks, including web search

## API Endpoints

### POST /api/chat

Send a message to the agent:

```json
{
  "message": "Your message here",
  "instructions": "Optional custom instructions",
  "tools": ["optional", "list", "of", "tool", "names"],
  "model": "o3-mini"
}
```

## Documentation

For detailed documentation, see [DOCUMENTATION.md](DOCUMENTATION.md)
