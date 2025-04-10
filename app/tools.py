import os
import functools
import logging
import json
from typing import Dict, Any, List # Ensure List is imported

# Imports for specific tools
from agents import function_tool, Agent, Runner, ModelSettings
from flask import current_app # Needed for summarize_text and potentially others
from pydantic import BaseModel # Needed for generate_report

# Import Pydantic models used by tools (adjust path if models are also moved)
from .models import ResearchFinding, AnalysisResult

logger = logging.getLogger(__name__)

# --- Security Decorator --- (Moved from agent_registry.py)
def require_safe_path(func):
    """Decorator to ensure file paths are within the workspace."""
    @functools.wraps(func)
    async def wrapper(filepath: str, *args, **kwargs):
        try:
            # Determine workspace root relative to this file's location
            # Assumes tools.py is in app/ directory
            WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            absolute_filepath = os.path.abspath(os.path.join(WORKSPACE_ROOT, 'instance', filepath)) # Target instance folder by default

            # Check if the path is within the instance folder inside the workspace
            instance_folder_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, 'instance'))
            if os.path.commonpath([instance_folder_path]) != os.path.commonpath([instance_folder_path, absolute_filepath]):
                logger.error(f"Security Error: Attempted file access outside instance folder: {filepath} resolved to {absolute_filepath}")
                return "Error: File access outside allowed workspace/instance folder is forbidden."

            # Ensure directory exists for write operations
            if 'content' in kwargs or (args and isinstance(args[0], str)): # Heuristic for write/append
                dir_path = os.path.dirname(absolute_filepath)
                os.makedirs(dir_path, exist_ok=True)

            return await func(absolute_filepath, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error during safe path check or execution for {filepath}: {e}", exc_info=True)
            return f"Error processing file path or executing function: {e}"
    return wrapper

# --- Tool Definitions --- (Moved from various files)

# Moved from agent_registry.py
@function_tool
async def rulebook_parser_tool(source_identifier: str, query: str) -> List[Dict[str, Any]]:
    """(Placeholder) Parses a rulebook (identified by URL/path) for sections relevant to the query.
    Returns a list of ResearchFinding-like dictionaries.
    Args:
        source_identifier: The URL or path to the rulebook.
        query: The specific information to search for (e.g., 'Non Pro eligibility').
    """
    logger.info(f"[TOOL STUB] Parsing rulebook '{source_identifier}' for query: '{query}'")
    return [
        {"content": f"Placeholder rule about {query} from {source_identifier} - Rule A.1", "source_type": "rulebook", "source_identifier": source_identifier, "page_or_section": "Section A, Rule 1"},
        {"content": f"Placeholder rule about {query} from {source_identifier} - Rule B.3", "source_type": "rulebook", "source_identifier": source_identifier, "page_or_section": "Section B, Rule 3"}
    ]

# Moved from agent_registry.py
@function_tool
async def comparison_generator_tool(findings_json: str) -> Dict[str, Any]:
    """(Placeholder) Compares structured findings (JSON string of List[ResearchFinding]).
    Returns an AnalysisResult-like dictionary.
    Args:
        findings_json: A JSON string representing a list of ResearchFinding objects.
    """
    logger.info("[TOOL STUB] Generating comparison from findings.")
    try:
        # findings = json.loads(findings_json) # Potential parsing
        return {
            "comparison_summary": "Placeholder comparison summary based on findings.",
            "key_differences": ["Difference 1 found", "Difference 2 found"],
            "key_similarities": ["Similarity 1 found"],
            "additional_insights": "Placeholder insight."
        }
    except Exception as e:
        logger.error(f"[TOOL STUB] Error in comparison_generator_tool: {e}")
        return {"comparison_summary": f"Error generating comparison: {e}", "key_differences": [], "key_similarities": []}

# Moved from agent_registry.py
@function_tool
async def citation_formatter_tool(finding_json: str) -> str:
    """(Placeholder) Formats a ResearchFinding (JSON string) into a citation.
    Args:
        finding_json: A JSON string representing a single ResearchFinding object.
    """
    logger.info("[TOOL STUB] Formatting citation.")
    try:
        finding = json.loads(finding_json)
        return f"(Source: {finding.get('source_identifier', 'N/A')}, Section: {finding.get('page_or_section', 'N/A')})"
    except Exception as e:
        logger.error(f"[TOOL STUB] Error in citation_formatter_tool: {e}")
        return f"(Error formatting citation: {e})"

# Moved from agent_registry.py
@function_tool
@require_safe_path
async def read_file_content(filepath: str) -> str:
    """Reads the content of a specified file within the workspace instance folder.
    Args:
        filepath: The relative path to the file within the workspace instance folder.
    """
    # The decorator now handles path resolution and security checks
    logger.info(f"Attempting to read file via tool: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            MAX_SIZE = 1 * 1024 * 1024
            if len(content.encode('utf-8')) > MAX_SIZE:
                logger.warning(f"File content truncated: {filepath}")
                # Truncate based on bytes, approximating characters
                truncated_content = content[:MAX_SIZE] # Simple char slice, might cut mid-multibyte char
                return truncated_content + "\n... [Content Truncated] ..."
            return content
    except FileNotFoundError:
        logger.error(f"File not found by tool: {filepath}")
        return "Error: File not found."
    except Exception as e:
        # Decorator might catch some, but keep specific handling here too
        logger.error(f"Error reading file {filepath} in tool: {e}", exc_info=True)
        return f"Error reading file: {e}"

# Moved from agent_registry.py
@function_tool
@require_safe_path
async def write_to_file(filepath: str, content: str, append: bool) -> Dict[str, str]:
    """Writes or appends content to a specified file within the workspace instance folder.
    You MUST specify the 'append' argument explicitly (True or False).
    Returns a dictionary `{'type': 'file_artifact', 'filename': 'your_filename.ext'}` on success,
    or an error message string on failure.
    Args:
        filepath: The relative path to the file within the workspace instance folder (e.g., 'my_report.txt').
        content: The content to write.
        append: Set to True to append to the file, False to overwrite it.
    """
    logger.info(f"Attempting to write to file via tool: {filepath} (append={append})")
    mode = 'a' if append else 'w'
    try:
        base_filename = os.path.basename(filepath)
        absolute_filepath = filepath # Decorator handles resolving this path
        with open(absolute_filepath, mode, encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Successfully wrote to {absolute_filepath}")
        # Return structured dictionary on success
        return {'type': 'file_artifact', 'filename': base_filename}
    except Exception as e:
        logger.error(f"Error writing to file {filepath} in tool: {e}", exc_info=True)
        # Return error string on failure
        return f"Error writing to file: {e}"

# Moved from agent_registry.py (simple_summarizer) & agents_core.py (summarize_text)
# This version uses an internal agent for better summaries than simple_summarizer
@function_tool
async def summarize_text_agent(text: str) -> str:
    """Summarizes a piece of text concisely and accurately using an internal agent.
    Args:
        text: The text to summarize.
    Returns:
        A summary of the provided text.
    """
    try:
        summarizer_model = current_app.config.get('DEFAULT_MODEL_NAME', 'gpt-4o')
        summarizer_agent = Agent(
            name="Internal Summarizer Agent",
            instructions="Summarize the following text concisely and accurately, capturing the main points.",
            model=summarizer_model,
            tools=[],
            model_settings=ModelSettings(tool_choice="none")
        )
        logger.info(f"Running internal summarizer agent on text (length: {len(text)})...")
        result = await Runner.run(summarizer_agent, text)
        summary = getattr(result, 'final_output', 'Could not generate summary.')
        logger.info("Internal summarizer agent finished.")
        return summary
    except Exception as e:
        logger.error(f"Error in summarize_text_agent tool: {e}", exc_info=True)
        return "Failed to generate summary due to an internal error."

# Moved from enhanced_workflow_execution_agent.py
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

# Moved from enhanced_workflow_execution_agent.py
@function_tool
def format_data(data: str, format_type: str) -> str:
    """Format data into the specified format.
    Args:
        data: The data to format
        format_type: The format to convert to (json, xml, yaml)
    Returns:
        Formatted data as a string
    """
    effective_format_type = format_type.lower() if format_type else "json"
    try:
        if effective_format_type == "json":
            # Attempt to parse/re-serialize for validation, otherwise basic wrap
            try: return json.dumps(json.loads(data)) # If data is valid JSON
            except: return json.dumps({"data": data}) # Basic wrap
        elif effective_format_type == "xml":
            # Basic wrapping, real XML handling is complex
            return f"<data>{data}</data>"
        elif effective_format_type == "yaml":
            # Basic wrapping, real YAML handling needs library (e.g., PyYAML)
            return f"data: {data}"
        else:
            return data # Fallback
    except Exception as e:
        logger.error(f"Error formatting data to {effective_format_type}: {e}")
        return f"Error: Could not format data to {effective_format_type}."

# Moved from enhanced_workflow_execution_agent.py
# Define Pydantic models needed by analyze_text_agent
class TextAnalysisOutput(BaseModel):
    sentiment: str
    key_phrases: List[str]
    summary: str
    word_count: int

@function_tool
async def analyze_text_agent(text: str) -> Dict[str, Any]:
    """Analyze text for sentiment, key phrases, and summary using an internal agent.
    Args:
        text: The text to analyze
    Returns:
        Dictionary with analysis results (sentiment, key_phrases, summary, word_count)
    """
    logger.info(f"Running internal analysis agent on text (length: {len(text)})...")
    try:
        # Assuming parent agent's model is accessible via config or passed context if needed
        analyzer_model = current_app.config.get('DEFAULT_MODEL_NAME', 'gpt-4o')
        analysis_agent = Agent(
            name="Internal Text Analysis Agent",
            instructions=(
                "Analyze the following text. Determine the overall sentiment (positive, negative, neutral), "
                "extract the top 3-5 key phrases, provide a concise one-sentence summary, "
                "and count the total number of words. Output the results as a JSON object matching the TextAnalysisOutput format."
            ),
            model=analyzer_model,
            output_type=TextAnalysisOutput,
            tools=[],
            model_settings=ModelSettings(tool_choice="none")
        )
        result = await Runner.run(analysis_agent, text)
        analysis_output = result.final_output_as(TextAnalysisOutput)
        logger.info("Internal analysis agent finished.")
        return analysis_output.dict()
    except Exception as e:
        logger.error(f"Error in analyze_text_agent tool: {e}", exc_info=True)
        return {
            "error": "Failed to analyze text due to an internal error.",
            "sentiment": "unknown", "key_phrases": [], "summary": "Analysis failed.",
            "word_count": len(text.split())
        }

# Moved from enhanced_workflow_execution_agent.py
# Define Pydantic models needed by generate_report_tool
class ReportSection(BaseModel):
    heading: str
    content: str

@function_tool
def generate_report_tool(title: str, sections_json: str) -> str:
    """Generate a formatted report from a title and sections data.
    Args:
        title: Report title
        sections_json: A JSON string representing a list of section objects, where each object has 'heading' and 'content' keys.
    Returns:
        Formatted report as a string
    """
    report = f"# {title}\n\n"
    try:
        sections = json.loads(sections_json)
        # Validate structure minimally
        if not isinstance(sections, list):
            raise ValueError("sections_json did not decode to a list")

        for section_data in sections:
             # Use Pydantic for validation per section
            section = ReportSection(**section_data)
            report += f"## {section.heading}\n\n{section.content}\n\n"
        return report
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return f"Error: Failed to generate report sections - {e}"

# Dictionary to easily access tools by name
# We use the function objects directly
all_tools = {
    "rulebook_parser": rulebook_parser_tool,
    "comparison_generator": comparison_generator_tool,
    "citation_formatter": citation_formatter_tool,
    "read_file": read_file_content,
    "write_file": write_to_file,
    "summarize": summarize_text_agent, # Use the agent-based summarizer
    "calculate_sum": calculate_sum,
    "format_data": format_data,
    "analyze_text": analyze_text_agent,
    "generate_report": generate_report_tool,
    # Add standard tools if they don't require complex init
    # WebSearchTool needs to be instantiated, handle in registry
} 