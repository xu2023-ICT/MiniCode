"""Tool for loading a selected MiniCode skill."""

from .base import Tool
from ..skills import read_skill


class ReadSkillTool(Tool):
    name = "read_skill"
    description = (
        "Read the full SKILL.md for one available MiniCode skill by name. "
        "Use after the available skills list indicates a skill is relevant."
    )
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Skill name from the available skills list",
            },
        },
        "required": ["name"],
    }

    def execute(self, name: str) -> str:
        return read_skill(name)
