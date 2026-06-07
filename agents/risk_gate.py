"""AlphaShield action gate for self-assembly work."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    """Minimal action contract evaluated by the AlphaShield gate."""

    name: str
    touches_money: bool = False
    dry_run: bool = True
    deletes_data: bool = False
    has_backup: bool = False
    modifies_prod: bool = False
    has_tests: bool = False
    confidence: float = 0.75


def alpha_shield_gate(action: Action) -> str:
    """Return BLOCK, REVIEW, or ALLOW for an action."""

    if action.touches_money and not action.dry_run:
        return "BLOCK"
    if action.deletes_data and not action.has_backup:
        return "BLOCK"
    if action.modifies_prod and not action.has_tests:
        return "BLOCK"
    if action.confidence < 0.75:
        return "REVIEW"
    return "ALLOW"

