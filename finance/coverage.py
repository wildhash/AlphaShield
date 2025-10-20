from dataclasses import dataclass

@dataclass
class LoanTerms:
    principal: float
    annual_rate: float  # e.g., 0.12 for 12%
    months: int

def monthly_payment(terms: LoanTerms) -> float:
    r = terms.annual_rate / 12.0
    if r == 0:
        return terms.principal / max(terms.months, 1)
    num = terms.principal * r * (1 + r) ** terms.months
    den = (1 + r) ** terms.months - 1
    return num / max(den, 1e-12)

def coverage_ratio(expected_annual_return: float, invested_amount: float, terms: LoanTerms) -> float:
    """CR = expected monthly return / required monthly payment."""
    mp = monthly_payment(terms)
    emr = invested_amount * (expected_annual_return / 12.0)
    return emr / max(mp, 1e-12)
