from agents import Agent, ModelSettings, OpenAIResponsesModel
from app.models import PlanOutput

plan_creation_agent = Agent(
    name="Plan Creation Agent",
    instructions=(
        "You are an expert at breaking down high-level requests into a series "
        "of actionable steps. The final output must be a structured plan.\n\n"
        "Given a user's request, create a detailed plan with clear steps that can be executed "
        "by other agents. Each step should be specific and actionable."
    ),
    model="o3-mini",
    output_type=PlanOutput,
    model_settings=ModelSettings(
        temperature=0.5,
        top_p=0.9,
        tool_choice="none"  # No tool usage for plan creation
    ),
)
