"""Tests for agents with mocked database."""
import unittest
from unittest.mock import MagicMock, patch
from alphashield.agents.lender_agent import LenderAgent
from alphashield.agents.alpha_trading_agent import AlphaTradingAgent
from alphashield.agents.spending_guard_agent import SpendingGuardAgent
from alphashield.agents.budget_analyzer_agent import BudgetAnalyzerAgent
from alphashield.agents.tax_optimizer_agent import TaxOptimizerAgent
from alphashield.agents.contract_review_agent import ContractReviewAgent


class TestLenderAgent(unittest.TestCase):
    """Test Lender agent functionality."""
    
    def setUp(self):
        """Set up mock database."""
        self.mock_db = MagicMock()
        self.agent = LenderAgent(self.mock_db)
    
    def test_agent_initialization(self):
        """Test agent is initialized correctly."""
        self.assertEqual(self.agent.name, "Lender")
        self.assertIsNotNone(self.agent.db)
    
    def test_originate_loan(self):
        """Test loan origination."""
        self.mock_db.store_loan.return_value = "loan_123"
        
        loan_id = self.agent.originate_loan(
            borrower_id="borrower_456",
            principal=10000,
            interest_rate=8.0,
            term_months=36
        )
        
        self.assertEqual(loan_id, "loan_123")
        self.mock_db.store_loan.assert_called_once()
        
        # Verify loan data structure
        call_args = self.mock_db.store_loan.call_args[0][0]
        self.assertEqual(call_args['borrower_id'], "borrower_456")
        self.assertEqual(call_args['principal'], 10000)
        self.assertEqual(call_args['interest_rate'], 8.0)
        # Verify 60/40 split
        self.assertAlmostEqual(call_args['split']['investment_amount'], 6000)
        self.assertAlmostEqual(call_args['split']['borrower_amount'], 4000)


class TestAlphaTradingAgent(unittest.TestCase):
    """Test Alpha Trading agent functionality."""
    
    def setUp(self):
        """Set up mock database."""
        self.mock_db = MagicMock()
        self.agent = AlphaTradingAgent(self.mock_db)
    
    def test_agent_initialization(self):
        """Test agent is initialized correctly."""
        self.assertEqual(self.agent.name, "AlphaTrading")
    
    def test_investment_strategies(self):
        """Test different investment strategies."""
        # Mock loan data
        self.mock_db.get_loan.return_value = {
            'borrower_id': 'test',
            'principal': 10000,
            'interest_rate': 8.0,
            'term_months': 36,
            'split': {
                'investment_amount': 6000,
                'borrower_amount': 4000,
                'total_amount': 10000,
            },
            'monthly_payment': 313.36,
            'status': 'active',
        }
        
        strategies = ['conservative', 'balanced', 'aggressive']
        
        for strategy in strategies:
            result = self.agent.invest_loan_funds("loan_123", strategy=strategy)
            
            self.assertEqual(result['strategy'], strategy)
            self.assertEqual(result['investment_amount'], 6000)
            self.assertIn('portfolio', result)
            self.assertIn('expected_annual_return', result)


class TestSpendingGuardAgent(unittest.TestCase):
    """Test Spending Guard agent functionality."""
    
    def setUp(self):
        """Set up mock database."""
        self.mock_db = MagicMock()
        self.agent = SpendingGuardAgent(self.mock_db)
    
    def test_agent_initialization(self):
        """Test agent is initialized correctly."""
        self.assertEqual(self.agent.name, "SpendingGuard")
    
    def test_normal_spending_analysis(self):
        """Test analysis with normal spending."""
        transactions = [
            {'amount': 50, 'category': 'food'},
            {'amount': 60, 'category': 'food'},
            {'amount': 45, 'category': 'food'},
            {'amount': 80, 'category': 'entertainment'},
        ]
        
        result = self.agent.analyze_spending("borrower_123", transactions)
        
        self.assertEqual(result['borrower_id'], "borrower_123")
        self.assertEqual(result['total_transactions'], 4)
        self.assertIn('total_spending', result)
        self.assertIn('anomaly_detected', result)
    
    def test_anomaly_detection(self):
        """Test detection of spending anomalies."""
        transactions = [
            {'amount': 50, 'category': 'food'},
            {'amount': 55, 'category': 'food'},
            {'amount': 60, 'category': 'food'},
            {'amount': 5000, 'category': 'luxury'},  # Anomaly
        ]
        
        result = self.agent.analyze_spending("borrower_123", transactions)
        
        # Should detect the $5000 luxury purchase as anomaly
        self.assertGreater(result['anomalies_detected'], 0)


class TestBudgetAnalyzerAgent(unittest.TestCase):
    """Test Budget Analyzer agent functionality."""
    
    def setUp(self):
        """Set up mock database."""
        self.mock_db = MagicMock()
        self.agent = BudgetAnalyzerAgent(self.mock_db)
    
    def test_agent_initialization(self):
        """Test agent is initialized correctly."""
        self.assertEqual(self.agent.name, "BudgetAnalyzer")
    
    def test_healthy_budget_analysis(self):
        """Test analysis of a healthy budget."""
        income = 5000
        expenses = {
            'housing': 1500,
            'utilities': 200,
            'food': 400,
            'transportation': 300,
            'insurance': 200,
        }
        
        result = self.agent.analyze_budget("borrower_123", income, expenses)
        
        self.assertEqual(result['monthly_income'], 5000)
        total_exp = sum(expenses.values())
        self.assertEqual(result['total_expenses'], total_exp)
        self.assertGreater(result['discretionary_income'], 0)
        self.assertIn('budget_health', result)
    
    def test_unhealthy_budget_analysis(self):
        """Test analysis of an unhealthy budget."""
        income = 3000
        expenses = {
            'housing': 1500,
            'utilities': 300,
            'food': 500,
            'transportation': 400,
            'insurance': 250,
            'other': 500,
        }
        
        result = self.agent.analyze_budget("borrower_123", income, expenses)
        
        # Total expenses > 90% of income should trigger warnings
        self.assertGreater(len(result['warnings']), 0)
        self.assertIn(result['budget_health'], ['concerning', 'critical'])


class TestTaxOptimizerAgent(unittest.TestCase):
    """Test Tax Optimizer agent functionality."""
    
    def setUp(self):
        """Set up mock database."""
        self.mock_db = MagicMock()
        self.agent = TaxOptimizerAgent(self.mock_db)
    
    def test_agent_initialization(self):
        """Test agent is initialized correctly."""
        self.assertEqual(self.agent.name, "TaxOptimizer")
    
    def test_tax_calculation(self):
        """Test basic tax calculation."""
        income = 60000
        deductions = {
            'retirement': 5000,
            'charitable': 1000,
        }
        
        result = self.agent.analyze_tax_situation(
            "borrower_123", income, deductions, "single"
        )
        
        self.assertEqual(result['annual_income'], 60000)
        self.assertIn('estimated_tax', result)
        self.assertIn('effective_rate', result)
        self.assertIn('optimization_opportunities', result)


class TestContractReviewAgent(unittest.TestCase):
    """Test Contract Review agent functionality."""
    
    def setUp(self):
        """Set up mock database."""
        self.mock_db = MagicMock()
        self.agent = ContractReviewAgent(self.mock_db)
    
    def test_agent_initialization(self):
        """Test agent is initialized correctly."""
        self.assertEqual(self.agent.name, "ContractReview")
    
    def test_favorable_contract_review(self):
        """Test review of favorable contract terms."""
        self.mock_db.get_loan.return_value = {
            'principal': 10000,
            'interest_rate': 8.0,
            'term_months': 36,
            'monthly_payment': 313.36,
        }
        
        contract_terms = {
            'interest_rate': 8.0,
            'term_months': 36,
            'fees': {'origination': 100},
            'penalties': {'prepayment': 0, 'late_payment': 15},
        }
        
        result = self.agent.review_loan_terms("loan_123", contract_terms)
        
        self.assertEqual(result['stated_interest_rate'], 8.0)
        self.assertIn('overall_rating', result)
        # 8% rate should be considered favorable
        self.assertTrue(result['recommended'])
    
    def test_predatory_contract_review(self):
        """Test review of predatory contract terms."""
        self.mock_db.get_loan.return_value = {
            'principal': 10000,
            'interest_rate': 24.0,
            'term_months': 36,
            'monthly_payment': 398.89,
        }
        
        contract_terms = {
            'interest_rate': 24.0,
            'term_months': 36,
            'fees': {'origination': 1000},  # 10% fee
            'penalties': {'prepayment': 500, 'late_payment': 100},
        }
        
        result = self.agent.review_loan_terms("loan_123", contract_terms)
        
        self.assertEqual(result['stated_interest_rate'], 24.0)
        # Should flag high interest and fees as issues
        self.assertGreater(len(result['issues']), 0)
        self.assertFalse(result['recommended'])


if __name__ == '__main__':
    unittest.main()
