"""Event hook registry and dispatcher."""

from dataclasses import dataclass, field
from typing import Any, Callable

from rich.console import Console


@dataclass
class HookEvent:
    """Payload passed to hook callbacks."""

    data: dict[str, Any] = field(default_factory=dict)


HookCallback = Callable[[HookEvent], None]


HOOK_EVENTS = ("UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop")
DEFAULT_HOOKS = {name: [] for name in HOOK_EVENTS}
console = Console()


class HookManager:
    """Register callbacks by event name and trigger them in order."""

    def __init__(self):
        self._hooks: dict[str, list[HookCallback]] = {
            name: callbacks.copy()
            for name, callbacks in DEFAULT_HOOKS.items()
        }

    def register(self, event_name: str, callback: HookCallback):
        """Register a callback for one event name."""
        self._ensure_known_event(event_name)
        self._hooks[event_name].append(callback)

    def trigger(self, event_name: str, event: HookEvent | None = None):
        """Trigger callbacks for an event."""
        self._ensure_known_event(event_name)
        event = event or HookEvent()

        for callback in self._hooks.get(event_name, []):
            try:
                callback(event)
            except Exception as e:
                console.print(f"[red]Hook error in {event_name}: {e}[/]")

    def _ensure_known_event(self, event_name: str):
        if event_name not in self._hooks:
            raise ValueError(f"Unknown hook event: {event_name}")


def default_hooks() -> HookManager:
    from .skill_prompt import inject_available_skills

    hooks = HookManager()
    hooks.register("UserPromptSubmit", inject_available_skills)
    return hooks
