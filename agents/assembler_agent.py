"""AssemblerAgent CLI for daily repo-aware self-assembly."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.patch_planner import PatchPlan, apply_report_patch, plan_minimal_patch  # noqa: E402
from agents.reflection_log import build_reflection_entry, write_reflection  # noqa: E402
from agents.repo_scanner import RepoState, scan_repo  # noqa: E402
from agents.risk_gate import Action, alpha_shield_gate  # noqa: E402
from agents.task_selector import SelectedTask, select_highest_leverage_task  # noqa: E402
from agents.test_runner import TestResult, run_test_command  # noqa: E402

GOAL = (
    "Turn scattered ideas, tools, repos, agents, and income paths into one operating "
    "system that compounds daily."
)
CORE_LOOP = "Observe -> Decide -> Act -> Verify -> Learn -> Improve"


def main() -> int:
    """Run the AssemblerAgent CLI."""

    parser = argparse.ArgumentParser(description="Repo-aware self-assembly agent.")
    parser.add_argument("--repo", default=".", help="Repository path to inspect.")
    parser.add_argument(
        "--mode",
        choices=("suggest", "patch", "test", "reflect"),
        default="suggest",
        help="AssemblerAgent mode to run.",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    state = scan_repo(repo)
    task = select_highest_leverage_task(state)
    plan = plan_minimal_patch(state, task)

    if args.mode == "suggest":
        print(render_report(state, task, plan, risk_result="ALLOW"))
        return 0
    if args.mode == "patch":
        return _run_patch(repo, state, task, plan)
    if args.mode == "test":
        return _run_test(repo, state, task, plan)
    if args.mode == "reflect":
        return _run_reflect(repo, state, task, plan)
    return 2


def render_report(
    state: RepoState,
    task: SelectedTask,
    plan: PatchPlan,
    *,
    risk_result: str,
    extra: str = "",
) -> str:
    """Render the required Assembly Report."""

    changed = "\n".join(f"- {line}" for line in state.changed_files) or "- clean"
    files = "\n".join(f"- {path}" for path in plan.files) or "- none"
    steps = "\n".join(f"- {step}" for step in plan.steps)

    sections = [
        "# Assembly Report",
        "## Repo State",
        f"- Repo: `{state.path}`",
        f"- Branch: `{state.branch}`",
        f"- Dirty: `{state.dirty}`",
        f"- Python files: `{len(state.python_files)}`",
        f"- Tests: `{len(state.test_files)}`",
        "- Changed files:",
        changed,
        "## Highest-Leverage Task",
        f"- Task: {task.title}",
        f"- Rationale: {task.rationale}",
        f"- Success Criteria: {task.success_criteria}",
        "## Proposed Minimal Patch",
        f"- Summary: {plan.summary}",
        "- Files:",
        files,
        "- Steps:",
        steps,
        "## Test Command",
        f"`{state.test_command}`",
        "## Risk",
        f"- Level: {task.risk_level}",
        f"- AlphaShield Gate: {risk_result}",
        "## Rollback",
        plan.rollback,
    ]
    if extra:
        sections.extend(["## Result", extra])
    return "\n".join(sections)


def _run_patch(repo: Path, state: RepoState, task: SelectedTask, plan: PatchPlan) -> int:
    action = Action(
        name="apply_report_patch",
        dry_run=False,
        has_tests=state.has_tests,
        confidence=0.84,
    )
    gate_result = alpha_shield_gate(action)
    if gate_result != "ALLOW":
        print(render_report(state, task, plan, risk_result=gate_result, extra="Patch skipped."))
        return 1

    touched = apply_report_patch(repo, task)
    entry = build_reflection_entry(
        goal=GOAL,
        action="patch",
        result=f"Touched files: {', '.join(touched) if touched else 'none'}",
        tests=f"Recommended: {state.test_command}",
        risk=gate_result,
        lesson="Keep patches repo-local and reversible until repeated success raises autonomy.",
        next_best_action=f"Run `{state.test_command}`.",
    )
    path = write_reflection(repo, entry)
    extra = f"- Touched: {', '.join(touched) if touched else 'none'}\n- Reflection: `{path}`"
    print(render_report(state, task, plan, risk_result=gate_result, extra=extra))
    return 0


def _run_test(repo: Path, state: RepoState, task: SelectedTask, plan: PatchPlan) -> int:
    gate_result = alpha_shield_gate(Action(name="run_tests", has_tests=True, confidence=0.9))
    if gate_result != "ALLOW":
        path = _write_blocked_reflection(
            repo,
            action="test",
            gate_result=gate_result,
            tests=f"Skipped: {state.test_command}",
            next_best_action="Lower risk or add safeguards before running tests.",
        )
        print(
            render_report(
                state,
                task,
                plan,
                risk_result=gate_result,
                extra=f"- Reflection: `{path}`\n- Result: Test run skipped.",
            )
        )
        return 1

    result = run_test_command(repo, state.test_command)
    entry = build_reflection_entry(
        goal=GOAL,
        action="test",
        result="passed" if result.passed else "failed",
        tests=f"{result.command} exited {result.returncode}",
        risk=gate_result,
        lesson="Verification must be captured before increasing autonomy.",
        next_best_action="Reflect on the result and queue the next task.",
    )
    path = write_reflection(repo, entry)
    print(
        render_report(state, task, plan, risk_result=gate_result, extra=_format_test(result, path))
    )
    return result.returncode


def _run_reflect(repo: Path, state: RepoState, task: SelectedTask, plan: PatchPlan) -> int:
    gate_result = alpha_shield_gate(Action(name="write_reflection", has_tests=state.has_tests))
    if gate_result != "ALLOW":
        path = _write_blocked_reflection(
            repo,
            action="reflect",
            gate_result=gate_result,
            tests=f"Recommended: {state.test_command}",
            next_best_action="Review the AlphaShield decision before writing reflection memory.",
        )
        print(
            render_report(
                state,
                task,
                plan,
                risk_result=gate_result,
                extra=f"- Reflection: `{path}`\n- Result: Reflection write skipped.",
            )
        )
        return 1

    entry = build_reflection_entry(
        goal=GOAL,
        action="reflect",
        result=f"Selected next task: {task.title}",
        tests=f"Recommended: {state.test_command}",
        risk=gate_result,
        lesson=f"The daily loop is `{CORE_LOOP}`.",
        next_best_action=task.success_criteria,
    )
    path = write_reflection(repo, entry)
    print(
        render_report(
            state,
            task,
            plan,
            risk_result=gate_result,
            extra=f"- Reflection written: `{path}`",
        )
    )
    return 0


def _format_test(result: TestResult, reflection_path: Path) -> str:
    output = result.stdout or result.stderr or "No test output captured."
    return (
        f"- Command: `{result.command}`\n"
        f"- Exit Code: `{result.returncode}`\n"
        f"- Reflection: `{reflection_path}`\n"
        f"- Output:\n{output}"
    )


def _write_blocked_reflection(
    repo: Path,
    *,
    action: str,
    gate_result: str,
    tests: str,
    next_best_action: str,
) -> Path:
    entry = build_reflection_entry(
        goal=GOAL,
        action=action,
        result="blocked before execution",
        tests=tests,
        risk=gate_result,
        lesson="AlphaShield gate decisions must be enforced before side effects occur.",
        next_best_action=next_best_action,
    )
    return write_reflection(repo, entry)


if __name__ == "__main__":
    raise SystemExit(main())
