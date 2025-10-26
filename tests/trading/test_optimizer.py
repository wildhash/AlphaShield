import numpy as np
import pandas as pd
from alphashield.trading.portfolio_optimizer import PortfolioOptimizer, OptimizerConfig


def test_optimizer_handles_near_singular_and_box_constraints():
    idx = pd.bdate_range("2020-01-01", periods=260)
    # correlated returns for near-singularity
    rng = np.random.default_rng(0)
    base = rng.normal(0, 0.01, size=len(idx))
    r = pd.DataFrame({
        "VTI": base + rng.normal(0, 0.002, size=len(idx)),
        "BND": base + rng.normal(0, 0.002, size=len(idx)),
        "VTIP": base + rng.normal(0, 0.002, size=len(idx)),
    }, index=idx)
    mu = r.mean() * 252
    cfg = OptimizerConfig(risk_aversion=1.0, max_position=0.6, covariance="ledoit_wolf", method="closed_form", min_return=0.0)
    opt = PortfolioOptimizer(cfg)
    w, info = opt.optimize(mu, r)
    assert abs(w.sum() - 1.0) < 1e-6
    assert (w >= 0).all() and (w <= cfg.max_position + 1e-8).all()


def test_optimizer_min_return_fallback_to_risk_off():
    """
    Verifies the optimizer falls back to a risk-off solution when the configured minimum return cannot be met.
    
    Constructs low-expected-return asset series, configures the optimizer with high risk aversion and an unattainable `min_return`, runs optimization, and asserts that the solver either reports a "fallback_risk_off" status or succeeds ("ok") and that the resulting weights sum to 1 within numerical tolerance.
    """
    idx = pd.bdate_range("2020-01-01", periods=260)
    rng = np.random.default_rng(1)
    r = pd.DataFrame({
        "VTI": rng.normal(0.0001, 0.01, size=len(idx)),
        "BND": rng.normal(0.0001, 0.01, size=len(idx)),
        "VTIP": rng.normal(0.0001, 0.01, size=len(idx)),
    }, index=idx)
    mu = pd.Series({"VTI":0.0001*252, "BND":0.0001*252, "VTIP":0.0001*252})
    cfg = OptimizerConfig(risk_aversion=50.0, max_position=0.5, covariance="ledoit_wolf", method="closed_form", min_return=0.20)
    opt = PortfolioOptimizer(cfg)
    w, info = opt.optimize(mu, r)
    assert info.get("status") in {"fallback_risk_off","ok"}
    assert abs(w.sum() - 1.0) < 1e-6