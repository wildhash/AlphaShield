from __future__ import annotations

from typing import Dict
import pandas as pd


TEMPLATES: dict[str, dict[str, float]] = {
    "risk_on": {"VTI": 0.70, "BND": 0.20, "VTIP": 0.10},
    "balanced": {"VTI": 0.50, "BND": 0.35, "VTIP": 0.15},
    "risk_off": {"VTI": 0.10, "BND": 0.70, "VTIP": 0.20},
    "bond_bias_plus": {"VTI": 0.35, "BND": 0.50, "VTIP": 0.15},
    "bond_bias_minus": {"VTI": 0.55, "BND": 0.30, "VTIP": 0.15},
}


def get_template(name: str) -> dict[str, float]:
    if name not in TEMPLATES:
        raise ValueError(f"unknown template: {name}")
    return dict(TEMPLATES[name])


def validate_template(weights: dict[str, float]) -> dict[str, float]:
    s = sum(max(0.0, float(w)) for w in weights.values())
    if s <= 0:
        raise ValueError("template must have positive weights")
    norm = {k: max(0.0, float(v)) / s for k, v in weights.items()}
    return norm


def apply_tilts(base: dict[str, float], tilts: dict[str, float] | None = None, tilt_strength: float = 0.1) -> dict[str, float]:
    if tilts is None or not tilts:
        return validate_template(base)
    w = base.copy()
    for k, sign in tilts.items():
        if k not in w:
            continue
        w[k] = max(0.0, w[k] + tilt_strength * float(sign))
    return validate_template(w)
