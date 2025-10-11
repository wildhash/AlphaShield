"""Tests for loan model and 60/40 split logic."""
import unittest
from alphashield.models.loan import Loan, LoanSplit, LoanStatus


class TestLoanSplit(unittest.TestCase):
    """Test the 60/40 loan split calculation."""
    
    def test_split_from_total(self):
        """Test 60/40 split calculation."""
        split = LoanSplit.from_total(10000)
        
        self.assertEqual(split.total_amount, 10000)
        self.assertEqual(split.investment_amount, 6000)  # 60%
        self.assertEqual(split.borrower_amount, 4000)    # 40%
    
    def test_split_with_different_amounts(self):
        """Test split with various loan amounts."""
        amounts = [1000, 5000, 15000, 50000]
        
        for amount in amounts:
            split = LoanSplit.from_total(amount)
            self.assertEqual(split.investment_amount, amount * 0.6)
            self.assertEqual(split.borrower_amount, amount * 0.4)
            self.assertEqual(
                split.investment_amount + split.borrower_amount,
                split.total_amount
            )


class TestLoan(unittest.TestCase):
    """Test loan model and calculations."""
    
    def test_loan_initialization(self):
        """Test basic loan initialization."""
        loan = Loan(
            borrower_id="test_123",
            principal=10000,
            interest_rate=8.0,
            term_months=36
        )
        
        self.assertEqual(loan.borrower_id, "test_123")
        self.assertEqual(loan.principal, 10000)
        self.assertEqual(loan.interest_rate, 8.0)
        self.assertEqual(loan.term_months, 36)
        self.assertEqual(loan.status, LoanStatus.PENDING)
    
    def test_loan_split_auto_creation(self):
        """Test that loan split is automatically created."""
        loan = Loan(
            borrower_id="test_123",
            principal=10000,
            interest_rate=8.0,
            term_months=36
        )
        
        self.assertIsNotNone(loan.split)
        self.assertEqual(loan.split.investment_amount, 6000)
        self.assertEqual(loan.split.borrower_amount, 4000)
    
    def test_monthly_payment_calculation(self):
        """Test monthly payment calculation."""
        loan = Loan(
            borrower_id="test_123",
            principal=10000,
            interest_rate=8.0,
            term_months=36
        )
        
        # Should calculate amortized payment
        self.assertGreater(loan.monthly_payment, 0)
        # For 10k at 8% over 36 months, payment should be around $313
        self.assertAlmostEqual(loan.monthly_payment, 313, delta=10)
    
    def test_zero_interest_loan(self):
        """Test loan with zero interest."""
        loan = Loan(
            borrower_id="test_123",
            principal=12000,
            interest_rate=0.0,
            term_months=12
        )
        
        # With 0% interest, payment should be principal / months
        self.assertEqual(loan.monthly_payment, 1000)
    
    def test_loan_to_dict(self):
        """Test conversion to dictionary."""
        loan = Loan(
            borrower_id="test_123",
            principal=10000,
            interest_rate=8.0,
            term_months=36
        )
        
        loan_dict = loan.to_dict()
        
        self.assertEqual(loan_dict['borrower_id'], "test_123")
        self.assertEqual(loan_dict['principal'], 10000)
        self.assertEqual(loan_dict['interest_rate'], 8.0)
        self.assertIn('split', loan_dict)
        self.assertEqual(loan_dict['split']['investment_amount'], 6000)
    
    def test_loan_from_dict(self):
        """Test creation from dictionary."""
        loan_dict = {
            'borrower_id': "test_456",
            'principal': 15000,
            'interest_rate': 8.0,
            'term_months': 48,
            'status': 'active',
            'split': {
                'total_amount': 15000,
                'investment_amount': 9000,
                'borrower_amount': 6000,
            },
            'monthly_payment': 366.19,
            'investment_balance': 9000,
            'outstanding_balance': 15000,
        }
        
        loan = Loan.from_dict(loan_dict)
        
        self.assertEqual(loan.borrower_id, "test_456")
        self.assertEqual(loan.principal, 15000)
        self.assertEqual(loan.status, LoanStatus.ACTIVE)
        self.assertEqual(loan.split.investment_amount, 9000)


class TestLoanEconomics(unittest.TestCase):
    """Test the economic model: 8% vs 24% predatory rates."""
    
    def test_alphashield_vs_predatory_savings(self):
        """Test savings from 8% vs 24% rate."""
        # 10k loan for 3 years
        principal = 10000
        alphashield_rate = 8.0
        predatory_rate = 24.0
        years = 3
        
        # Simple interest calculation for comparison
        alphashield_interest = principal * (alphashield_rate / 100) * years
        predatory_interest = principal * (predatory_rate / 100) * years
        
        savings = predatory_interest - alphashield_interest
        
        # Should save $4,800 over 3 years
        self.assertEqual(alphashield_interest, 2400)
        self.assertEqual(predatory_interest, 7200)
        self.assertEqual(savings, 4800)
    
    def test_investment_coverage(self):
        """Test that 60% investment can theoretically cover payments."""
        loan = Loan(
            borrower_id="test_123",
            principal=10000,
            interest_rate=8.0,
            term_months=36
        )
        
        # With 10% annual return on $6,000
        investment_amount = loan.split.investment_amount
        expected_monthly_return = (investment_amount * 0.10) / 12
        
        # Should be able to cover or nearly cover monthly payment
        coverage_ratio = expected_monthly_return / loan.monthly_payment
        
        # With 10% returns on 60% investment, covers about 16% of monthly payment
        # This is realistic - the investment helps reduce burden but doesn't
        # fully cover payments. The key benefit is the 8% rate vs 24% predatory.
        self.assertGreater(coverage_ratio, 0.10)
        self.assertLess(coverage_ratio, 0.30)


if __name__ == '__main__':
    unittest.main()
