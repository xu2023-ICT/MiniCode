"""MiniCode skill discovery and loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillSummary:
    name: str
    description: str
    path: Path


def skill_roots(cwd: Path | None = None, home: Path | None = None) -> list[Path]:
    """Return MiniCode skill roots in runtime-first order."""
    cwd = (cwd or Path.cwd()).resolve()
    home = (home or Path.home()).resolve()
    roots = [
        cwd / "skills",
        cwd / ".minicode" / "skills",
        home / ".minicode" / "skills",
    ]

    seen: set[Path] = set()
    result: list[Path] = []
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        result.append(resolved)
    return result


def discover_skills(roots: list[Path] | None = None) -> list[SkillSummary]:
    """Find SKILL.md files and parse only name + description frontmatter."""
    roots = roots if roots is not None else skill_roots()
    summaries: list[SkillSummary] = []
    seen_paths: set[Path] = set()
    seen_names: set[str] = set()

    for root in roots:
        if not root.is_dir():
            continue
        for skill_file in sorted(root.rglob("SKILL.md")):
            try:
                resolved = skill_file.resolve()
            except OSError:
                continue
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)

            summary = parse_skill_frontmatter(resolved)
            if summary is None:
                continue
            if summary.name in seen_names:
                continue
            seen_names.add(summary.name)
            summaries.append(summary)

    return summaries


def find_skill(name: str, roots: list[Path] | None = None) -> SkillSummary | None:
    wanted = name.strip()
    if not wanted:
        return None
    for skill in discover_skills(roots):
        if skill.name == wanted:
            return skill
    return None


def parse_skill_frontmatter(path: Path) -> SkillSummary | None:
    """Parse initial YAML frontmatter without loading the full skill body."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            first = f.readline()
            if first.strip() != "---":
                return None

            fields: dict[str, str] = {}
            for _ in range(80):
                line = f.readline()
                if not line:
                    return None
                if line.strip() == "---":
                    break
                key, value = _parse_frontmatter_line(line)
                if key in ("name", "description"):
                    fields[key] = value
            else:
                return None
    except OSError:
        return None

    name = fields.get("name", "").strip()
    description = fields.get("description", "").strip()
    if not name or not description:
        return None
    return SkillSummary(name=name, description=description, path=path)


def read_skill(name: str, roots: list[Path] | None = None) -> str:
    skill = find_skill(name, roots)
    if skill is None:
        return f"Error: skill '{name}' not found"
    try:
        return skill.path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"Error reading skill '{name}': {e}"


def _parse_frontmatter_line(line: str) -> tuple[str, str]:
    if ":" not in line:
        return "", ""
    key, value = line.split(":", 1)
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    return key.strip(), value
