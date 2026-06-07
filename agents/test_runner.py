"""Test command runner for AssemblerAgent."""

from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestResult:
    """Captured test execution result."""

    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def run_test_command(repo: str | Path, command: str) -> TestResult:
    """Run a shell-free test command and capture output."""

    try:
        args = shlex.split(command)
    except ValueError as exc:
        return TestResult(command=command, returncode=2, stdout="", stderr=str(exc))
    if not args:
        return TestResult(command=command, returncode=2, stdout="", stderr="Empty test command")
    if args and args[0] == "pytest" and shutil.which("pytest") is None:
        args = [sys.executable, "-m", "pytest", *args[1:]]
    elif shutil.which(args[0]) is None and not Path(args[0]).exists():
        return TestResult(
            command=command,
            returncode=127,
            stdout="",
            stderr=f"Command not found: {args[0]}",
        )
    try:
        completed = subprocess.run(
            args,
            cwd=Path(repo).resolve(),
            check=False,
            capture_output=True,
            text=True,
            timeout=900,
        )
    except FileNotFoundError as exc:
        return TestResult(command=command, returncode=127, stdout="", stderr=str(exc))
    except subprocess.TimeoutExpired as exc:
        return TestResult(
            command=command,
            returncode=124,
            stdout=(exc.stdout or "").strip(),
            stderr=(exc.stderr or "Test command timed out").strip(),
        )
    return TestResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )
