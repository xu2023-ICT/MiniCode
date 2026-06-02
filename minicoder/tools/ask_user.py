"""Ask the human user for clarification."""

import threading
from collections.abc import Callable, Sequence

from .base import Tool

# Class-level lock: stdin is a single shared resource. If the agent issues
# multiple ask_user calls in one batch, the executor runs them on parallel
# threads and they'd race for the terminal. Holding this lock around the
# input() call serializes them — one question is fully answered before the
# next prompt appears.
_ASK_LOCK = threading.Lock()


class AskUserTool(Tool):
    name = "ask_user"
    description = (
        "Ask the human user a clarification question and return their answer. "
        "Use this when required information is missing or a decision should not be guessed."
    )
    parameters = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The specific question to ask the user",
            },
            "choices": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional suggested answers to show the user",
            },
        },
        "required": ["question"],
    }

    def __init__(self, input_func: Callable[[str], str] | None = None):
        self._input = input_func or input

    def execute(self, question: str, choices: Sequence[str] | None = None) -> str:
        question = question.strip()
        if not question:
            return "Error: question must not be empty"

        prompt = _format_prompt(question, choices or [])
        with _ASK_LOCK:
            try:
                answer = self._input(prompt).strip()
            except EOFError:
                return "Error: user input is unavailable"

        if not answer:
            return "User answered with an empty response."
        return f"User answered: {answer}"


def _format_prompt(question: str, choices: Sequence[str]) -> str:
    lines = ["", "MiniCoder needs input:", question]
    for i, choice in enumerate(choices, start=1):
        lines.append(f"  {i}. {choice}")
    lines.append("Answer: ")
    return "\n".join(lines)
