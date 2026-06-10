"""Reflection memory for self-assembly actions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class ReflectionEntry:
    """Learning substrate record written after completed actions."""

    timestamp: str
    goal: str
    action: str
    result: str
    tests: str
    risk: str
    lesson: str
    next_best_action: str


def build_reflection_entry(
    *,
    goal: str,
    action: str,
    result: str,
    tests: str,
    risk: str,
    lesson: str,
    next_best_action: str,
) -> ReflectionEntry:
    """Create a timestamped reflection entry."""

    return ReflectionEntry(
        timestamp=datetime.now(UTC).isoformat(),
        goal=goal,
        action=action,
        result=result,
        tests=tests,
        risk=risk,
        lesson=lesson,
        next_best_action=next_best_action,
    )


def write_reflection(repo: str | Path, entry: ReflectionEntry) -> Path:
    """Append reflection memory as JSON Lines."""

    reports_dir = Path(repo).resolve() / "reports"
    reports_dir.mkdir(exist_ok=True)
    log_path = reports_dir / "reflection_log.jsonl"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), sort_keys=True))
        handle.write("\n")
    return log_path

