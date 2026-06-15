from __future__ import annotations


def default_constraints() -> dict:
    """Default portfolio constraints used by optimizers."""
    # Example sector limits mapping
    sector_limits: dict[str, tuple[list[int], float]] = {}
    return {
        "risk_aversion": 1.0,
        "max_weight": 0.20,
        "max_turnover": 0.30,
        "sector_limits": sector_limits,
    }
