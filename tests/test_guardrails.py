import numpy as np
from trading_core.risk.guardrails import RiskLimits, enforce_caps, check_risk_limits

def test_enforce_caps_and_limits():
    limits = RiskLimits(pos_cap=0.25, cr_floor=1.3, min_cash=0.05)
    # Use weights that when capped and renormalized still respect the cap
    w = np.array([0.25, 0.25, 0.25, 0.25])
    w_cap = enforce_caps(w, limits)
    assert (w_cap <= limits.pos_cap + 1e-12).all()
    assert abs(w_cap.sum() - 1.0) < 1e-9

    is_ok, viol = check_risk_limits(
        current_cash_ratio=0.10, proposed_weights=w_cap, coverage_ratio_value=1.4, limits=limits
    )
    assert is_ok
    assert viol == []
