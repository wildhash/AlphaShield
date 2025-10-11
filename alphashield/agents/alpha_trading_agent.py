"""Alpha Trading agent for algorithmic investment of 60% loan funds."""
from typing import Dict, Any, List
import random
from datetime import datetime

from alphashield.agents.base_agent import BaseAgent
from alphashield.models.loan import Loan


class AlphaTradingAgent(BaseAgent):
    """Agent responsible for investing 60% of loan to generate returns."""
    
    def __init__(self, db_client, embeddings_client=None):
        super().__init__("AlphaTrading", db_client, embeddings_client)
        
    def invest_loan_funds(self, loan_id: str, strategy: str = "balanced") -> Dict[str, Any]:
        """Invest the 60% allocation algorithmically.
        
        Args:
            loan_id: Loan whose funds to invest
            strategy: Investment strategy (conservative, balanced, aggressive)
            
        Returns:
            Investment allocation and expected returns.
        """
        loan_data = self.get_loan(loan_id)
        if not loan_data:
            return {'error': 'Loan not found'}
        
        loan = Loan.from_dict(loan_data)
        investment_amount = loan.split.investment_amount
        
        # Define strategy allocations
        strategies = {
            'conservative': {
                'bonds': 0.6,
                'index_funds': 0.3,
                'dividend_stocks': 0.1,
                'expected_annual_return': 0.06
            },
            'balanced': {
                'bonds': 0.3,
                'index_funds': 0.4,
                'dividend_stocks': 0.2,
                'growth_stocks': 0.1,
                'expected_annual_return': 0.10
            },
            'aggressive': {
                'index_funds': 0.3,
                'growth_stocks': 0.4,
                'dividend_stocks': 0.2,
                'alternatives': 0.1,
                'expected_annual_return': 0.15
            }
        }
        
        allocation = strategies.get(strategy, strategies['balanced'])
        
        # Calculate investment allocations
        portfolio = {}
        for asset_class, percentage in allocation.items():
            if asset_class != 'expected_annual_return':
                portfolio[asset_class] = investment_amount * percentage
        
        # Calculate monthly payment coverage target
        monthly_payment_needed = loan.monthly_payment
        expected_monthly_return = (investment_amount * allocation['expected_annual_return']) / 12
        coverage_ratio = expected_monthly_return / monthly_payment_needed if monthly_payment_needed > 0 else 0
        
        investment_plan = {
            'loan_id': loan_id,
            'investment_amount': investment_amount,
            'strategy': strategy,
            'portfolio': portfolio,
            'expected_annual_return': allocation['expected_annual_return'],
            'expected_monthly_return': expected_monthly_return,
            'monthly_payment_needed': monthly_payment_needed,
            'coverage_ratio': coverage_ratio,
            'status': 'sufficient' if coverage_ratio >= 1.0 else 'needs_monitoring'
        }
        
        # Store investment plan
        self.store_context('investment_plan', investment_plan, generate_embedding=True)
        
        # Record initial investment transaction
        self.db.store_transaction({
            'loan_id': loan_id,
            'type': 'investment',
            'amount': investment_amount,
            'details': investment_plan
        })
        
        self.log_action('invest_funds', investment_plan)
        
        return investment_plan
    
    def process(self, loan_id: str, **kwargs) -> Dict[str, Any]:
        """Process investment returns and rebalancing.
        
        Args:
            loan_id: Loan to process
            
        Returns:
            Investment performance metrics.
        """
        loan_data = self.get_loan(loan_id)
        if not loan_data:
            return {'error': 'Loan not found'}
        
        loan = Loan.from_dict(loan_data)
        
        # Get investment transactions
        transactions = self.db.get_transactions(loan_id=loan_id, transaction_type='investment')
        
        if not transactions:
            return {'message': 'No investment yet', 'action': 'invest_first'}
        
        # Simulate monthly returns (in production, would connect to trading APIs)
        # Using random with bounds to simulate realistic returns
        monthly_return_rate = random.uniform(0.005, 0.015)  # 0.5% to 1.5% monthly
        current_value = loan.investment_balance * (1 + monthly_return_rate)
        returns = current_value - loan.investment_balance
        
        # Update investment balance
        self.db.update_loan(loan_id, {'investment_balance': current_value})
        
        # Record return transaction
        self.db.store_transaction({
            'loan_id': loan_id,
            'type': 'investment_return',
            'amount': returns,
            'details': {
                'previous_balance': loan.investment_balance,
                'new_balance': current_value,
                'return_rate': monthly_return_rate,
            }
        })
        
        performance = {
            'loan_id': loan_id,
            'investment_balance': current_value,
            'period_return': returns,
            'period_return_rate': monthly_return_rate,
            'total_returns': current_value - loan.split.investment_amount,
            'performance': 'positive' if returns > 0 else 'negative'
        }
        
        self.store_context('investment_performance', performance, generate_embedding=True)
        
        return performance
    
    def assess_risk_capacity(self, loan_id: str) -> Dict[str, Any]:
        """Assess portfolio risk and capacity to cover payments.
        
        Args:
            loan_id: Loan to assess
            
        Returns:
            Risk capacity assessment.
        """
        loan_data = self.get_loan(loan_id)
        if not loan_data:
            return {'error': 'Loan not found'}
        
        loan = Loan.from_dict(loan_data)
        
        # Calculate months of coverage available
        months_covered = loan.investment_balance / loan.monthly_payment if loan.monthly_payment > 0 else 0
        
        risk_level = 'low' if months_covered >= 6 else 'medium' if months_covered >= 3 else 'high'
        
        assessment = {
            'loan_id': loan_id,
            'investment_balance': loan.investment_balance,
            'monthly_payment': loan.monthly_payment,
            'months_covered': months_covered,
            'risk_level': risk_level,
            'recommendation': 'maintain' if risk_level == 'low' else 'increase_returns'
        }
        
        self.store_context('risk_capacity', assessment, generate_embedding=True)
        
        return assessment
