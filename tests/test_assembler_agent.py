"""Tests for the self-assembly agent skeleton."""

from __future__ import annotations

import json
import subprocess
import sys

from agents.patch_planner import apply_report_patch, plan_minimal_patch
from agents.reflection_log import build_reflection_entry, write_reflection
from agents.repo_scanner import scan_repo
from agents.risk_gate import Action, alpha_shield_gate
from agents.task_selector import select_highest_leverage_task


def test_alpha_shield_gate_blocks_reckless_actions() -> None:
    assert alpha_shield_gate(Action(name="trade", touches_money=True, dry_run=False)) == "BLOCK"
    assert alpha_shield_gate(Action(name="delete", deletes_data=True, has_backup=False)) == "BLOCK"
    assert alpha_shield_gate(Action(name="prod", modifies_prod=True, has_tests=False)) == "BLOCK"
    assert alpha_shield_gate(Action(name="uncertain", confidence=0.5)) == "REVIEW"
    assert alpha_shield_gate(Action(name="safe", confidence=0.9)) == "ALLOW"


def test_scanner_selector_and_patch_plan_choose_missing_reports(tmp_path) -> None:
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "assembler_agent.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_example.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    state = scan_repo(tmp_path)
    task = select_highest_leverage_task(state)
    plan = plan_minimal_patch(state, task)

    assert task.title == "Create operating report files"
    assert "reports/daily_status.md" in task.suggested_files
    assert plan.rollback.startswith("Use `git checkout --")
    assert state.test_command == "pytest -q"


def test_apply_report_patch_is_idempotent(tmp_path) -> None:
    task = select_highest_leverage_task(scan_repo(tmp_path))

    first = apply_report_patch(tmp_path, task)
    second = apply_report_patch(tmp_path, task)

    assert "reports/next_actions.md" in first
    assert second == ()
    assert (tmp_path / "reports" / "daily_status.md").exists()
    assert "Queued by AssemblerAgent" in (tmp_path / "reports" / "next_actions.md").read_text(
        encoding="utf-8"
    )


def test_write_reflection_appends_jsonl_memory(tmp_path) -> None:
    entry = build_reflection_entry(
        goal="compound daily",
        action="suggest",
        result="selected task",
        tests="pytest -q",
        risk="ALLOW",
        lesson="verify first",
        next_best_action="run patch",
    )

    path = write_reflection(tmp_path, entry)
    payload = json.loads(path.read_text(encoding="utf-8").splitlines()[0])

    assert payload["goal"] == "compound daily"
    assert payload["action"] == "suggest"
    assert payload["risk"] == "ALLOW"
    assert payload["next_best_action"] == "run patch"


def test_suggest_mode_prints_required_report_sections() -> None:
    completed = subprocess.run(
        [sys.executable, "agents/assembler_agent.py", "--repo", ".", "--mode", "suggest"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "# Assembly Report" in completed.stdout
    assert "## Repo State" in completed.stdout
    assert "## Highest-Leverage Task" in completed.stdout
    assert "## Proposed Minimal Patch" in completed.stdout
    assert "## Test Command" in completed.stdout
    assert "## Risk" in completed.stdout
    assert "## Rollback" in completed.stdout

