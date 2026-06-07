"""Repository scanner for AssemblerAgent."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

IGNORED_PARTS = {".git", ".pytest_cache", "__pycache__", "venv", ".venv", "env", "ENV"}
GIT_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class RepoState:
    """Snapshot of the repository facts needed for assembly decisions."""

    path: Path
    branch: str
    dirty: bool
    changed_files: tuple[str, ...]
    tracked_files: tuple[str, ...]
    python_files: tuple[str, ...]
    test_files: tuple[str, ...]
    report_files: tuple[str, ...]
    test_command: str

    @property
    def has_tests(self) -> bool:
        return bool(self.test_files)


def scan_repo(repo: str | Path) -> RepoState:
    """Read project state without mutating the repository."""

    repo_path = Path(repo).resolve()
    tracked_files = _git_lines(repo_path, ["ls-files"])
    changed_files = _git_lines(repo_path, ["status", "--short"])
    branch = _git_stdout(repo_path, ["branch", "--show-current"]) or "unknown"

    if not tracked_files:
        tracked_files = _walk_files(repo_path)

    python_files = tuple(path for path in tracked_files if path.endswith(".py"))
    test_files = tuple(
        path
        for path in tracked_files
        if Path(path).parts[:1] == ("tests",) and os.path.basename(path).startswith("test_")
    )
    report_files = tuple(path for path in tracked_files if path.startswith("reports/"))

    return RepoState(
        path=repo_path,
        branch=branch,
        dirty=bool(changed_files),
        changed_files=tuple(changed_files),
        tracked_files=tuple(tracked_files),
        python_files=python_files,
        test_files=test_files,
        report_files=report_files,
        test_command=_detect_test_command(repo_path, tracked_files),
    )


def _git_lines(repo_path: Path, args: list[str]) -> tuple[str, ...]:
    output = _git_stdout(repo_path, args)
    return tuple(line for line in output.splitlines() if line.strip())


def _git_stdout(repo_path: Path, args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_path), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""

    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _walk_files(repo_path: Path) -> tuple[str, ...]:
    files: list[str] = []
    for path in repo_path.rglob("*"):
        if not path.is_file() or IGNORED_PARTS.intersection(path.parts):
            continue
        files.append(path.relative_to(repo_path).as_posix())
    return tuple(sorted(files))


def _detect_test_command(repo_path: Path, tracked_files: tuple[str, ...]) -> str:
    if "tests/test_assembler_agent.py" in tracked_files:
        return "pytest -q tests/test_assembler_agent.py"
    if (repo_path / "pyproject.toml").exists() or any(path.startswith("tests/") for path in tracked_files):
        return "pytest -q"
    return "python -m compileall agents"
