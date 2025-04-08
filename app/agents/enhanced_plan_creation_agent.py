from agents import Agent, ModelSettings, OpenAIResponsesModel, Runner
from app.models import PlanOutput, Step
from typing import List, Dict, Any
import logging
from pydantic import BaseModel

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
                "You are an expert at breaking down high-level requests into a series "
                "of actionable steps. The final output must be a structured plan.\n\n"
                "Given a user's request, create a detailed plan with clear steps that can be executed "
                "by other agents. Each step should be specific and actionable.\n\n"
                "Consider the following when creating your plan:\n"
                "1. Break down complex tasks into smaller, manageable steps\n"
                "2. Ensure each step has a clear objective and expected outcome\n"
                "3. Consider dependencies between steps and order them logically\n"
                "4. Include steps for gathering necessary information before taking action\n"
                "5. Include verification steps to ensure quality and accuracy\n"
                "6. Provide a comprehensive summary of the overall plan and its goals\n\n"
                "Your plan should be thorough yet concise, with each step clearly defined."
            ),
            model=model_name,
            output_type=PlanOutput,
            model_settings=ModelSettings(
                tool_choice="none"  # No tool usage for plan creation
            ),
        )
        logger.info(f"Enhanced Plan Creation Agent initialized with model: {model_name}")
    
    async def refine_plan(self, plan: PlanOutput, feedback: str) -> PlanOutput:
        """Refine an existing plan based on user feedback.
        
        Args:
            plan: The original plan
            feedback: User feedback for refinement
            
        Returns:
            Refined plan
        """
        # Create a string representation of the current plan
        current_plan_str = f"Current Plan Summary: {plan.summary}\n\nCurrent Steps:\n"
        for i, step in enumerate(plan.steps):
            current_plan_str += f"{i+1}. {step.title}: {step.description}\n"
        
        # Create a refinement agent with the feedback context
        refinement_agent = Agent(
            name="Plan Refinement Agent",
            instructions=(
                "You are an expert at refining plans based on user feedback. "
                "You will be given a current plan and user feedback. "
                "Your task is to create an improved version of the plan that addresses the feedback.\n\n"
                f"User Feedback: {feedback}\n\n"
                f"{current_plan_str}\n\n"
                "Create an improved plan that addresses the user's feedback while maintaining "
                "the overall structure and goals of the original plan."
            ),
            model=self.agent.model,
            output_type=PlanOutput,
            model_settings=self.agent.model_settings,
        )
        
        # Use an empty string as input since all context is in the instructions
        # Use Runner.run to execute the refinement agent
        result = await Runner.run(refinement_agent, "")
        return result.final_output_as(PlanOutput)
    
    async def create_plan_with_examples(self, user_input: str, examples: List[Dict[str, Any]] = None) -> PlanOutput:
        """Create a plan with example plans as reference.
        
        Args:
            user_input: The user's request
            examples: Optional list of example plans to use as reference
            
        Returns:
            Generated plan
        """
        if not examples:
            # Use Runner.run to execute the main agent
            result = await Runner.run(self.agent, user_input)
            return result.final_output_as(PlanOutput)
        
        # Format examples as string
        examples_str = "Example Plans:\n\n"
        for i, example in enumerate(examples):
            examples_str += f"Example {i+1}:\n"
            examples_str += f"Request: {example.get('request', 'No request provided')}\n"
            examples_str += f"Summary: {example.get('summary', 'No summary provided')}\n"
            examples_str += "Steps:\n"
            
            steps = example.get('steps', [])
            for j, step in enumerate(steps):
                examples_str += f"{j+1}. {step.get('title', 'Untitled')}: {step.get('description', 'No description')}\n"
            
            examples_str += "\n"
        
        # Create an agent with examples in the instructions
        examples_agent = Agent(
            name="Plan Creation with Examples Agent",
            instructions=(
                "You are an expert at breaking down high-level requests into a series "
                "of actionable steps. The final output must be a structured plan.\n\n"
                "Below are some example plans to guide your thinking:\n\n"
                f"{examples_str}\n\n"
                "Using these examples as a guide, create a detailed plan for the user's request. "
                "Each step should be specific and actionable, following the format of the examples."
            ),
            model=self.agent.model,
            output_type=PlanOutput,
            model_settings=self.agent.model_settings,
        )
        
        # Use Runner.run to execute the examples agent
        result = await Runner.run(examples_agent, user_input)
        return result.final_output_as(PlanOutput)
    
    async def analyze_plan_quality(self, plan: PlanOutput) -> Dict[str, Any]:
        """Analyze the quality of a plan and provide feedback.
        
        Args:
            plan: The plan to analyze
            
        Returns:
            Dictionary with quality metrics and improvement suggestions
        """
        # Create a string representation of the plan
        plan_str = f"Plan Summary: {plan.summary}\n\nSteps:\n"
        for i, step in enumerate(plan.steps):
            plan_str += f"{i+1}. {step.title}: {step.description}\n"
        
        # Create an analysis agent
        analysis_agent = Agent(
            name="Plan Quality Analysis Agent",
            instructions=(
                "You are an expert at analyzing the quality of plans. "
                "You will be given a plan and your task is to analyze its quality "
                "and provide feedback for improvement.\n\n"
                "Analyze the following aspects of the plan:\n"
                "1. Completeness: Does the plan cover all necessary steps?\n"
                "2. Clarity: Are the steps clearly defined and understandable?\n"
                "3. Actionability: Can each step be executed without further clarification?\n"
                "4. Logical Flow: Do the steps follow a logical sequence?\n"
                "5. Feasibility: Is the plan realistic and achievable?\n\n"
                "Provide a score from 1-10 for each aspect and suggest improvements."
            ),
            model=self.agent.model,
        )
        
        # Get the analysis using Runner.run
        analysis_result = await Runner.run(analysis_agent, plan_str)
        
        # Parse the analysis result
        return {
            # Assuming the analysis agent returns the analysis as its final_output
            'analysis': analysis_result.final_output, 
            'plan': plan
        }
