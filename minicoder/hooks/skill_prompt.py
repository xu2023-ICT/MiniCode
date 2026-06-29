"""Prompt injection for available MiniCode skills."""

from __future__ import annotations

from .manager import HookEvent
from ..skills import SkillSummary, discover_skills


def format_skill_prompt(skills: list[SkillSummary]) -> str:
    if not skills:
        return ""

    lines = [
        "# Available Skills",
        "Only each skill's name and description are loaded here. If one is relevant to the user's request, call `read_skill` with that skill name before acting. If none are relevant, ignore this list.",
        "",
    ]
    for skill in skills:
        lines.append(f"- **{skill.name}**: {skill.description}")
    return "\n".join(lines)


def inject_available_skills(event: HookEvent):
    prompt = format_skill_prompt(discover_skills())
    if not prompt:
        return

    additions = event.data.setdefault("system_additions", [])
    if isinstance(additions, list):
        additions.append(prompt)
