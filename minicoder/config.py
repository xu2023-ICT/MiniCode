"""Configuration - env vars and defaults."""

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv():
    """Load .env from cwd, walking up to home dir. No-op if python-dotenv missing."""
    try:
        from dotenv import load_dotenv
        # search cwd first, then parent dirs up to ~
        env_path = Path(".env")
        if not env_path.exists():
            cur = Path.cwd()
            home = Path.home()
            while cur != home and cur != cur.parent:
                candidate = cur / ".env"
                if candidate.exists():
                    env_path = candidate
                    break
                cur = cur.parent
        load_dotenv(env_path, override=False)
    except ImportError:
        pass  # python-dotenv not installed, silently skip


@dataclass
class Config:
    model: str = "deepseek-v4-flash"
    api_key: str = ""
    base_url: str | None = "https://api.deepseek.com"
    max_tokens: int = 8192
    temperature: float = 1.0
    max_context_tokens: int = 1_048_576
    provider: str = "openai"

    @classmethod
    def from_env(cls) -> "Config":
        # load .env if present (won't override existing env vars)
        _load_dotenv()
        # pick up common env vars automatically
        api_key = (
            os.getenv("MINICODE_API_KEY")
            or ""
        )
        return cls(
            model=os.getenv("MINICODE_MODEL", "deepseek-v4-flash"),
            api_key=api_key,
            base_url=os.getenv("MINICODE_BASE_URL", "https://api.deepseek.com"),
            max_tokens=int(os.getenv("MINICODE_MAX_TOKENS", "8192")),
            temperature=float(os.getenv("MINICODE_TEMPERATURE", "1.0")),
            max_context_tokens=int(os.getenv("MINICODE_MAX_CONTEXT", "1048576")),
            provider=os.getenv("MINICODE_PROVIDER", "openai"),
        )
