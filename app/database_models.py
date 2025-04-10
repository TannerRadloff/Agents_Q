from .extensions import db # We will create extensions.py next
import json
from .models import TasksOutput # Import Pydantic model for type hinting
from typing import Any

class WorkflowSessionDB(db.Model):
    id = db.Column(db.String, primary_key=True) # Corresponds to session_id
    user_query = db.Column(db.Text, nullable=True) # Added user query column
    plan_json = db.Column(db.Text, nullable=True) # Store TasksOutput as JSON string
    accepted_plan = db.Column(db.Boolean, default=False, nullable=False)
    steps_results_json = db.Column(db.Text, nullable=True) # Store Dict[str, Any] as JSON string
    step_statuses_json = db.Column(db.Text, nullable=True) # Store Dict[str, str] as JSON string
    status = db.Column(db.String, default="pending", nullable=False)
    updates_json = db.Column(db.Text, nullable=True) # Store List[str] as JSON string
    final_result = db.Column(db.Text, nullable=True)

    # Helper property to get/set Pydantic TasksOutput
    @property
    def plan(self) -> TasksOutput | None:
        if self.plan_json:
            try:
                return TasksOutput.parse_raw(self.plan_json)
            except Exception: # Handle potential JSON parsing errors
                 return None
        return None

    @plan.setter
    def plan(self, value: TasksOutput | None):
        self.plan_json = value.json() if value else None

    # Helper property for steps_results (name kept)
    @property
    def steps_results(self) -> dict[str, Any]:
        return json.loads(self.steps_results_json) if self.steps_results_json else {}

    @steps_results.setter
    def steps_results(self, value: dict[str, Any]):
        self.steps_results_json = json.dumps(value)

    # Helper property for step_statuses (name kept)
    @property
    def step_statuses(self) -> dict[str, str]:
        return json.loads(self.step_statuses_json) if self.step_statuses_json else {}

    @step_statuses.setter
    def step_statuses(self, value: dict[str, str]):
        self.step_statuses_json = json.dumps(value)

    # Helper property for updates
    @property
    def updates(self) -> list[str]:
         return json.loads(self.updates_json) if self.updates_json else []

    @updates.setter
    def updates(self, value: list[str]):
        self.updates_json = json.dumps(value)

    def __repr__(self):
        return f'<WorkflowSessionDB {self.id} Status: {self.status}>' 