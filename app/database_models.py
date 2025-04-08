from .extensions import db # We will create extensions.py next
import json
from .models import PlanOutput # Import Pydantic model for type hinting if desired

class WorkflowSessionDB(db.Model):
    id = db.Column(db.String, primary_key=True) # Corresponds to session_id
    plan_json = db.Column(db.Text, nullable=True) # Store PlanOutput as JSON string
    accepted_plan = db.Column(db.Boolean, default=False, nullable=False)
    current_step_index = db.Column(db.Integer, default=0, nullable=False)
    total_steps = db.Column(db.Integer, default=0, nullable=False)
    steps_results_json = db.Column(db.Text, nullable=True) # Store List[str] as JSON string
    status = db.Column(db.String, default="pending", nullable=False)
    updates_json = db.Column(db.Text, nullable=True) # Store List[str] as JSON string
    final_result = db.Column(db.Text, nullable=True)

    # Helper property to get/set Pydantic PlanOutput
    @property
    def plan(self) -> PlanOutput | None:
        if self.plan_json:
            try:
                return PlanOutput.parse_raw(self.plan_json)
            except Exception: # Handle potential JSON parsing errors
                 return None
        return None

    @plan.setter
    def plan(self, value: PlanOutput | None):
        self.plan_json = value.json() if value else None

    # Helper property for steps_results
    @property
    def steps_results(self) -> list[str]:
        return json.loads(self.steps_results_json) if self.steps_results_json else []

    @steps_results.setter
    def steps_results(self, value: list[str]):
        self.steps_results_json = json.dumps(value)

    # Helper property for updates
    @property
    def updates(self) -> list[str]:
         return json.loads(self.updates_json) if self.updates_json else []

    @updates.setter
    def updates(self, value: list[str]):
        self.updates_json = json.dumps(value)

    def __repr__(self):
        return f'<WorkflowSessionDB {self.id} Status: {self.status}>' 