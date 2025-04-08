# Comprehensive Guide to OpenAI Agents SDK and Responses API

## Table of Contents

1. [Introduction](#introduction)
   - [What is the OpenAI Agents SDK?](#what-is-the-openai-agents-sdk)
   - [What is the Responses API?](#what-is-the-responses-api)
   - [Relationship Between the Two](#relationship-between-the-two)

2. [Installation and Setup](#installation-and-setup)
   - [Environment Setup](#environment-setup)
   - [Installing the Agents SDK](#installing-the-agents-sdk)
   - [API Key Configuration](#api-key-configuration)
   - [Required Dependencies](#required-dependencies)

3. [Agents SDK Core Concepts](#agents-sdk-core-concepts)
   - [Understanding Agents](#understanding-agents)
   - [Basic Agent Configuration](#basic-agent-configuration)
   - [Instructions and System Prompts](#instructions-and-system-prompts)
   - [Model Configuration](#model-configuration)
   - [Context Management](#context-management)
   - [Output Types](#output-types)

4. [Running Agents](#running-agents)
   - [Using the Runner Class](#using-the-runner-class)
   - [Synchronous vs Asynchronous Execution](#synchronous-vs-asynchronous-execution)
   - [Handling Agent Results](#handling-agent-results)
   - [Streaming Responses](#streaming-responses)
   - [Error Handling](#error-handling)

5. [Tools Integration](#tools-integration)
   - [Hosted Tools](#hosted-tools)
     - [WebSearchTool](#websearchtool)
     - [FileSearchTool](#filesearchtool)
     - [ComputerTool](#computertool)
   - [Function Tools](#function-tools)
   - [Custom Function Tools](#custom-function-tools)
   - [Automatic Argument and Docstring Parsing](#automatic-argument-and-docstring-parsing)
   - [Using Agents as Tools](#using-agents-as-tools)
   - [Error Handling in Function Tools](#error-handling-in-function-tools)

6. [Advanced Features](#advanced-features)
   - [Handoffs Between Agents](#handoffs-between-agents)
   - [Dynamic Instructions](#dynamic-instructions)
   - [Lifecycle Events and Hooks](#lifecycle-events-and-hooks)
   - [Guardrails for Input Validation](#guardrails-for-input-validation)
   - [Cloning and Copying Agents](#cloning-and-copying-agents)
   - [Forcing Tool Use](#forcing-tool-use)
   - [Model Context Protocol (MCP)](#model-context-protocol-mcp)
   - [Tracing and Debugging](#tracing-and-debugging)
   - [Orchestrating Multiple Agents](#orchestrating-multiple-agents)

7. [Responses API](#responses-api)
   - [Core Concepts](#core-concepts)
   - [Differences from Chat Completions API](#differences-from-chat-completions-api)
   - [State Management](#state-management)
   - [Built-in Tools](#built-in-tools)
   - [Integration with Agents SDK](#integration-with-agents-sdk)

8. [Practical Examples](#practical-examples)
   - [Basic Agent Example](#basic-agent-example)
   - [Web Search Example](#web-search-example)
   - [File Search Example](#file-search-example)
   - [Computer Use Example](#computer-use-example)
   - [Multi-Agent Orchestration Example](#multi-agent-orchestration-example)
   - [Agent Handoff Example](#agent-handoff-example)

9. [Best Practices](#best-practices)
   - [Performance Optimization](#performance-optimization)
   - [Security Considerations](#security-considerations)
   - [Cost Management](#cost-management)
   - [Error Handling Strategies](#error-handling-strategies)
   - [Testing and Evaluation](#testing-and-evaluation)

10. [References and Resources](#references-and-resources)

## Introduction

### What is the OpenAI Agents SDK?

The OpenAI Agents SDK is a lightweight, powerful framework for building agentic AI applications. It provides a production-ready upgrade of OpenAI's previous experimentation for agents called Swarm. The Agents SDK is designed with a small set of primitives that, when combined with Python, are powerful enough to express complex relationships between tools and agents, allowing you to build real-world applications without a steep learning curve.

The SDK has two driving design principles:
1. Enough features to be worth using, but few enough primitives to make it quick to learn.
2. Works great out of the box, but you can customize exactly what happens.

The main features of the SDK include:
- **Agent loop**: Built-in agent loop that handles calling tools, sending results to the LLM, and looping until the LLM is done.
- **Python-first**: Use built-in language features to orchestrate and chain agents, rather than needing to learn new abstractions.
- **Handoffs**: A powerful feature to coordinate and delegate between multiple agents.
- **Guardrails**: Run input validations and checks in parallel to your agents, breaking early if the checks fail.
- **Function tools**: Turn any Python function into a tool, with automatic schema generation and Pydantic-powered validation.
- **Tracing**: Built-in tracing that lets you visualize, debug and monitor your workflows, as well as use the OpenAI suite of evaluation, fine-tuning and distillation tools.

### What is the Responses API?

The Responses API is a new API primitive from OpenAI that combines the best of both the Chat Completions and Assistants APIs. It's designed to be simpler to use and includes built-in tools provided by OpenAI that execute tool calls and add results automatically to the conversation context.

The Responses API is a faster, more flexible, and easier way to create agentic experiences. It combines the simplicity of Chat Completions with the tool use and state management capabilities of the Assistants API. The Responses API supports new built-in tools like web search, file search, and computer use.

### Relationship Between the Two

The OpenAI Agents SDK and Responses API are complementary technologies. The Agents SDK comes with out-of-the-box support for OpenAI models in two flavors:

1. **Recommended**: the `OpenAIResponsesModel`, which calls OpenAI APIs using the new Responses API.
2. The `OpenAIChatCompletionsModel`, which calls OpenAI APIs using the Chat Completions API.

While the SDK supports both model shapes, OpenAI recommends using the `OpenAIResponsesModel` (which uses the Responses API) as it provides more capabilities and is the future direction of OpenAI's APIs. The Responses API is the foundation upon which the Agents SDK builds its functionality, providing the underlying model capabilities that the SDK orchestrates.

## Installation and Setup

### Environment Setup

Before installing the Agents SDK, it's recommended to set up a Python virtual environment to manage dependencies cleanly. Here's how to create a project and virtual environment:

```bash
# Create a project directory
mkdir my_project
cd my_project

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
# .venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Installing the Agents SDK

Once your virtual environment is activated, you can install the Agents SDK using pip:

```bash
pip install openai-agents
```

For voice support, you can install with the optional `voice` group:

```bash
pip install 'openai-agents[voice]'
```

### API Key Configuration

To use the Agents SDK, you need to set up an OpenAI API key. You can do this by setting the `OPENAI_API_KEY` environment variable:

```bash
# On macOS/Linux
export OPENAI_API_KEY=sk-...

# On Windows (Command Prompt)
set OPENAI_API_KEY=sk-...

# On Windows (PowerShell)
$env:OPENAI_API_KEY="sk-..."
```

If you don't have an API key, you'll need to create one from the OpenAI platform.

### Required Dependencies

The Agents SDK has several dependencies that are automatically installed when you install the package:

- **openai**: The official OpenAI Python client
- **pydantic**: For data validation and settings management
- **griffe**: For parsing docstrings
- **typing-extensions**: For advanced type hints

For tracing and visualization, additional dependencies might be required, which can be installed as needed.

## Agents SDK Core Concepts

### Understanding Agents

Agents are the core building block in your applications. An agent is a large language model (LLM), configured with instructions and tools. In the Agents SDK, agents are represented by the `Agent` class.

Agents can:
- Process user inputs
- Use tools to accomplish tasks
- Delegate to other agents via handoffs
- Generate structured or unstructured outputs

### Basic Agent Configuration

The most common properties of an agent you'll configure are:

- `instructions`: Also known as a developer message or system prompt.
- `model`: Which LLM to use, and optional `model_settings` to configure model tuning parameters like temperature, top_p, etc.
- `tools`: Tools that the agent can use to achieve its tasks.

Here's a basic example of creating an agent:

```python
from agents import Agent, ModelSettings, function_tool

@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Haiku agent",
    instructions="Always respond in haiku form",
    model="o3-mini",
    tools=[get_weather],
)
```

### Instructions and System Prompts

Instructions (also known as system prompts) define the behavior, personality, and capabilities of your agent. They are provided as a string when creating the agent:

```python
agent = Agent(
    name="Math Tutor",
    instructions="You provide help with math problems. Explain your reasoning at each step and include examples",
)
```

You can also provide dynamic instructions via a function:

```python
def dynamic_instructions(context: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
    return f"The user's name is {context.context.name}. Help them with their questions."

agent = Agent[UserContext](
    name="Triage agent",
    instructions=dynamic_instructions,
)
```

### Model Configuration

You can specify which model to use for your agent in several ways:

1. Passing the name of an OpenAI model:
   ```python
   agent = Agent(
       name="Assistant",
       model="o3-mini",
   )
   ```

2. Passing a model instance:
   ```python
   from agents import OpenAIChatCompletionsModel, AsyncOpenAI

   agent = Agent(
       name="Assistant",
       model=OpenAIChatCompletionsModel(
           model="gpt-4o",
           openai_client=AsyncOpenAI()
       ),
   )
   ```

3. Using model settings to configure parameters:
   ```python
   from agents import Agent, ModelSettings

   agent = Agent(
       name="Assistant",
       model="o3-mini",
       model_settings=ModelSettings(
           temperature=0.7,
           top_p=0.9,
           tool_choice="auto"
       ),
   )
   ```

### Context Management

Agents are generic on their `context` type. Context is a dependency-injection tool: it's an object you create and pass to `Runner.run()`, that is passed to every agent, tool, handoff etc., and it serves as a grab bag of dependencies and state for the agent run.

```python
from dataclasses import dataclass
from typing import List

@dataclass
class UserContext:
    uid: str
    is_pro_user: bool
    
    async def fetch_purchases(self) -> List[Purchase]:
        # Implementation
        return []

agent = Agent[UserContext](
    name="Assistant",
    instructions="You are a helpful assistant",
)

# When running the agent
context = UserContext(uid="123", is_pro_user=True)
result = await Runner.run(agent, "Help me with my question", context=context)
```

### Output Types

By default, agents produce plain text (i.e., `str`) outputs. If you want the agent to produce a particular type of output, you can use the `output_type` parameter. A common choice is to use Pydantic objects:

```python
from pydantic import BaseModel
from agents import Agent

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

agent = Agent(
    name="Calendar extractor",
    instructions="Extract calendar events from text",
    output_type=CalendarEvent,
)
```

When you pass an `output_type`, the model will use structured outputs instead of regular plain text responses.

## Running Agents

### Using the Runner Class

The `Runner` class is responsible for executing agents. It handles the agent loop, tool calls, and handoffs. There are two main ways to run an agent:

1. **Asynchronous execution** (recommended for most applications):
   ```python
   from agents import Agent, Runner
   import asyncio

   async def main():
       agent = Agent(name="Assistant", instructions="You are a helpful assistant")
       result = await Runner.run(agent, "Write a haiku about recursion in programming.")
       print(result.final_output)

   if __name__ == "__main__":
       asyncio.run(main())
   ```

2. **Synchronous execution** (simpler but blocks the main thread):
   ```python
   from agents import Agent, Runner

   agent = Agent(name="Assistant", instructions="You are a helpful assistant")
   result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
   print(result.final_output)
   ```

### Synchronous vs Asynchronous Execution

The Agents SDK supports both synchronous and asynchronous execution:

- **Asynchronous execution** (`Runner.run`): This is the recommended approach for most applications, especially those that need to handle multiple requests concurrently or integrate with other asynchronous code.

- **Synchronous execution** (`Runner.run_sync`): This is a convenience method for simple scripts or when you don't need asynchronous execution. It blocks the main thread until the agent completes.

### Handling Agent Results

When you run an agent, you get a `Result` object that contains information about the agent run:

```python
result = await Runner.run(agent, "What's the weather in Tokyo?")

# Get the final output as a string
print(result.final_output)

# If the agent has an output_type, get the structured output
if agent.output_type:
    structured_output = result.final_output_as(agent.output_type)
    print(structured_output)

# Access the full conversation history
for message in result.messages:
    print(f"{message.role}: {message.content}")

# Check if tools were used
for message in result.messages:
    if message.tool_calls:
        for tool_call in message.tool_calls:
            print(f"Tool called: {tool_call.name}")
            print(f"Arguments: {tool_call.arguments}")
```

### Streaming Responses

The Agents SDK supports streaming responses, which allows you to get partial results as they become available:

```python
from agents import Agent, Runner
import asyncio

async def main():
    agent = Agent(name="Assistant", instructions="You are a helpful assistant")
    
    async for event in Runner.stream(agent, "Write a story about a robot."):
        if event.type == "content_block_delta":
            print(event.delta, end="", flush=True)
        elif event.type == "tool_call":
            print(f"\nTool call: {event.tool_call.name}")
        elif event.type == "tool_result":
            print(f"\nTool result: {event.result}")
        elif event.type == "handoff":
            print(f"\nHandoff to: {event.handoff_to.name}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Handling

When running agents, various errors can occur, such as API errors, tool execution errors, or validation errors. It's important to handle these errors appropriately:

```python
from agents import Agent, Runner
import asyncio

async def main():
    agent = Agent(name="Assistant", instructions="You are a helpful assistant")
    
    try:
        result = await Runner.run(agent, "What's the weather in Tokyo?")
        print(result.final_output)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Tools Integration

### Hosted Tools

OpenAI offers a few built-in tools when using the `OpenAIResponsesModel`:

#### WebSearchTool

The `WebSearchTool` lets an agent search the web:

```python
from agents import Agent, Runner, WebSearchTool

agent = Agent(
    name="Research Assistant",
    instructions="You help users find information on the web.",
    tools=[WebSearchTool()],
)

async def main():
    result = await Runner.run(agent, "What are the latest developments in quantum computing?")
    print(result.final_output)
```

#### FileSearchTool

The `FileSearchTool` allows retrieving information from your OpenAI Vector Stores:

```python
from agents import Agent, Runner, FileSearchTool

agent = Agent(
    name="Document Assistant",
    instructions="You help users find information in their documents.",
    tools=[
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=["VECTOR_STORE_ID"],
        ),
    ],
)

async def main():
    result = await Runner.run(agent, "Find information about project XYZ in my documents.")
    print(result.final_output)
```

#### ComputerTool

The `ComputerTool` allows automating computer use tasks:

```python
from agents import Agent, Runner, ComputerTool

agent = Agent(
    name="Computer Assistant",
    instructions="You help users automate tasks on their computer.",
    tools=[ComputerTool()],
)

async def main():
    result = await Runner.run(agent, "Help me create a new folder on my desktop.")
    print(result.final_output)
```

### Function Tools

You can use any Python function as a tool. The Agents SDK will set up the tool automatically:

```python
from agents import Agent, Runner, function_tool
import asyncio

@function_tool
def get_weather(city: str) -> str:
    """Fetch the weather for a given location.
    
    Args:
        city: The city to fetch the weather for.
    """
    # In a real application, you would call a weather API here
    return f"The weather in {city} is sunny."

agent = Agent(
    name="Weather Assistant",
    instructions="You help users check the weather.",
    tools=[get_weather],
)

async def main():
    result = await Runner.run(agent, "What's the weather in Tokyo?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Function Tools

Sometimes, you don't want to use a Python function as a tool. You can directly create a `FunctionTool` if you prefer:

```python
from agents import Agent, Runner, FunctionTool, RunContextWrapper
import asyncio
import json

async def on_invoke_tool(ctx: RunContextWrapper, arguments_json: str) -> str:
    """Custom tool implementation."""
    arguments = json.loads(arguments_json)
    city = arguments.get("city", "")
    # In a real application, you would call a weather API here
    return f"The weather in {city} is sunny."

weather_tool = FunctionTool(
    name="get_weather",
    description="Fetch the weather for a given location.",
    params_json_schema={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city to fetch the weather for."
            }
        },
        "required": ["city"]
    },
    on_invoke_tool=on_invoke_tool,
)

agent = Agent(
    name="Weather Assistant",
    instructions="You help users check the weather.",
    tools=[weather_tool],
)

async def main():
    result = await Runner.run(agent, "What's the weather in Tokyo?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Automatic Argument and Docstring Parsing

The Agents SDK automatically parses function signatures and docstrings to create tool schemas:

```python
from typing_extensions import TypedDict
from agents import Agent, function_tool

class Location(TypedDict):
    lat: float
    long: float

@function_tool
async def fetch_weather(location: Location) -> str:
    """Fetch the weather for a given location.
    
    Args:
        location: The location to fetch the weather for.
    """
    # In a real application, you would call a weather API here
    return "sunny"

agent = Agent(
    name="Weather Assistant",
    instructions="You help users check the weather.",
    tools=[fetch_weather],
)
```

The SDK uses Python's `inspect` module to extract the function signature, along with `griffe` to parse docstrings and `pydantic` for schema creation.

### Using Agents as Tools

You can use an agent as a tool, allowing agents to call other agents without handing off to them:

```python
from agents import Agent, Runner, agent_as_tool
import asyncio

calculator_agent = Agent(
    name="Calculator",
    instructions="You are a calculator that can perform mathematical operations.",
)

@agent_as_tool(calculator_agent)
async def calculate(expression: str) -> str:
    """Calculate the result of a mathematical expression.
    
    Args:
        expression: The mathematical expression to calculate.
    """
    pass  # The implementation is handled by the agent

assistant_agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    tools=[calculate],
)

async def main():
    result = await Runner.run(assistant_agent, "What is 123 * 456?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Handling in Function Tools

When a tool encounters an error, you can handle it gracefully:

```python
from agents import Agent, Runner, function_tool
import asyncio

@function_tool
def divide(a: float, b: float) -> float:
    """Divide two numbers.
    
    Args:
        a: The numerator.
        b: The denominator.
    """
    try:
        return a / b
    except ZeroDivisionError:
        return "Error: Cannot divide by zero."

agent = Agent(
    name="Calculator",
    instructions="You are a calculator that can perform mathematical operations.",
    tools=[divide],
)

async def main():
    result = await Runner.run(agent, "What is 10 divided by 0?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Features

### Handoffs Between Agents

Handoffs are sub-agents that the agent can delegate to. You provide a list of handoffs, and the agent can choose to delegate to them if relevant:

```python
from agents import Agent, Runner
import asyncio

spanish_agent = Agent(
    name="Spanish agent",
    handoff_description="Specialist agent for Spanish language queries",
    instructions="You only speak Spanish.",
)

english_agent = Agent(
    name="English agent",
    handoff_description="Specialist agent for English language queries",
    instructions="You only speak English",
)

triage_agent = Agent(
    name="Triage agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[spanish_agent, english_agent],
)

async def main():
    result = await Runner.run(triage_agent, "Hola, ¿cómo estás?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Dynamic Instructions

You can provide dynamic instructions via a function that receives the agent and context:

```python
from agents import Agent, Runner, RunContextWrapper
from typing import Any
import asyncio

def dynamic_instructions(context: RunContextWrapper[Any], agent: Agent[Any]) -> str:
    user_name = context.context.get("user_name", "User")
    return f"The user's name is {user_name}. Help them with their questions."

agent = Agent(
    name="Dynamic Assistant",
    instructions=dynamic_instructions,
)

async def main():
    context = {"user_name": "Alice"}
    result = await Runner.run(agent, "Tell me about yourself.", context=context)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Lifecycle Events and Hooks

Sometimes, you want to observe the lifecycle of an agent. You can hook into the agent lifecycle with the `hooks` property:

```python
from agents import Agent, Runner, AgentHooks, RunContextWrapper
import asyncio

class MyAgentHooks(AgentHooks):
    async def before_agent_run(self, ctx: RunContextWrapper, agent: Agent, input_data: str) -> None:
        print(f"Agent {agent.name} is about to run with input: {input_data}")
    
    async def after_agent_run(self, ctx: RunContextWrapper, agent: Agent, result: Any) -> None:
        print(f"Agent {agent.name} has completed with result: {result.final_output}")

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    hooks=MyAgentHooks(),
)

async def main():
    result = await Runner.run(agent, "Tell me a joke.")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Guardrails for Input Validation

Guardrails allow you to run checks/validations on user input, in parallel to the agent running:

```python
from agents import Agent, Runner, GuardrailFunctionOutput, InputGuardrail
from pydantic import BaseModel
import asyncio

class HomeworkOutput(BaseModel):
    is_homework: bool
    reasoning: str

guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking about homework.",
    output_type=HomeworkOutput,
)

async def homework_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(HomeworkOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_homework,
    )

main_agent = Agent(
    name="Homework Helper",
    instructions="You help students with their homework.",
    input_guardrails=[InputGuardrail(homework_guardrail)],
)

async def main():
    result = await Runner.run(main_agent, "Can you do my homework for me?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Cloning and Copying Agents

By using the `clone()` method on an agent, you can duplicate an Agent, and optionally change any properties you like:

```python
from agents import Agent
import asyncio

pirate_agent = Agent(
    name="Pirate",
    instructions="Write like a pirate",
    model="o3-mini",
)

robot_agent = pirate_agent.clone(
    name="Robot",
    instructions="Write like a robot",
)

async def main():
    # Use both agents...
    pass
```

### Forcing Tool Use

Supplying a list of tools doesn't always mean the LLM will use a tool. You can force tool use by setting `ModelSettings.tool_choice`:

```python
from agents import Agent, ModelSettings, function_tool
import asyncio

@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny."

agent = Agent(
    name="Weather Assistant",
    instructions="You help users check the weather.",
    tools=[get_weather],
    model_settings=ModelSettings(
        tool_choice="required",  # Forces the LLM to use a tool
    ),
)

async def main():
    result = await Runner.run(agent, "What's the weather in Tokyo?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

Valid values for `tool_choice` are:
1. `"auto"`: Allows the LLM to decide whether or not to use a tool.
2. `"required"`: Requires the LLM to use a tool (but it can intelligently decide which tool).
3. `"none"`: Requires the LLM to not use a tool.
4. A specific string (e.g., `"get_weather"`): Requires the LLM to use that specific tool.

### Model Context Protocol (MCP)

The Model Context Protocol (MCP) is a standard for interacting with LLMs. The Agents SDK supports MCP, allowing you to use different LLM providers:

```python
from agents import Agent, Runner, set_default_openai_client
from openai import AsyncOpenAI
import asyncio

# Use a different OpenAI-compatible API endpoint
client = AsyncOpenAI(
    base_url="https://api.alternative-provider.com/v1",
    api_key="your-api-key",
)
set_default_openai_client(client)

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    model="alternative-model",
)

async def main():
    result = await Runner.run(agent, "Tell me a joke.")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Tracing and Debugging

The Agents SDK includes built-in tracing, collecting a comprehensive record of events during an agent run:

```python
from agents import Agent, Runner, set_tracing_disabled, set_tracing_export_api_key
import asyncio

# Disable tracing if needed
# set_tracing_disabled(True)

# Set a specific API key for tracing
# set_tracing_export_api_key("your-openai-api-key")

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
)

async def main():
    result = await Runner.run(agent, "Tell me a joke.")
    print(result.final_output)
    
    # Access trace information
    print(f"Trace ID: {result.trace_id}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Orchestrating Multiple Agents

You can orchestrate multiple agents to work together on complex tasks:

```python
from agents import Agent, Runner
import asyncio

research_agent = Agent(
    name="Research Agent",
    instructions="You research information on topics.",
)

summarization_agent = Agent(
    name="Summarization Agent",
    instructions="You summarize information concisely.",
)

async def main():
    # First, use the research agent to gather information
    research_result = await Runner.run(research_agent, "Find information about quantum computing.")
    
    # Then, use the summarization agent to summarize the research
    summary_prompt = f"Summarize this information: {research_result.final_output}"
    summary_result = await Runner.run(summarization_agent, summary_prompt)
    
    print(summary_result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Responses API

### Core Concepts

The Responses API is a new API primitive from OpenAI that combines the best of both the Chat Completions and Assistants APIs. It's designed to be simpler to use and includes built-in tools provided by OpenAI that execute tool calls and add results automatically to the conversation context.

Key features of the Responses API include:

1. **Server-side state management**: The API can maintain conversation state on the server, eliminating the need to send the full conversation history with each request.
2. **Built-in tools**: The API includes built-in tools like web search, file search, and computer use.
3. **Simplified workflow**: The API simplifies workflows involving tool use, code execution, and state management.

### Differences from Chat Completions API

The Responses API differs from the Chat Completions API in several ways:

1. **State management**: The Responses API can manage conversation state on the server, while the Chat Completions API requires you to maintain your own records of the current conversation.

2. **Tool integration**: The Responses API has built-in tools and handles tool execution automatically, while the Chat Completions API requires you to implement tool execution yourself.

3. **API format**: The Responses API continues to support the list of messages format from Chat Completions, but also adds new options like `"store": true` and `"previous_response_id": response_id` for state management.

4. **Form encoding support**: The Responses API supports HTML form encoding in addition to JSON:
   ```bash
   curl https://api.openai.com/v1/responses \
     -u :$OPENAI_API_KEY \
     -d model="gpt-4o" \
     -d input="What is the capital of France?"
   ```

### State Management

One of the most important features of the Responses API is its ability to manage conversation state on the server:

```python
import openai

# First request - store the conversation state
response = openai.responses.create(
    model="gpt-4o",
    input="What is the capital of France?",
    store=True
)
response_id = response.id

# Second request - continue the conversation
response = openai.responses.create(
    model="gpt-4o",
    input="What's the population there?",
    previous_response_id=response_id
)
```

This eliminates the need to send the full conversation history with each request, which can be especially beneficial when dealing with long conversations or attachments like images.

### Built-in Tools

The Responses API includes several built-in tools:

1. **Web Search**: Delivers accurate and clearly-cited answers from the web.
   ```python
   import openai

   response = openai.responses.create(
       model="gpt-4o",
       input="What are the latest developments in quantum computing?",
       tools=[{"type": "web_search_preview"}]
   )
   ```

2. **File Search**: Provides integration with OpenAI's vector store for RAG (Retrieval-Augmented Generation).
   ```python
   import openai

   response = openai.responses.create(
       model="gpt-4o",
       input="Find information about project XYZ in my documents.",
       tools=[{"type": "file_search", "vector_store_ids": ["VECTOR_STORE_ID"]}]
   )
   ```

3. **Computer Use**: Allows control of computers or virtual machines.
   ```python
   import openai

   response = openai.responses.create(
       model="gpt-4o",
       input="Help me create a new folder on my desktop.",
       tools=[{
           "type": "computer_use_preview",
           "display_width": 1024,
           "display_height": 768,
           "environment": "browser"
       }]
   )
   ```

### Integration with Agents SDK

The Agents SDK integrates with the Responses API through the `OpenAIResponsesModel` class:

```python
from agents import Agent, Runner, OpenAIResponsesModel
import asyncio

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    model=OpenAIResponsesModel(model="gpt-4o"),
)

async def main():
    result = await Runner.run(agent, "Tell me a joke.")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

The Agents SDK recommends using the `OpenAIResponsesModel` over the `OpenAIChatCompletionsModel` as it provides more capabilities and is the future direction of OpenAI's APIs.

## Practical Examples

### Basic Agent Example

Here's a basic example of creating and running an agent:

```python
from agents import Agent, Runner
import asyncio

async def main():
    agent = Agent(
        name="Assistant",
        instructions="You only respond in haikus.",
    )
    
    result = await Runner.run(agent, "Tell me about recursion in programming.")
    print(result.final_output)
    # Function calls itself,
    # Looping in smaller pieces,
    # Endless by design.

if __name__ == "__main__":
    asyncio.run(main())
```

### Web Search Example

This example demonstrates how to use the `WebSearchTool` to search the web:

```python
from agents import Agent, Runner, WebSearchTool
import asyncio

async def main():
    agent = Agent(
        name="Research Assistant",
        instructions="You help users find information on the web.",
        tools=[WebSearchTool()],
    )
    
    result = await Runner.run(agent, "What are the latest developments in quantum computing?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### File Search Example

This example shows how to use the `FileSearchTool` to search through documents:

```python
from agents import Agent, Runner, FileSearchTool
import asyncio

async def main():
    agent = Agent(
        name="Document Assistant",
        instructions="You help users find information in their documents.",
        tools=[
            FileSearchTool(
                max_num_results=3,
                vector_store_ids=["VECTOR_STORE_ID"],
            ),
        ],
    )
    
    result = await Runner.run(agent, "Find information about project XYZ in my documents.")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Computer Use Example

This example demonstrates how to use the `ComputerTool` to automate computer tasks:

```python
from agents import Agent, Runner, ComputerTool
import asyncio

async def main():
    agent = Agent(
        name="Computer Assistant",
        instructions="You help users automate tasks on their computer.",
        tools=[ComputerTool()],
    )
    
    result = await Runner.run(agent, "Help me create a new folder on my desktop.")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Multi-Agent Orchestration Example

This example shows how to orchestrate multiple agents to work together:

```python
from agents import Agent, Runner
import asyncio

async def main():
    research_agent = Agent(
        name="Research Agent",
        instructions="You research information on topics.",
    )
    
    summarization_agent = Agent(
        name="Summarization Agent",
        instructions="You summarize information concisely.",
    )
    
    # First, use the research agent to gather information
    research_result = await Runner.run(research_agent, "Find information about quantum computing.")
    
    # Then, use the summarization agent to summarize the research
    summary_prompt = f"Summarize this information: {research_result.final_output}"
    summary_result = await Runner.run(summarization_agent, summary_prompt)
    
    print(summary_result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Agent Handoff Example

This example demonstrates how to use handoffs between agents:

```python
from agents import Agent, Runner
import asyncio

async def main():
    spanish_agent = Agent(
        name="Spanish agent",
        handoff_description="Specialist agent for Spanish language queries",
        instructions="You only speak Spanish.",
    )
    
    english_agent = Agent(
        name="English agent",
        handoff_description="Specialist agent for English language queries",
        instructions="You only speak English",
    )
    
    triage_agent = Agent(
        name="Triage agent",
        instructions="Handoff to the appropriate agent based on the language of the request.",
        handoffs=[spanish_agent, english_agent],
    )
    
    result = await Runner.run(triage_agent, "Hola, ¿cómo estás?")
    print(result.final_output)
    # Expected output in Spanish

if __name__ == "__main__":
    asyncio.run(main())
```

## Best Practices

### Performance Optimization

To optimize the performance of your agents:

1. **Use the right model**: Choose the appropriate model for your task. Smaller models like `o3-mini` are faster and cheaper for simpler tasks, while larger models like `gpt-4o` are better for complex tasks.

2. **Minimize token usage**: Be concise in your instructions and prompts to reduce token usage.

3. **Use caching**: Implement caching for tool results to avoid redundant API calls.

4. **Batch processing**: When processing multiple items, consider batching them to reduce the number of API calls.

5. **Asynchronous execution**: Use asynchronous execution (`Runner.run`) instead of synchronous execution (`Runner.run_sync`) for better performance in concurrent scenarios.

### Security Considerations

When building with the Agents SDK and Responses API, consider these security best practices:

1. **API key management**: Store your API keys securely and never expose them in client-side code.

2. **Input validation**: Validate user inputs before passing them to agents to prevent prompt injection attacks.

3. **Output sanitization**: Sanitize agent outputs before displaying them to users to prevent XSS attacks.

4. **Rate limiting**: Implement rate limiting to prevent abuse of your application.

5. **Least privilege**: When using tools, follow the principle of least privilege and only grant the necessary permissions.

### Cost Management

To manage costs effectively:

1. **Monitor usage**: Keep track of your API usage to avoid unexpected bills.

2. **Choose appropriate models**: Use smaller models for simpler tasks to reduce costs.

3. **Optimize prompts**: Write efficient prompts to minimize token usage.

4. **Implement caching**: Cache responses to avoid redundant API calls.

5. **Set usage limits**: Set usage limits in your OpenAI account to prevent unexpected costs.

### Error Handling Strategies

Implement robust error handling in your applications:

1. **Graceful degradation**: Design your application to gracefully handle API errors and continue functioning.

2. **Retry logic**: Implement retry logic with exponential backoff for transient errors.

3. **Fallback mechanisms**: Have fallback mechanisms in place for when the primary approach fails.

4. **Comprehensive error messages**: Provide clear error messages to users when something goes wrong.

5. **Logging and monitoring**: Implement logging and monitoring to detect and diagnose errors.

### Testing and Evaluation

To ensure the quality of your agent-based applications:

1. **Unit testing**: Write unit tests for your tools and agent configurations.

2. **Integration testing**: Test the integration between agents and tools.

3. **End-to-end testing**: Test the entire workflow from user input to final output.

4. **Evaluation metrics**: Define metrics to evaluate the performance of your agents, such as accuracy, relevance, and user satisfaction.

5. **User feedback**: Collect and incorporate user feedback to improve your agents over time.

## References and Resources

- [OpenAI Agents SDK Documentation](https://openai.github.io/openai-agents-python/)
- [OpenAI Agents SDK GitHub Repository](https://github.com/openai/openai-agents-python)
- [OpenAI Responses API Documentation](https://platform.openai.com/docs/api-reference/responses)
- [OpenAI Developer Community](https://community.openai.com/)
- [Simon Willison's Blog: Responses vs. Chat Completions](https://simonwillison.net/2025/Mar/11/responses-vs-chat-completions/)
- [OpenAI Blog: New tools for building agents](https://community.openai.com/t/new-tools-for-building-agents-responses-api-web-search-file-search-computer-use-and-agents-sdk/1140896)
