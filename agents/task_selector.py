"""Select the next self-assembly task from repository state."""

from __future__ import annotations

from dataclasses import dataclass

from agents.repo_scanner import RepoState


@dataclass(frozen=True)
class SelectedTask:
    """Highest-leverage task chosen for the next assembly loop."""

    title: str
    rationale: str
    success_criteria: str
    risk_level: str
    suggested_files: tuple[str, ...]


def select_highest_leverage_task(state: RepoState) -> SelectedTask:
    """Pick the smallest useful task that improves the operating system."""

    tracked = set(state.tracked_files)
    report_targets = {
        "reports/daily_status.md",
        "reports/decisions.md",
        "reports/failures.md",
        "reports/next_actions.md",
    }

    if "agents/assembler_agent.py" not in tracked:
        return SelectedTask(
            title="Add AssemblerAgent CLI skeleton",
            rationale="The repo needs a runnable nucleus before daily self-assembly can compound.",
            success_criteria="`python agents/assembler_agent.py --repo . --mode suggest` prints an Assembly Report.",
            risk_level="low",
            suggested_files=(
                "agents/assembler_agent.py",
                "agents/risk_gate.py",
                "agents/repo_scanner.py",
            ),
        )

    if missing_reports := tuple(sorted(report_targets - tracked)):
        return SelectedTask(
            title="Create operating report files",
            rationale="AssemblerAgent needs stable report surfaces for daily status, decisions, failures, and queued work.",
            success_criteria=f"Missing report files exist: {', '.join(missing_reports)}.",
            risk_level="low",
            suggested_files=missing_reports,
        )

    if "tests/test_assembler_agent.py" not in tracked:
        return SelectedTask(
            title="Add focused AssemblerAgent tests",
            rationale="Autonomy should only increase after verified success, so the new loop needs executable checks.",
            success_criteria="Focused pytest coverage passes for scan, select, gate, report, and reflection paths.",
            risk_level="low",
            suggested_files=("tests/test_assembler_agent.py",),
        )

    return SelectedTask(
        title="Run the daily suggest-test-reflect loop",
        rationale="The skeleton exists; the next useful step is keeping the loop verified and the queue current.",
        success_criteria="Suggest mode prints a report, focused tests pass, and reflect mode writes memory.",
        risk_level="low",
        suggested_files=("reports/next_actions.md", "reports/reflection_log.jsonl"),
    )

