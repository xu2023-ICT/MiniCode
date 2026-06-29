"""Tool registry."""

from .bash import BashTool
from .read import ReadFileTool
from .write import WriteFileTool
from .edit import EditFileTool
from .glob_tool import GlobTool
from .grep import GrepTool
from .agent import AgentTool
from .ask_user import AskUserTool
from .plan import UpdatePlanTool
from .skill import ReadSkillTool

ALL_TOOLS = [
    BashTool(),
    ReadFileTool(),
    WriteFileTool(),
    EditFileTool(),
    GlobTool(),
    GrepTool(),
    AgentTool(),
    AskUserTool(),
    UpdatePlanTool(),
    ReadSkillTool(),
]


def get_tool(name: str, tools=None):
    """Look up a tool by name.

    Pass a custom `tools` list (e.g. an Agent's own configured tools) to
    search that list instead of the global ALL_TOOLS registry. This lets
    callers that hold their own tool instances find them rather than the
    default singletons.
    """
    pool = tools if tools is not None else ALL_TOOLS
    for t in pool:
        if t.name == name:
            return t
    return None
