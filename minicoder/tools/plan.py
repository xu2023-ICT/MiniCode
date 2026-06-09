"""Structured task planning tool."""

from .base import Tool


VALID_STATUSES = {"pending", "in_progress", "completed"}


class UpdatePlanTool(Tool):
    name = "update_plan"
    description = (
        "Create or update the current task plan for complex, multi-step work. "
        "Pass the complete current plan every time, and update step statuses "
        "as work progresses."
    )
    parameters = {
        "type": "object",
        "properties": {
            "plan": {
                "type": "array",
                "description": "The complete current plan",
                "items": {
                    "type": "object",
                    "properties": {
                        "step": {
                            "type": "string",
                            "description": "A concise action-oriented step",
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"],
                            "description": "The current status for this step",
                        },
                    },
                    "required": ["step", "status"],
                },
            },
        },
        "required": ["plan"],
    }

    # set by Agent.__init__ after construction
    _parent_agent = None

    def execute(self, plan: list[dict], explanation: str | None = None) -> str:
        if self._parent_agent is None:
            return "Error: update_plan tool not initialized (no parent agent)"

        normalized = _normalize_plan(plan)
        if isinstance(normalized, str):
            return normalized

        self._parent_agent.plan = {
            "explanation": explanation.strip() if isinstance(explanation, str) and explanation.strip() else None,
            "steps": normalized,
        }
        return "Plan updated."


def _normalize_plan(plan: list[dict]) -> list[dict] | str:
    if not isinstance(plan, list):
        return "Error: plan must be a list"

    normalized = []
    in_progress_count = 0
    for index, item in enumerate(plan, start=1):
        if not isinstance(item, dict):
            return f"Error: plan item {index} must be an object"

        step = item.get("step")
        status = item.get("status")
        if not isinstance(step, str) or not step.strip():
            return f"Error: plan item {index} step must be a non-empty string"
        if status not in VALID_STATUSES:
            return f"Error: plan item {index} status must be one of: completed, in_progress, pending"
        if status == "in_progress":
            in_progress_count += 1

        normalized.append({"step": step.strip(), "status": status})

    if in_progress_count > 1:
        return "Error: at most one plan step can be in_progress"

    return normalized
