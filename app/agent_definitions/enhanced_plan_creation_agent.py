from agents import Agent, ModelSettings, OpenAIResponsesModel, Runner
from app.models import TasksOutput, Task
from typing import List, Dict, Any
import logging
from pydantic import BaseModel, Field

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedPlanCreationAgent:
    """Enhanced plan creation agent with improved capabilities."""
    
    def __init__(self, model_name: str = "o3-mini", temperature: float = 0.5):
        """Initialize the enhanced plan creation agent.
        
        Args:
            model_name: Name of the OpenAI model to use
            temperature: Temperature setting for the model
        """
        self.agent = Agent(
            name="Enhanced Plan Creation Agent",
            instructions=(
                "You are an expert planner. Your goal is to break down a user's complex request into a detailed, "
                "potentially hierarchical plan consisting of high-level tasks and specific, actionable sub-tasks. "
                "The final output MUST be a structured JSON object matching the required `TasksOutput` format.\n\n"
                "**Plan Requirements:**\n"
                "1.  **Hierarchy (Optional but Encouraged):** First, identify the main high-level phases or tasks needed. Then, for any complex high-level task, break it down into smaller, specific sub-tasks. Represent this hierarchy implicitly through descriptive titles (e.g., 'Phase 1: Data Gathering', 'Sub-Task 1.1: Fetch User Reviews', 'Sub-Task 1.2: Scrape Competitor Websites') or explicitly if the output format allows (though the current `Task` format requires a flat list). Aim for a flat list of granular tasks/sub-tasks if hierarchy is difficult to represent.\n"
                "2.  **Granularity:** Each item in the final list (whether a high-level task or a sub-task) must represent a distinct, concrete action. Avoid overly broad steps.\n"
                "3.  **Unique IDs:** Assign a unique, *short*, *descriptive*, *lowercase_snake_case* string ID to EACH task and sub-task (e.g., 'phase1_data_gathering', 'fetch_user_reviews', 'scrape_competitor_sites'). These IDs are crucial for tracking dependencies. Do NOT use UUIDs.\n"
                "4.  **Dependencies:** For EACH task/sub-task, identify ALL other tasks/sub-tasks (by their unique IDs) that MUST be completed before it can begin. List these prerequisite IDs accurately in the `dependencies` field. Ensure dependencies only refer to IDs defined within this plan. If an item has no prerequisites, use an empty list `[]`. Avoid circular dependencies.\n"
                "5.  **Agent Roles:** For EACH task/sub-task, determine the most suitable agent role required to execute it, considering the action description and necessary tools/capabilities. Choose ONE role from the following list: ['Researcher', 'Writer', 'Summarizer', 'CodeGenerator', 'DataAnalyzer', 'Reviewer', 'DefaultExecutor']. Assign the chosen role string to the `agent_role` field.\n"
                "6.  **Logical Order:** Ensure the flat list of tasks/sub-tasks, when considering dependencies, represents a logical progression.\n"
                "7.  **Comprehensive Summary:** Provide a brief summary outlining the overall goal and the high-level approach of the plan.\n\n"
                "**Example Task/Sub-task Format (within the 'tasks' list):**\n"
                "{\n" \
                "  \"id\": \"fetch_user_reviews\",\n" \
                "  \"title\": \"Sub-Task 1.1: Fetch User Reviews\",\n" \
                "  \"description\": \"Retrieve user reviews from internal database and specified external platforms.\",\n" \
                "  \"dependencies\": [],\n" \
                "  \"agent_role\": \"Researcher\"\n" \
                "}\n\n"
                "Given the user request, generate the complete `TasksOutput` JSON object including the `summary` and the flat list of `tasks` (representing all high-level tasks and sub-tasks), ensuring EVERY field (id, title, description, dependencies, agent_role) is correctly populated for each item and adheres strictly to the requirements."
            ),
            model=model_name,
            output_type=TasksOutput,
            model_settings=ModelSettings(
                temperature=temperature,
                tool_choice="none"  # No tool usage for plan creation
            ),
        )
        logger.info(f"Enhanced Plan Creation Agent initialized with model: {model_name}")
    
    async def refine_plan(self, plan: TasksOutput, feedback: str) -> TasksOutput:
        """Refine an existing plan based on user feedback.
        
        Args:
            plan: The original plan (TasksOutput)
            feedback: User feedback for refinement
            
        Returns:
            Refined plan (TasksOutput)
        """
        # Create a string representation of the current plan, including new fields
        current_plan_str = f"Current Plan Summary: {plan.summary}\n\nCurrent Tasks:\n"
        for task in plan.tasks:
            dependencies_str = ", ".join(task.dependencies) if task.dependencies else "None"
            current_plan_str += f"- ID: {task.id}\n"
            current_plan_str += f"  Title: {task.title}\n"
            current_plan_str += f"  Description: {task.description}\n"
            current_plan_str += f"  Dependencies: [{dependencies_str}]\n"
            current_plan_str += f"  Agent Role: {task.agent_role}\n"
        
        # Create a refinement agent with the feedback context
        refinement_agent = Agent(
            name="Plan Refinement Agent",
            instructions=(
                "You are an expert plan refiner. You will be given a current plan (including task/sub-task IDs, descriptions, agent roles, and dependencies) and user feedback. "
                "Your task is to create an improved version of the plan that addresses the feedback. "
                "**Crucially, you MUST output a complete, valid JSON object matching the `TasksOutput` format**, similar to the original plan creation. "
                "This includes re-evaluating and potentially adjusting task/sub-task IDs, descriptions, dependencies, and agent roles for the *entire* plan based on the feedback.\n\n"
                f"User Feedback: {feedback}\n\n"
                f"Current Plan Structure:\n{current_plan_str}\n\n"
                "Generate the complete, refined `TasksOutput` JSON, ensuring all tasks/sub-tasks have unique IDs, correct dependencies (referencing only IDs in the refined plan), and appropriate agent roles selected from ['Researcher', 'Writer', 'Summarizer', 'CodeGenerator', 'DataAnalyzer', 'Reviewer', 'DefaultExecutor']."
            ),
            model=self.agent.model,
            output_type=TasksOutput,
            model_settings=ModelSettings(
                 temperature=self.agent.model_settings.temperature,
                 tool_choice="none"
            ),
        )
        
        # Use an empty string as input since all context is in the instructions
        # Use Runner.run to execute the refinement agent
        result = await Runner.run(refinement_agent, "")
        return result.final_output_as(TasksOutput)
    
    async def generate_plan(self, user_input: str, examples: List[Dict[str, Any]] = None) -> TasksOutput:
        """Create a plan, optionally using example plans as reference.
        
        Args:
            user_input: The user's request
            examples: Optional list of example plans to use as reference
            
        Returns:
            Generated plan (TasksOutput)
        """
        agent_to_run = self.agent # Default agent
        
        if examples:
            # Format examples as string
            examples_str = "Example Plans:\n\n"
            for i, example in enumerate(examples):
                examples_str += f"Example {i+1}:\n"
                examples_str += f"Request: {example.get('request', 'No request provided')}\n"
                examples_str += f"Summary: {example.get('summary', 'No summary provided')}\n"
                examples_str += "Tasks:\n"
                
                tasks = example.get('tasks', [])
                for j, task in enumerate(tasks):
                    examples_str += f"{j+1}. {task.get('title', 'Untitled')}: {task.get('description', 'No description')}\n"
                
                examples_str += "\n"
            
            # Create an agent with examples in the instructions
            agent_to_run = Agent(
                name="Plan Creation with Examples Agent",
                instructions=(
                    "You are an expert at breaking down high-level requests into a series "
                    "of actionable tasks. The final output must be a structured plan.\n\n"
                    "Below are some example plans to guide your thinking:\n\n"
                    f"{examples_str}\n\n"
                    "Using these examples as a guide, create a detailed plan for the user's request. "
                    "Each task should be specific and actionable, following the format of the examples."
                ),
                model=self.agent.model,
                output_type=TasksOutput,
                model_settings=self.agent.model_settings,
            )
        
        # Use Runner.run to execute the appropriate agent
        result = await Runner.run(agent_to_run, user_input)
        plan = result.final_output_as(TasksOutput)
        
        # Programmatically add the final synthesis step
        if plan and plan.tasks:
            all_task_ids = {task.id for task in plan.tasks}
            dependency_ids = set()
            for task in plan.tasks:
                dependency_ids.update(task.dependencies)
            
            # Find terminal tasks (those not listed as dependencies of other tasks)
            terminal_task_ids = [task.id for task in plan.tasks if task.id not in dependency_ids]
            
            # If no clear terminal tasks (e.g., empty plan or circular refs), depend on all
            if not terminal_task_ids:
                logger.warning("Could not determine clear terminal tasks/sub-tasks for synthesis. Depending on all tasks.")
                terminal_task_ids = list(all_task_ids)
            
            synthesis_task = Task(
                id="synthesize_final_report",
                title="Synthesize Final Report",
                description="Review the original user request and the results from previous tasks/sub-tasks to generate a single, coherent, well-formatted final report that directly answers the user's query.",
                dependencies=terminal_task_ids,
                agent_role="Writer"
            )
            plan.tasks.append(synthesis_task)
            logger.info(f"Added final synthesis task depending on terminal tasks/sub-tasks: {terminal_task_ids}")
        
        return plan
    
    async def analyze_plan_quality(self, plan: TasksOutput) -> Dict[str, Any]:
        """Analyze the quality of a plan and provide feedback.
        
        Args:
            plan: The plan to analyze (TasksOutput)
            
        Returns:
            Dictionary with quality metrics and improvement suggestions
        """
        # Create a string representation of the plan including new fields
        plan_str = f"Plan Summary: {plan.summary}\n\nTasks:\n"
        for task in plan.tasks:
            dependencies_str = ", ".join(task.dependencies) if task.dependencies else "None"
            plan_str += f"- ID: {task.id}\n"
            plan_str += f"  Title: {task.title}\n"
            plan_str += f"  Description: {task.description}\n"
            plan_str += f"  Dependencies: [{dependencies_str}]\n"
            plan_str += f"  Agent Role: {task.agent_role}\n\n"
        
        # Define the expected output structure for the analysis
        class PlanAnalysisOutput(BaseModel):
            completeness_score: int = Field(..., ge=1, le=10)
            clarity_score: int = Field(..., ge=1, le=10)
            actionability_score: int = Field(..., ge=1, le=10)
            dependency_score: int = Field(..., ge=1, le=10) # New score for dependencies
            role_assignment_score: int = Field(..., ge=1, le=10) # New score for roles
            feasibility_score: int = Field(..., ge=1, le=10)
            overall_score: float = Field(..., ge=1, le=10)
            suggestions: str

        # Create an analysis agent
        analysis_agent = Agent(
            name="Plan Quality Analysis Agent",
            instructions=(
                "You are an expert plan analyst. You will be given a plan including task/sub-task IDs, descriptions, dependencies, and assigned agent roles. "
                "Your task is to critically analyze the plan's quality based on the following criteria and provide scores (1-10) and suggestions. "
                "Output a JSON object matching the `PlanAnalysisOutput` format.\n\n"
                "**Analysis Criteria:**\n"
                "1.  **Completeness:** Does the plan comprehensively address the original user request? Are any major tasks/sub-tasks missing?\n"
                "2.  **Clarity:** Are the task/sub-task titles and descriptions clear, specific, and unambiguous?\n"
                "3.  **Actionability:** Can each task/sub-task be realistically executed by the assigned agent role based on the description? Is the granularity appropriate?\n"
                "4.  **Dependencies:** Are the dependencies between tasks/sub-tasks correctly identified? Are there missing or incorrect dependencies? Are there circular dependencies?\n"
                "5.  **Role Assignment:** Is the assigned agent role appropriate for each task/sub-task's description?\n"
                "6.  **Feasibility:** Is the overall plan realistic and achievable given typical agent capabilities?\n"
                "7.  **Overall Score:** Calculate an average score based on the above criteria.\n"
                "8.  **Suggestions:** Provide specific, constructive suggestions for improving the plan, referencing task/sub-task IDs where applicable.\n\n"
                f"**Plan to Analyze:**\n{plan_str}\n\n"
                "Provide your analysis as a JSON object adhering strictly to the `PlanAnalysisOutput` format."
            ),
            model=self.agent.model,
            output_type=PlanAnalysisOutput,
            model_settings=ModelSettings(
                 temperature=0.2,
                 tool_choice="none"
             )
        )
        
        # Get the analysis using Runner.run
        analysis_result = await Runner.run(analysis_agent, "") # Input is in instructions
        
        # Return the structured analysis output as a dictionary
        return analysis_result.final_output_as(PlanAnalysisOutput).dict()
