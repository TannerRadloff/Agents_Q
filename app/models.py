from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Step(BaseModel):
    title: str
    description: str

class PlanOutput(BaseModel):
    steps: List[Step]
    summary: str

class WorkflowState(BaseModel):
    session_id: str
    plan: Optional[PlanOutput] = None
    accepted_plan: bool = False
    current_step_index: int = 0
    total_steps: int = 0
    steps_results: List[str] = []
    status: str = "pending"
    updates: List[str] = []
    final_result: Optional[str] = None
