import numpy as np
import pandas as pd

from alphashield.trading.coverage_monitor import monthly_payment, coverage_ratio, is_coverage_ok
from alphashield.trading.risk_manager import RiskManager


def pmt(rate_annual, n_months, principal):
    """
    Compute the fixed monthly payment for an amortizing loan given an annual interest rate, term, and principal.
    
    Parameters:
        rate_annual (float): Annual nominal interest rate expressed as a decimal (e.g., 0.08 for 8%).
        n_months (int): Total number of monthly payments (loan term in months).
        principal (float): Initial loan principal amount.
    
    Returns:
        monthly_payment (float): The fixed monthly payment amount.
    """
    r = rate_annual / 12.0
    if r == 0:
        return principal / n_months
    return principal * (r * (1 + r) ** n_months) / ((1 + r) ** n_months - 1)


def test_monthly_payment_matches_baseline():
    mp = monthly_payment(100000, 0.08, 36)
    assert abs(mp - pmt(0.08, 36, 100000)) < 1e-6


def test_coverage_ratio_thresholding():
    nav = 60000
    mp = monthly_payment(100000, 0.08, 36)
    cr = coverage_ratio(nav, mp, exp_return_assumption=0.10)
    assert isinstance(cr, float) and cr > 0
    assert is_coverage_ok(cr, target_ratio=1.3, emergency_ratio=1.2) in {True, False}


def test_risk_manager_defensive_on_breach():
    rm = RiskManager(max_drawdown=0.15)
    # Simulate returns with large drawdown
    vals = pd.Series([100, 110, 108, 90, 85, 84, 86])
    peak = vals.cummax()
    dd = float(((peak - vals) / peak).max())
    assert dd > 0.15
    decision = rm.emergency_mode_check(coverage_ratio=1.25, portfolio_drawdown=dd)
    assert decision.action in {"emergency", "defensive"}