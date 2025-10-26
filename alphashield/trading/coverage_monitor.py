from __future__ import annotations

import math


def monthly_payment(principal: float, rate: float, term_months: int) -> float:
    """
    Compute the fixed monthly payment for an amortizing loan.
    
    Parameters:
        principal (float): Loan principal amount.
        rate (float): Annual interest rate expressed as a decimal (e.g., 0.05 for 5%).
        term_months (int): Loan term in months.
    
    Returns:
        float: Monthly payment amount. Returns 0.0 if term_months <= 0. If the monthly rate is effectively zero, returns principal divided by term_months.
    """
    if term_months <= 0:
        return 0.0
    r = rate / 12.0
    if abs(r) < 1e-12:
        return principal / term_months
    return principal * (r * (1 + r) ** term_months) / ((1 + r) ** term_months - 1)


def expected_monthly_return(nav: float, exp_return_assumption: float) -> float:
    # Continuous comp approximation for monthly
    """
    Estimate the expected monthly return from a net asset value using an annual return assumption.
    
    Parameters:
        nav (float): Net asset value.
        exp_return_assumption (float): Annual expected return rate as a decimal (for example, 0.10 for 10%).
    
    Returns:
        monthly_return (float): Expected monthly return amount (nav * annual rate / 12).
    """
    return nav * exp_return_assumption / 12.0


def coverage_ratio(nav: float, monthly_payment_amt: float, exp_return_assumption: float = 0.10) -> float:
    """
    Compute the ratio of expected monthly return from a net asset value to a monthly payment amount.
    
    Parameters:
        nav (float): Net asset value used to estimate expected return.
        monthly_payment_amt (float): Monthly payment amount to compare against; if less than or equal to zero the function returns positive infinity.
        exp_return_assumption (float): Annual expected return assumption as a decimal (e.g., 0.10 for 10%).
    
    Returns:
        float: Expected monthly return divided by `monthly_payment_amt`, or `float('inf')` if `monthly_payment_amt` <= 0.
    """
    if monthly_payment_amt <= 0:
        return float('inf')
    exp_monthly = expected_monthly_return(float(nav), float(exp_return_assumption))
    return float(exp_monthly / monthly_payment_amt)


def is_coverage_ok(cr: float, target_ratio: float = 1.3, emergency_ratio: float = 1.2) -> bool:
    """
    Determine whether a coverage ratio meets emergency and target thresholds.
    
    Parameters:
    	cr (float): Coverage ratio to evaluate.
    	target_ratio (float): Ratio at or above which coverage is considered acceptable.
    	emergency_ratio (float): Minimum critical ratio; values below this are immediately unacceptable.
    
    Returns:
    	True if `cr` is greater than or equal to `target_ratio` and not below `emergency_ratio`, `False` otherwise.
    """
    if cr < emergency_ratio:
        return False
    return cr >= target_ratio