# tests/rl/test_reward.py
from math import isclose

# If you named it differently, adjust import:
from alphashield.rl.reward import compute_reward

def test_reward_respects_fairness_and_compliance_gates():
    metrics_ok = {
        "wealth_delta": 0.6,
        "coverage_ratio": 1.3,
        "fairness": 0.8,
        "satisfaction": 0.7,
        "drawdown": 0.1,
        "anomaly": 0.0,
        "tax_risk": 0.0,
        "calibration": 1.0,
        "compliance_ok": True,
    }
    cfg = dict(alpha=.4, beta=.15, gamma=.15, delta=.10, lambda1=.10, lambda2=.05, lambda3=.05)
    r_ok = compute_reward(metrics_ok, cfg)
    assert r_ok > 0.0

    # Fairness below threshold or compliance fail → zero reward
    for bad in [
        dict(metrics_ok, fairness=0.3),
        dict(metrics_ok, compliance_ok=False),
    ]:
        r_bad = compute_reward(bad, cfg)
        assert isclose(r_bad, 0.0, abs_tol=1e-9)
