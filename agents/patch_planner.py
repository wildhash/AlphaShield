"""Patch planning and narrow report maintenance for AssemblerAgent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agents.repo_scanner import RepoState
from agents.task_selector import SelectedTask


REPORT_FILES = {
    "daily_status.md": "# Daily Status\n\nNo assembly run recorded yet.\n",
    "decisions.md": "# Decisions\n\n- Nucleus: Botspot + AlphaShield autonomous agent marketplace.\n",
    "failures.md": "# Failures\n\nNo failures recorded yet.\n",
    "next_actions.md": "# Next Actions\n\n- Run `python agents/assembler_agent.py --repo . --mode suggest`.\n",
}


@dataclass(frozen=True)
class PatchPlan:
    """Smallest safe patch proposal for the selected task."""

    summary: str
    files: tuple[str, ...]
    steps: tuple[str, ...]
    rollback: str


def plan_minimal_patch(state: RepoState, task: SelectedTask) -> PatchPlan:
    """Build a minimal patch plan from task and repo state."""

    return PatchPlan(
        summary=f"Advance `{task.title}` with the narrowest repo-local change.",
        files=task.suggested_files,
        steps=(
            "Confirm AlphaShield gate result is ALLOW.",
            "Touch only the files listed in the proposed patch.",
            f"Run `{state.test_command}` after the patch.",
            "Write reflection memory with result and next best action.",
        ),
        rollback=f"Use `git checkout -- {' '.join(task.suggested_files)}` to revert the patch files.",
    )


def apply_report_patch(repo: str | Path, task: SelectedTask) -> tuple[str, ...]:
    """Create/update only report files for patch mode."""

    reports_dir = Path(repo).resolve() / "reports"
    reports_dir.mkdir(exist_ok=True)

    touched: list[str] = []
    for filename, content in REPORT_FILES.items():
        path = reports_dir / filename
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            touched.append(path.relative_to(Path(repo).resolve()).as_posix())

    next_actions = reports_dir / "next_actions.md"
    marker = f"- Queued by AssemblerAgent: {task.title}"
    current = next_actions.read_text(encoding="utf-8")
    if marker not in current:
        next_actions.write_text(f"{current.rstrip()}\n{marker}\n", encoding="utf-8")
        touched.append("reports/next_actions.md")

    return tuple(touched)

