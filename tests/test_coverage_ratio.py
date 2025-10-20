from finance.coverage import LoanTerms, monthly_payment, coverage_ratio

def test_monthly_payment_and_cr():
    terms = LoanTerms(principal=10000, annual_rate=0.12, months=36)
    mp = monthly_payment(terms)
    assert mp > 0
    # Suppose we expect 10% annual return on $6000 invested
    cr = coverage_ratio(0.10, 6000.0, terms)
    assert cr > 0
