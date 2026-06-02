import threading
from concurrent.futures import ThreadPoolExecutor

from minicoder.agent import Agent
from minicoder.llm import ToolCall
from minicoder.tools import ALL_TOOLS, get_tool
from minicoder.tools.ask_user import AskUserTool
from minicoder.tools.base import Tool


def test_ask_user_schema_includes_question_and_choices():
    schema = AskUserTool().schema()

    function = schema["function"]
    assert function["name"] == "ask_user"
    assert function["parameters"]["required"] == ["question"]
    assert function["parameters"]["properties"]["question"]["type"] == "string"
    assert function["parameters"]["properties"]["choices"]["type"] == "array"


def test_ask_user_execute_uses_injected_input():
    prompts = []

    def fake_input(prompt):
        prompts.append(prompt)
        return "Use pytest"

    result = AskUserTool(input_func=fake_input).execute(
        question="Which test runner should I use?",
        choices=["pytest", "unittest"],
    )

    assert result == "User answered: Use pytest"
    assert "Which test runner should I use?" in prompts[0]
    assert "1. pytest" in prompts[0]
    assert "2. unittest" in prompts[0]


def test_ask_user_rejects_empty_question():
    result = AskUserTool(input_func=lambda prompt: "ignored").execute("  ")

    assert result == "Error: question must not be empty"


def test_ask_user_is_registered():
    assert any(tool.name == "ask_user" for tool in ALL_TOOLS)
    assert get_tool("ask_user").name == "ask_user"


def test_agent_uses_configured_tool_instance_for_execution():
    tool = AskUserTool(input_func=lambda prompt: "configured answer")
    agent = Agent(llm=object(), tools=[tool])
    call = ToolCall(
        id="call_1",
        name="ask_user",
        arguments={"question": "Proceed?"},
    )

    assert agent._exec_tool(call) == "User answered: configured answer"


def test_ask_user_lock_serializes_concurrent_calls():
    """Two ask_user calls on parallel threads must not interleave on stdin.

    The class-level lock should make the second call wait until the first
    has fully released input(), so enter/exit events stay paired.
    """
    events = []
    events_lock = threading.Lock()
    inside = threading.Event()  # set while a fake_input is mid-flight

    def fake_input(prompt):
        # If serialization works, `inside` is always clear when we enter:
        # the previous holder cleared it before releasing the ask_user lock.
        assert not inside.is_set(), "two ask_user calls overlapped on stdin"
        inside.set()
        with events_lock:
            events.append(f"enter:{prompt.splitlines()[-2]}")
        # give the other thread a real chance to race in
        import time; time.sleep(0.05)
        with events_lock:
            events.append(f"exit:{prompt.splitlines()[-2]}")
        inside.clear()
        return "ok"

    tool = AskUserTool(input_func=fake_input)
    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(tool.execute, "Q1")
        f2 = pool.submit(tool.execute, "Q2")
        results = sorted([f1.result(), f2.result()])

    assert results == ["User answered: ok", "User answered: ok"]
    # exactly 4 events, and every enter is immediately followed by its exit
    assert len(events) == 4
    for i in range(0, 4, 2):
        enter_q = events[i].split(":", 1)[1]
        exit_q = events[i + 1].split(":", 1)[1]
        assert events[i].startswith("enter:") and events[i + 1].startswith("exit:")
        assert enter_q == exit_q, f"enter/exit mismatch: {events}"
