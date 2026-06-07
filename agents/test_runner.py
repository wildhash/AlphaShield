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

    args = shlex.split(command)
    if args and args[0] == "pytest" and shutil.which("pytest") is None:
        args = [sys.executable, "-m", "pytest", *args[1:]]
    completed = subprocess.run(
        args,
        cwd=Path(repo).resolve(),
        check=False,
        capture_output=True,
        text=True,
    )
    return TestResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )

