"""MiniCoder - Minimal AI coding agent inspired by Claude Code's architecture."""

__version__ = "0.1.0"

from minicoder.agent import Agent
from minicoder.llm import LLM
from minicoder.config import Config
from minicoder.tools import ALL_TOOLS

__all__ = ["Agent", "LLM", "Config", "ALL_TOOLS", "__version__"]
