from __future__ import annotations

import math


def monthly_payment(principal: float, rate: float, term_months: int) -> float:
    if term_months <= 0:
        return 0.0
    r = rate / 12.0
    if abs(r) < 1e-12:
        return principal / term_months
    return principal * (r * (1 + r) ** term_months) / ((1 + r) ** term_months - 1)


def expected_monthly_return(nav: float, exp_return_assumption: float) -> float:
    # Continuous comp approximation for monthly
    return nav * exp_return_assumption / 12.0


def coverage_ratio(nav: float, monthly_payment_amt: float, exp_return_assumption: float = 0.10) -> float:
    if monthly_payment_amt <= 0:
        return float('inf')
    exp_monthly = expected_monthly_return(float(nav), float(exp_return_assumption))
    return float(exp_monthly / monthly_payment_amt)


def is_coverage_ok(cr: float, target_ratio: float = 1.3, emergency_ratio: float = 1.2) -> bool:
    if cr < emergency_ratio:
        return False
    return cr >= target_ratio
