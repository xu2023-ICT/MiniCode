from rich.console import Console

from minicoder.agent import Agent
from minicoder.cli import _render_plan
from minicoder.hooks import HookManager
from minicoder.llm import ToolCall
from minicoder.tools import ALL_TOOLS, get_tool
from minicoder.tools.base import Tool
from minicoder.tools.plan import UpdatePlanTool


class CheckPlanTool(Tool):
    name = "check_plan"
    description = "Check whether the agent has a plan"
    parameters = {"type": "object", "properties": {}}

    def __init__(self):
        self.agent = None

    def execute(self) -> str:
        return "has plan" if self.agent.plan else "missing plan"


def _plan_payload(status: str = "in_progress"):
    return {
        "explanation": "Need several steps",
        "plan": [
            {"step": "Read relevant files", "status": status},
            {"step": "Make the change", "status": "pending"},
        ],
    }


def test_update_plan_schema_includes_full_plan_statuses():
    schema = UpdatePlanTool().schema()

    function = schema["function"]
    plan_items = function["parameters"]["properties"]["plan"]["items"]
    assert function["name"] == "update_plan"
    assert function["parameters"]["required"] == ["plan"]
    assert plan_items["required"] == ["step", "status"]
    assert plan_items["properties"]["status"]["enum"] == ["pending", "in_progress", "completed"]


def test_update_plan_is_registered():
    assert any(tool.name == "update_plan" for tool in ALL_TOOLS)
    assert get_tool("update_plan").name == "update_plan"


def test_update_plan_updates_agent_state_and_reset_clears_it():
    tool = UpdatePlanTool()
    agent = Agent(llm=object(), tools=[tool], hooks=HookManager())
    call = ToolCall(id="call_1", name="update_plan", arguments=_plan_payload())

    assert agent._exec_tool(call) == "Plan updated."
    assert agent.plan == {
        "explanation": "Need several steps",
        "steps": [
            {"step": "Read relevant files", "status": "in_progress"},
            {"step": "Make the change", "status": "pending"},
        ],
    }

    agent.reset()
    assert agent.plan is None


def test_update_plan_rejects_multiple_in_progress_steps():
    tool = UpdatePlanTool()
    agent = Agent(llm=object(), tools=[tool], hooks=HookManager())

    result = tool.execute(
        plan=[
            {"step": "One", "status": "in_progress"},
            {"step": "Two", "status": "in_progress"},
        ]
    )

    assert result == "Error: at most one plan step can be in_progress"
    assert agent.plan is None


def test_update_plan_executes_before_other_tools_but_preserves_result_order():
    plan_tool = UpdatePlanTool()
    check_tool = CheckPlanTool()
    agent = Agent(llm=object(), tools=[check_tool, plan_tool], hooks=HookManager())
    check_tool.agent = agent

    results = agent._exec_tools_parallel(
        [
            ToolCall(id="call_1", name="check_plan", arguments={}),
            ToolCall(id="call_2", name="update_plan", arguments=_plan_payload()),
        ]
    )

    assert results == ["has plan", "Plan updated."]


def test_render_plan_prints_checklist(monkeypatch):
    console = Console(record=True, force_terminal=False, width=120)
    monkeypatch.setattr("minicoder.cli.console", console)

    _render_plan({
        "plan": [
            {"step": "Read relevant files", "status": "completed"},
            {"step": "Make the change", "status": "in_progress"},
            {"step": "Run tests", "status": "pending"},
        ]
    })

    output = console.export_text()
    assert "Plan" in output
    assert "[x] Read relevant files" in output
    assert "[>] Make the change" in output
    assert "[ ] Run tests" in output
