"""Tests for agent output schemas."""
import unittest
from datetime import datetime

from alphashield.schemas.agent_schemas import (
    LenderAgentOutput,
    AlphaTradingAgentOutput,
    SpendingGuardAgentOutput,
    BudgetAnalyzerAgentOutput,
    TaxOptimizerAgentOutput,
    ContractReviewAgentOutput,
    validate_schema,
)


class TestLenderAgentOutput(unittest.TestCase):
    """Test LenderAgent output schema."""
    
    def test_minimal_schema(self):
        """Test minimal required fields."""
        output = LenderAgentOutput(
            borrower_id="borrower_123"
        )
        
        self.assertEqual(output.borrower_id, "borrower_123")
        self.assertFalse(output.approved)
        self.assertEqual(len(output.approval_conditions), 0)
    
    def test_complete_schema(self):
        """Test complete schema with all fields."""
        output = LenderAgentOutput(
            borrower_id="borrower_123",
            loan_id="loan_456",
            credit_score=720,
            credit_history_length_years=5.5,
            total_credit_accounts=8,
            derogatory_marks=0,
            payment_history={'on_time_count': 24, 'late_count': 0, 'missed_count': 0},
            credit_utilization=0.30,
            verified_income={'annual_gross': 60000, 'monthly_gross': 5000, 'monthly_net': 3800},
            employment_length_years=3.0,
            debt_to_income_ratio=0.35,
            spending_to_income_ratio=0.65,
            default_risk_score=0.15,
            approved_loan_amount_max=15000,
            approved=True
        )
        
        self.assertTrue(output.approved)
        self.assertEqual(output.credit_score, 720)
        self.assertEqual(output.default_risk_score, 0.15)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        output = LenderAgentOutput(
            borrower_id="borrower_123",
            credit_score=720
        )
        
        data = output.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data['borrower_id'], "borrower_123")
        self.assertEqual(data['credit_score'], 720)


class TestAlphaTradingAgentOutput(unittest.TestCase):
    """Test AlphaTradingAgent output schema."""
    
    def test_minimal_schema(self):
        """Test minimal required fields."""
        output = AlphaTradingAgentOutput(
            loan_id="loan_123"
        )
        
        self.assertEqual(output.loan_id, "loan_123")
        self.assertEqual(output.cash_balance, 0.0)
        self.assertEqual(output.risk_level, "medium")
    
    def test_portfolio_positions(self):
        """Test with portfolio positions."""
        positions = [
            {
                'symbol': 'AAPL',
                'shares': 10,
                'cost_basis': 150.00,
                'current_price': 180.00,
                'market_value': 1800.00,
                'unrealized_gain_loss': 300.00,
                'holding_period': 'long_term',
                'tax_status': 'long_term_gains'
            }
        ]
        
        output = AlphaTradingAgentOutput(
            loan_id="loan_123",
            portfolio_positions=positions,
            cash_balance=1000.0,
            total_portfolio_value=2800.0,
            asset_allocation={'stocks_pct': 64.3, 'cash_pct': 35.7},
            tax_bracket="22%"
        )
        
        self.assertEqual(len(output.portfolio_positions), 1)
        self.assertEqual(output.portfolio_positions[0]['symbol'], 'AAPL')
        self.assertEqual(output.tax_bracket, "22%")


class TestSpendingGuardAgentOutput(unittest.TestCase):
    """Test SpendingGuardAgent output schema."""
    
    def test_minimal_schema(self):
        """Test minimal required fields."""
        output = SpendingGuardAgentOutput(
            borrower_id="borrower_123"
        )
        
        self.assertEqual(output.borrower_id, "borrower_123")
        self.assertEqual(output.alert_level, "normal")
        self.assertFalse(output.rapid_depletion_risk)
    
    def test_with_anomalies(self):
        """Test with detected anomalies."""
        anomalies = [
            {
                'date': '2024-01-15',
                'amount': 5000.00,
                'merchant': 'Luxury Store',
                'category': 'luxury',
                'threshold_exceeded_by': 4500.00
            }
        ]
        
        output = SpendingGuardAgentOutput(
            borrower_id="borrower_123",
            loan_id="loan_456",
            total_transactions=120,
            category_spending={'food': 500, 'luxury': 5000},
            anomalies_detected=anomalies,
            anomaly_count=1,
            alert_level="high",
            alert_reasons=["Unusual luxury spending detected"]
        )
        
        self.assertEqual(output.anomaly_count, 1)
        self.assertEqual(output.alert_level, "high")
        self.assertEqual(len(output.anomalies_detected), 1)


class TestBudgetAnalyzerAgentOutput(unittest.TestCase):
    """Test BudgetAnalyzerAgent output schema."""
    
    def test_minimal_schema(self):
        """Test minimal required fields."""
        output = BudgetAnalyzerAgentOutput(
            borrower_id="borrower_123"
        )
        
        self.assertEqual(output.borrower_id, "borrower_123")
        self.assertEqual(output.budget_health_status, "unknown")
    
    def test_complete_budget_analysis(self):
        """Test complete budget analysis."""
        output = BudgetAnalyzerAgentOutput(
            borrower_id="borrower_123",
            loan_id="loan_456",
            monthly_gross_income=5000.0,
            monthly_net_income=3800.0,
            monthly_expenses_by_category={
                'housing': 1500,
                'utilities': 200,
                'food': 400,
                'transportation': 300
            },
            average_monthly_spending=2400.0,
            needs_spending=2400.0,
            wants_spending=600.0,
            savings_rate=0.20,
            recommended_needs=2500.0,
            recommended_wants=1500.0,
            recommended_savings=1000.0,
            expense_ratio=0.63,
            debt_service_ratio=0.10,
            budget_health_status="healthy",
            payment_affordable=True,
            affordability_score=0.85
        )
        
        self.assertEqual(output.budget_health_status, "healthy")
        self.assertTrue(output.payment_affordable)
        self.assertEqual(output.affordability_score, 0.85)


class TestTaxOptimizerAgentOutput(unittest.TestCase):
    """Test TaxOptimizerAgent output schema."""
    
    def test_minimal_schema(self):
        """Test minimal required fields."""
        output = TaxOptimizerAgentOutput(
            borrower_id="borrower_123"
        )
        
        self.assertEqual(output.borrower_id, "borrower_123")
        self.assertEqual(output.estimated_tax_savings, 0.0)
    
    def test_with_optimization_opportunities(self):
        """Test with tax optimization strategies."""
        short_term = [
            {
                'strategy': 'tax_loss_harvesting',
                'description': 'Harvest $2000 in losses',
                'potential_savings': 440.00,
                'timeline': '1 month'
            }
        ]
        
        long_term = [
            {
                'strategy': 'increase_401k',
                'description': 'Max out 401k contributions',
                'potential_savings': 4950.00,
                'timeline': '12 months'
            }
        ]
        
        output = TaxOptimizerAgentOutput(
            borrower_id="borrower_123",
            loan_id="loan_456",
            marginal_tax_bracket="22%",
            projected_w2_wages=60000.0,
            retirement_contribution_ytd=5000.0,
            retirement_contribution_room=17500.0,
            short_term_strategies=short_term,
            long_term_strategies=long_term,
            total_potential_savings=5390.00
        )
        
        self.assertEqual(output.marginal_tax_bracket, "22%")
        self.assertEqual(len(output.short_term_strategies), 1)
        self.assertEqual(len(output.long_term_strategies), 1)
        self.assertEqual(output.total_potential_savings, 5390.00)


class TestContractReviewAgentOutput(unittest.TestCase):
    """Test ContractReviewAgent output schema."""
    
    def test_minimal_schema(self):
        """Test minimal required fields."""
        output = ContractReviewAgentOutput(
            loan_id="loan_123"
        )
        
        self.assertEqual(output.loan_id, "loan_123")
        self.assertFalse(output.approved)
        self.assertEqual(output.risk_score, 0.5)
    
    def test_favorable_contract(self):
        """Test favorable contract review."""
        output = ContractReviewAgentOutput(
            loan_id="loan_123",
            borrower_id="borrower_456",
            principal_amount=10000.0,
            stated_interest_rate=8.0,
            annual_percentage_rate=8.5,
            loan_term_months=36,
            monthly_payment=313.36,
            fees={'origination': 100.0},
            total_fees=100.0,
            loan_features={'fixed_rate': True, 'prepayment_allowed': True},
            borrower_credit_score=720,
            payment_to_income_ratio=0.10,
            affordability_rating="excellent",
            competitive_position="excellent",
            positive_terms=["Low interest rate", "No prepayment penalty"],
            truth_in_lending_compliant=True,
            state_usury_laws_compliant=True,
            mandatory_disclosures_present=True,
            approved=True,
            overall_rating="excellent"
        )
        
        self.assertTrue(output.approved)
        self.assertEqual(output.overall_rating, "excellent")
        self.assertEqual(output.competitive_position, "excellent")
        self.assertTrue(output.truth_in_lending_compliant)
    
    def test_predatory_contract(self):
        """Test predatory contract detection."""
        output = ContractReviewAgentOutput(
            loan_id="loan_123",
            principal_amount=10000.0,
            stated_interest_rate=24.0,
            annual_percentage_rate=28.5,
            fees={'origination': 1000.0, 'late_payment': 100.0},
            total_fees=1100.0,
            predatory_indicators=["Excessive interest rate", "High fees"],
            concerning_terms=["Prepayment penalty"],
            competitive_position="predatory",
            approved=False,
            overall_rating="poor",
            risk_score=0.9
        )
        
        self.assertFalse(output.approved)
        self.assertEqual(output.overall_rating, "poor")
        self.assertEqual(output.competitive_position, "predatory")
        self.assertGreater(len(output.predatory_indicators), 0)


class TestSchemaValidation(unittest.TestCase):
    """Test schema validation function."""
    
    def test_valid_schema(self):
        """Test validation of valid schema."""
        data = {
            'borrower_id': 'borrower_123',
            'credit_score': 720
        }
        
        self.assertTrue(validate_schema(data, LenderAgentOutput))
    
    def test_invalid_schema(self):
        """Test validation of invalid schema."""
        data = {
            'invalid_field': 'value'
        }
        
        with self.assertRaises(ValueError):
            validate_schema(data, LenderAgentOutput)


if __name__ == '__main__':
    unittest.main()
