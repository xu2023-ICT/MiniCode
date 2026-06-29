from minicoder.agent import Agent
from minicoder.hooks import HookEvent, HookManager, default_hooks
from minicoder.hooks.skill_prompt import format_skill_prompt
from minicoder.llm import LLMResponse, ToolCall
from minicoder.skills import discover_skills, read_skill, skill_roots
from minicoder.tools import get_tool
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


class CapturingLLM:
    def __init__(self):
        self.messages = None

    def chat(self, messages, tools=None, on_token=None):
        self.messages = messages
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

    hooks.register("PreToolUse", lambda event: events.append(event.data.copy()))
    hooks.trigger(
        "PreToolUse",
        HookEvent(
            data={
                "tool_call_id": "call_1",
                "tool_name": "echo",
                "arguments": {"value": "hello"},
            },
        ),
    )

    assert events == [
        {
            "tool_call_id": "call_1",
            "tool_name": "echo",
            "arguments": {"value": "hello"},
        },
    ]


def test_hook_manager_rejects_unknown_events():
    hooks = HookManager()

    try:
        hooks.register("TypoEvent", lambda event: None)
    except ValueError as e:
        assert str(e) == "Unknown hook event: TypoEvent"
    else:
        raise AssertionError("expected unknown hook event to fail")


def test_agent_accepts_hooks_parameter_without_requiring_hooks():
    hooks = HookManager()
    agent = Agent(llm=FakeLLM(), tools=[], hooks=hooks)

    assert agent.chat("hello") == "done"
    assert agent.hooks is hooks


def test_skill_discovery_reads_only_frontmatter(tmp_path):
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        "---\n"
        "name: demo-skill\n"
        "description: Use when testing skill discovery.\n"
        "---\n"
        "\n"
        "# Body that should not be needed for discovery\n",
        encoding="utf-8",
    )

    skills = discover_skills([tmp_path / "skills"])

    assert len(skills) == 1
    assert skills[0].name == "demo-skill"
    assert skills[0].description == "Use when testing skill discovery."
    assert skills[0].path == skill_file


def test_skill_prompt_points_model_to_read_selected_skill(tmp_path):
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        "---\n"
        "name: demo-skill\n"
        "description: Use when testing skill prompt formatting.\n"
        "---\n",
        encoding="utf-8",
    )

    prompt = format_skill_prompt(discover_skills([tmp_path / "skills"]))

    assert "Only each skill's name and description are loaded here." in prompt
    assert "call `read_skill` with that skill name before acting" in prompt
    assert "demo-skill" in prompt
    assert str(skill_file) not in prompt


def test_skill_roots_use_runtime_and_minicode_dirs(tmp_path):
    cwd = tmp_path / "repo"
    home = tmp_path / "home"

    assert skill_roots(cwd=cwd, home=home) == [
        cwd.resolve() / "skills",
        cwd.resolve() / ".minicode" / "skills",
        home.resolve() / ".minicode" / "skills",
    ]


def test_read_skill_loads_selected_skill_body(tmp_path):
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        "---\n"
        "name: demo-skill\n"
        "description: Use when testing skill reading.\n"
        "---\n"
        "\n"
        "# Demo Skill\n"
        "Full body.\n",
        encoding="utf-8",
    )

    assert "# Demo Skill" in read_skill("demo-skill", [tmp_path / "skills"])


def test_read_skill_tool_is_registered():
    assert get_tool("read_skill").name == "read_skill"


def test_user_prompt_hook_can_extend_system_prompt():
    hooks = HookManager()
    hooks.register(
        "UserPromptSubmit",
        lambda event: event.data["system_additions"].append("extra system context"),
    )
    llm = CapturingLLM()
    agent = Agent(llm=llm, tools=[], hooks=hooks)

    assert agent.chat("hello") == "done"

    assert llm.messages is not None
    assert llm.messages[0]["role"] == "system"
    assert "extra system context" in llm.messages[0]["content"]
