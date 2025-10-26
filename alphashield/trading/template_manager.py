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
    """
    Retrieve a predefined weight template by name.
    
    Parameters:
        name (str): The template identifier to look up.
    
    Returns:
        dict[str, float]: A shallow copy of the template mapping asset tickers to their weights.
    
    Raises:
        ValueError: If no template exists with the given name.
    """
    if name not in TEMPLATES:
        raise ValueError(f"unknown template: {name}")
    return dict(TEMPLATES[name])


def validate_template(weights: dict[str, float]) -> dict[str, float]:
    """
    Normalize a mapping of asset weights by treating negative values as zero and scaling values to sum to 1.
    
    Parameters:
        weights (dict[str, float]): Mapping of asset identifiers to numeric weights. Negative weights are treated as zero before normalization.
    
    Returns:
        dict[str, float]: New mapping with the same keys where each value is the non-negative weight divided by the sum of all non-negative weights (sums to 1).
    
    Raises:
        ValueError: If the sum of non-negative weights is less than or equal to zero.
    """
    s = sum(max(0.0, float(w)) for w in weights.values())
    if s <= 0:
        raise ValueError("template must have positive weights")
    norm = {k: max(0.0, float(v)) / s for k, v in weights.items()}
    return norm


def apply_tilts(base: dict[str, float], tilts: dict[str, float] | None = None, tilt_strength: float = 0.1) -> dict[str, float]:
    """
    Apply per-asset tilt adjustments to a base weight map and return a validated, normalized weight map.
    
    Parameters:
        base (dict[str, float]): Base asset weights keyed by asset identifier.
        tilts (dict[str, float] | None): Mapping of asset identifiers to tilt signs (positive to increase, negative to decrease). Keys not present in `base` are ignored. If `None` or empty, `base` is validated and normalized without changes.
        tilt_strength (float): Magnitude applied to each tilt sign before adding to the corresponding base weight.
    
    Returns:
        dict[str, float]: Normalized weights (values >= 0 and summing to 1) after applying tilts.
    
    Raises:
        ValueError: If the validated weight set has a non-positive sum (e.g., all weights are zero after clamping).
    """
    if tilts is None or not tilts:
        return validate_template(base)
    w = base.copy()
    for k, sign in tilts.items():
        if k not in w:
            continue
        w[k] = max(0.0, w[k] + tilt_strength * float(sign))
    return validate_template(w)