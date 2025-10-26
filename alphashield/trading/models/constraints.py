from __future__ import annotations

from typing import Dict, List, Tuple


def default_constraints() -> Dict:
    """Default portfolio constraints used by optimizers."""
    # Example sector limits mapping
    sector_limits: Dict[str, Tuple[List[int], float]] = {}
    return {
        "risk_aversion": 1.0,
        "max_weight": 0.20,
        "max_turnover": 0.30,
        "sector_limits": sector_limits,
    }
