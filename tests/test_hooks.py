from minicoder.agent import Agent
from minicoder.hooks import HookEvent, HookManager, default_hooks
from minicoder.llm import LLMResponse, ToolCall
from minicoder.tools.base import Tool


class EchoTool(Tool):
    name = "echo"
    description = "Echo a value"
    parameters = {
        "type": "object",
        "properties": {"value": {"type": "string"}},
        "required": ["value"],
    }

    def __init__(self):
        self.calls = []

    def execute(self, value: str) -> str:
        self.calls.append(value)
        return f"echo:{value}"


class FakeLLM:
    def chat(self, messages, tools=None, on_token=None):
        return LLMResponse(content="done")


def test_agent_exec_tool_without_hooks_preserves_behavior():
    tool = EchoTool()
    agent = Agent(llm=object(), tools=[tool])
    call = ToolCall(id="call_1", name="echo", arguments={"value": "hello"})

    assert agent._exec_tool(call) == "echo:hello"
    assert tool.calls == ["hello"]


def test_tool_hooks_receive_before_and_after_events():
    events = []
    hooks = HookManager()
    tool = EchoTool()
    agent = Agent(llm=object(), tools=[tool], hooks=hooks)
    call = ToolCall(id="call_1", name="echo", arguments={"value": "hello"})

    hooks.register("PreToolUse", lambda event: events.append(("PreToolUse", event.data.copy())))
    hooks.register("PostToolUse", lambda event: events.append(("PostToolUse", event.data.copy())))

    assert agent._exec_tool(call) == "echo:hello"
    assert events == [
        (
            "PreToolUse",
            {
                "tool_call_id": "call_1",
                "tool_name": "echo",
                "arguments": {"value": "hello"},
            },
        ),
        (
            "PostToolUse",
            {
                "tool_call_id": "call_1",
                "tool_name": "echo",
                "arguments": {"value": "hello"},
                "result": "echo:hello",
            },
        ),
    ]


def test_hook_manager_rejects_unknown_events():
    hooks = HookManager()

    try:
        hooks.register("TypoEvent", lambda event: None)
    except ValueError as e:
        assert str(e) == "Unknown hook event: TypoEvent"
    else:
        raise AssertionError("expected unknown hook event to fail")


def test_user_prompt_submit_and_stop_hooks_fire_during_chat():
    events = []
    hooks = HookManager()
    agent = Agent(llm=FakeLLM(), tools=[], hooks=hooks)

    hooks.register("UserPromptSubmit", lambda event: events.append(("UserPromptSubmit", event.data.copy())))
    hooks.register("Stop", lambda event: events.append(("Stop", event.data.copy())))

    assert agent.chat("hello") == "done"
    assert events == [
        ("UserPromptSubmit", {"prompt": "hello"}),
        ("Stop", {"response": "done"}),
    ]
