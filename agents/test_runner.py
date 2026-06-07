"""Test command runner for AssemblerAgent."""

from __future__ import annotations

import shlex
import subprocess
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

