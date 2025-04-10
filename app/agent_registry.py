from agents import Agent, ModelSettings, WebSearchTool, Runner, RunResult, function_tool # Changed Result to RunResult
from app.models import ResearchFinding, AnalysisResult, CoordinationDecision
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import os
import functools # Keep for require_safe_path if it were here
import json

# Import specific tools needed for agent configurations
from .tools import (
    rulebook_parser_tool,
    comparison_generator_tool,
    citation_formatter_tool,
    read_file_content,
    write_to_file,
    summarize_text_agent,
    calculate_sum,       # Although not used in default configs, import if potentially used
    format_data,         # Although not used in default configs, import if potentially used
    analyze_text_agent,  # Although not used in default configs, import if potentially used
    generate_report_tool # Although not used in default configs, import if potentially used
)
# Import the decorator if needed by tools defined here (it was moved)
# from .tools import require_safe_path

logger = logging.getLogger(__name__)

# --- Tool Definitions Removed --- (Moved to app/tools.py)
# rulebook_parser_tool, comparison_generator_tool, citation_formatter_tool,
# require_safe_path, read_file_content, write_to_file, simple_summarizer

# --- Define Base Agent Configurations ---
BASE_MODEL = "gpt-4o" # Or load from config
BASE_TEMPERATURE = 0.7

# Instantiate tools that require it (like WebSearchTool)
web_search_tool = WebSearchTool()

# Define configurations using imported tool function objects
AGENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "Coordinator": {
        "instructions": "Analyze the user's request. Determine if it's a simple query or requires a complex research report. Output a CoordinationDecision JSON object. For simple queries, specify 'simple_query' and the 'target_agent_role'. For complex reports, specify 'complex_report' and provide detailed 'plan_generation_instructions' for the Plan Creation Agent, outlining the necessary steps (e.g., Research, Analysis, Drafting, Review) and agent roles.",
        "model": "o3-mini",
        "tools": [],
        "model_settings": ModelSettings(),
        "output_type": CoordinationDecision,
    },
    "Researcher": {
        "instructions": f"You are a research assistant. Find information on the given topic using available tools (WebSearch, RulebookParser, ReadFile). Focus on accuracy and gather specific facts. Output ONLY a JSON list of ResearchFinding objects. Each object must conform to this Pydantic schema: {ResearchFinding.schema_json(indent=2)}. Use the RulebookParser tool for official rulebooks when possible.",
        # Use instantiated and imported tools
        "tools": [web_search_tool, rulebook_parser_tool, read_file_content],
        "model_settings": ModelSettings(temperature=BASE_TEMPERATURE, tool_choice="auto"),
        # "output_type": List[ResearchFinding]
    },
    "AnalysisAgent": {
        "instructions": f"Analyze the provided research findings (JSON list of ResearchFinding). Compare/contrast entities as requested. Identify key differences and similarities. Use the comparison_generator_tool. Output ONLY a JSON object conforming to the AnalysisResult schema: {AnalysisResult.schema_json(indent=2)}.",
        "model": "o3-mini",
        "tools": [comparison_generator_tool],
        "model_settings": ModelSettings(tool_choice="required"),
        # "output_type": AnalysisResult
    },
    "Writer": {
        "instructions": (
            "You are a skilled writer. Compose a report/article/creative piece based on the provided context (ResearchFindings, AnalysisResult, or previous step outputs).\n\n"
            "**File Handling:**\n"
            "1.  **Determine Filename:** Generate a concise, relevant, lowercase filename with an appropriate extension (e.g., 'hawaii_itinerary_draft.txt', 'research_summary.md').\n"
            "2.  **Read Previous Draft (If Revising):** If your task involves revising a document created by a previous step, check the results of dependency steps. If a filename (e.g., 'some_draft.txt') was returned by a dependency, use the `read_file_content` tool with that specific filename to get the existing content.\n"
            "3.  **Write Output:** Use the `write_to_file` tool with your generated filename and `append=False` (to overwrite/create). Ensure the *complete* final text is written.\n"
            "4.  **Tool Result:** The `write_to_file` tool will return a dictionary `{'type': 'file_artifact', 'filename': 'your_filename.ext'}` containing the filename upon success. This dictionary will be passed to subsequent steps.\n\n"
            "Use the `citation_formatter_tool` to add citations for each ResearchFinding used, if applicable."
        ),
        "tools": [read_file_content, write_to_file, citation_formatter_tool],
        "model_settings": ModelSettings(
            temperature=BASE_TEMPERATURE,
            tool_choice="auto",
            max_tokens=15000
        ),
    },
    "Summarizer": {
        "instructions": "You specialize in summarizing text concisely while retaining key information. Adapt the summary length and style based on the request.",
        "model": "o3-mini",
        # Use the imported agent-based summarizer tool
        "tools": [summarize_text_agent],
        "model_settings": ModelSettings(tool_choice="auto"),
    },
    "CodeGenerator": {
        "instructions": (
            "You are a code generation assistant. Write clean, efficient, and well-documented code based on the user's requirements in the specified language.\n\n"
            "**File Handling:**\n"
            "1.  **Determine Filename:** Generate a relevant filename with the correct extension (e.g., 'data_parser.py', 'styles.css').\n"
            "2.  **Write Output:** Use the `write_to_file` tool with your generated filename and `append=False` to save the complete code.\n"
            "3.  **Tool Result:** The `write_to_file` tool will return a dictionary `{'type': 'file_artifact', 'filename': 'your_filename.ext'}` containing the filename upon success."
        ),
        "model": "o3-mini",
        "tools": [write_to_file],
        "model_settings": ModelSettings(tool_choice="auto"),
    },
     "DataAnalyzer": {
        "instructions": "You are a data analysis assistant. Analyze provided data, identify patterns, and generate insights or visualizations based on the request.",
        "model": "o3-mini",
        "tools": [],
        "model_settings": ModelSettings(tool_choice="none"),
    },
    "Reviewer": {
        "instructions": "You are a reviewer. Critically evaluate the provided draft text against the original research findings (JSON list) and analysis (JSON object). Check for accuracy, completeness, clarity, logical flow, and adherence to instructions. Provide constructive feedback.",
        "model": "o3-mini",
        "tools": [],
        "model_settings": ModelSettings(tool_choice="none"),
    },
    "DefaultExecutor": {
        "instructions": "You are a general-purpose execution agent. Follow the instructions provided for the step accurately. Use tools if necessary and available.",
        "model": "o3-mini",
        "tools": [summarize_text_agent], # Example using the agent summarizer
        "model_settings": ModelSettings(tool_choice="auto"),
    },
    "Synthesizer": {
        "instructions": (
            "**Persona:** Act as an expert analyst providing a definitive, comprehensive final report.\n\n"
            "**Core Task:** Generate a single, coherent, well-structured report that directly and fully answers the **Original User Query** provided below. **Your primary output should be the report text itself.**\n\n"
            "**Context:** You will receive the results from all preceding steps of an executed plan. These results might include text summaries, analysis, or *filenames* (e.g., 'final_draft.txt') pointing to detailed content saved by previous steps.\n\n"
            "**Critical Instructions:**\n"
            "- **Access File Content:** If a previous step's result is a filename, use the `read_file_content` tool with that *exact filename* to retrieve its content.\n"
            "- **Integrate Deeply:** You MUST deeply integrate information from ALL relevant preceding steps (including content read from files). **DO NOT** simply list outputs.\n"
            "- **Address the Query Directly:** Explicitly reference the **Original User Query** and ensure your entire response is focused on fulfilling *that specific request*.\n"
            "- **Structure:** Structure the report logically using Markdown.\n"
            "- **Accuracy & Detail:** Ensure the report is accurate, detailed, and easy to understand.\n"
            "- **(Optional) Save Final Report:** You *may* also save your complete final report text to a relevantly named file (e.g., 'final_hawaii_report.md') using `write_to_file` (`append=False`).\n\n"
            "**Input Format:** You will receive the original query and a collection of results (text or filenames) from previous steps.\n\n"
            "--- START OF CONTEXT ---" # Marker
        ),
        "model": "o3-mini",
        "tools": [read_file_content, write_to_file],
        "model_settings": ModelSettings(
            tool_choice="auto",
            max_tokens=15000
        ),
    },
}

# Store instantiated agents to avoid recreation
_agent_cache: Dict[str, Agent] = {}

def get_agent(role: str) -> Optional[Agent]:
    """
    Retrieves or creates an Agent instance based on the specified role.
    Handles caching and uses centralized tool definitions.
    """
    if role in _agent_cache:
        return _agent_cache[role]

    config = AGENT_CONFIGS.get(role)
    if not config:
        logger.warning(f"No configuration found for agent role: {role}")
        # Optionally return a default agent or raise an error
        # Trying to return DefaultExecutor as a fallback
        config = AGENT_CONFIGS.get("DefaultExecutor")
        if not config:
             logger.error(f"DefaultExecutor config also missing. Cannot create agent for role: {role}")
             return None
        logger.info(f"Using DefaultExecutor config as fallback for role: {role}")

    try:
        # Ensure tools listed in config are valid function objects
        agent_tools = config.get('tools', [])
        if not isinstance(agent_tools, list):
            logger.error(f"Invalid tools configuration for role {role}: not a list.")
            agent_tools = []

        # Handle model incompatibility (e.g., WebSearch with o3-mini)
        effective_model = config.get('model', BASE_MODEL)
        final_tools = agent_tools
        if effective_model == "o3-mini":
            original_tool_count = len(final_tools)
            # Filter out WebSearchTool instances specifically
            final_tools = [tool for tool in final_tools if not isinstance(tool, WebSearchTool)]
            if len(final_tools) < original_tool_count:
                logger.warning(f"Removed WebSearchTool as it is incompatible with model '{effective_model}' for role '{role}'.")

        agent = Agent(
            name=f"{role} Agent",
            instructions=config['instructions'],
            model=effective_model,
            tools=final_tools,
            model_settings=config.get('model_settings'),
            output_type=config.get('output_type')
        )
        _agent_cache[role] = agent
        logger.info(f"Created and cached agent for role: {role}")
        return agent
    except Exception as e:
        logger.error(f"Error creating agent for role '{role}': {e}", exc_info=True)
        return None

def get_coordinator_agent() -> Optional[Agent]:
    """Helper function to get the coordinator agent."""
    return get_agent("Coordinator") 