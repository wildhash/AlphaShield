from dataclasses import dataclass
import numpy as np
from typing import Tuple, List

@dataclass
class RiskLimits:
    target_vol: float = 0.10
    max_monthly_dd: float = 0.03
    es95_limit: float = 0.04
    cr_floor: float = 1.30
    pos_cap: float = 0.25        # 25% per asset
    min_cash: float = 0.05       # 5% cash buffer
    turnover_budget: float = 0.20  # <= 20% of NAV per rebalance

def enforce_caps(weights: np.ndarray, limits: RiskLimits) -> np.ndarray:
    w = np.clip(weights, 0.0, limits.pos_cap)
    s = w.sum()
    return w / s if s > 1e-12 else w

def expected_shortfall(pnl_series: np.ndarray, alpha: float = 0.95) -> float:
    """Positive number == loss magnitude at ES level."""
    if pnl_series.size == 0:
        return 0.0
    q = np.quantile(pnl_series, 1 - alpha)
    tail = pnl_series[pnl_series <= q]
    if tail.size == 0:
        return 0.0
    return float(-tail.mean())

def check_risk_limits(
    current_cash_ratio: float,
    proposed_weights: np.ndarray,
    coverage_ratio_value: float,
    limits: RiskLimits
) -> Tuple[bool, List[str]]:
    violations = []
    if coverage_ratio_value < limits.cr_floor:
        violations.append(f"CR {coverage_ratio_value:.2f} < floor {limits.cr_floor:.2f}")
    if proposed_weights.max(initial=0.0) > limits.pos_cap + 1e-9:
        violations.append(f"Position cap exceeded (> {limits.pos_cap:.0%})")
    if current_cash_ratio < limits.min_cash - 1e-9:
        violations.append(f"Cash {current_cash_ratio:.1%} < min {limits.min_cash:.0%}")
    return len(violations) == 0, violations

def emergency_weights(n_assets: int, venue: str = "equities") -> np.ndarray:
    """
    Returns a defensive template as weights over the tradeable assets vector.
    For now: heavy cash -> we represent cash by shrinking all asset weights.
    """
    if n_assets == 0:
        return np.array([])
    # 70% cash equivalent -> scale risky allocations to 30%
    base = np.ones(n_assets, dtype=float)
    base = base / base.sum() if base.sum() > 0 else base
    return 0.30 * base  # remaining 70% is cash buffer handled at execution layer
