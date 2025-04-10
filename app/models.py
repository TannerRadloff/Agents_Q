import uuid
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Task(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    title: str
    description: str
    dependencies: List[str] = Field(default_factory=list) # List of Task IDs this task depends on
    agent_role: str # Role/type of agent needed for this task

class TasksOutput(BaseModel):
    tasks: List[Task] # Renamed from steps to tasks
    summary: str

class WorkflowState(BaseModel):
    session_id: str
    user_query: Optional[str] = None # Added user query field
    plan: Optional[TasksOutput] = None # Updated type hint
    accepted_plan: bool = False
    steps_results: Dict[str, Any] = Field(default_factory=dict) # Store results by Task ID (keeping name for now, consider renaming later if needed)
    step_statuses: Dict[str, str] = Field(default_factory=dict) # Track status per Task ID (keeping name for now, consider renaming later if needed)
    status: str = "pending" # Overall workflow status
    updates: List[str] = Field(default_factory=list)
    final_result: Optional[str] = None

# --- Added Missing Model Definitions ---

class ResearchFinding(BaseModel):
    """Represents a piece of information found during research."""
    content: str
    source_type: str  # e.g., 'web', 'rulebook', 'file'
    source_identifier: str  # e.g., URL, filename, rulebook name
    page_or_section: Optional[str] = None

class AnalysisResult(BaseModel):
    """Represents the outcome of analyzing research findings."""
    comparison_summary: str
    key_differences: List[str] = Field(default_factory=list)
    key_similarities: List[str] = Field(default_factory=list)
    additional_insights: Optional[str] = None

class CoordinationDecision(BaseModel):
    """Represents the coordinator's decision on how to proceed."""
    decision_type: str  # e.g., 'simple_query', 'complex_report'
    target_agent_role: Optional[str] = None  # For simple_query
    plan_generation_instructions: Optional[str] = None  # For complex_report
