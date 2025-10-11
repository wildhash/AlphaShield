"""Lender agent for loan origination and portfolio management."""
from typing import Dict, Any
from alphashield.agents.base_agent import BaseAgent
from alphashield.models.loan import Loan, LoanStatus


class LenderAgent(BaseAgent):
    """Agent responsible for loan origination and portfolio management."""
    
    def __init__(self, db_client, embeddings_client=None):
        super().__init__("Lender", db_client, embeddings_client)
        
    def originate_loan(self, borrower_id: str, principal: float, 
                      interest_rate: float = 8.0, term_months: int = 36) -> str:
        """Originate a new self-funding loan.
        
        Args:
            borrower_id: Borrower identifier
            principal: Loan amount
            interest_rate: Annual interest rate (default 8% to replace 24% predatory rates)
            term_months: Loan term in months
            
        Returns:
            Loan ID as string.
        """
        # Create loan with 60/40 split
        loan = Loan(
            borrower_id=borrower_id,
            principal=principal,
            interest_rate=interest_rate,
            term_months=term_months,
            status=LoanStatus.ACTIVE
        )
        
        # Store loan in database
        loan_id = self.db.store_loan(loan.to_dict())
        
        # Log origination
        self.log_action('originate_loan', {
            'loan_id': loan_id,
            'borrower_id': borrower_id,
            'principal': principal,
            'interest_rate': interest_rate,
            'split': {
                'investment': loan.split.investment_amount,
                'borrower': loan.split.borrower_amount
            }
        })
        
        # Store context for other agents
        self.store_context('loan_originated', {
            'loan_id': loan_id,
            'principal': principal,
            'investment_amount': loan.split.investment_amount,
            'borrower_amount': loan.split.borrower_amount,
            'monthly_payment': loan.monthly_payment,
        }, generate_embedding=True)
        
        return loan_id
    
    def process(self, loan_id: str, **kwargs) -> Dict[str, Any]:
        """Process loan portfolio management.
        
        Args:
            loan_id: Loan to process
            
        Returns:
            Portfolio status and metrics.
        """
        loan_data = self.get_loan(loan_id)
        if not loan_data:
            return {'error': 'Loan not found'}
        
        loan = Loan.from_dict(loan_data)
        
        # Get transaction history
        transactions = self.db.get_transactions(loan_id=loan_id)
        
        # Calculate portfolio metrics
        total_payments = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'payment')
        investment_returns = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'investment_return')
        
        metrics = {
            'loan_id': loan_id,
            'status': loan.status.value,
            'outstanding_balance': loan.outstanding_balance,
            'investment_balance': loan.investment_balance,
            'total_payments_received': total_payments,
            'investment_returns': investment_returns,
            'performance_ratio': investment_returns / loan.split.investment_amount if loan.split.investment_amount > 0 else 0,
        }
        
        # Store metrics as context
        self.store_context('portfolio_metrics', metrics, generate_embedding=True)
        
        return metrics
    
    def assess_risk(self, loan_id: str) -> Dict[str, Any]:
        """Assess loan risk based on agent insights.
        
        Args:
            loan_id: Loan to assess
            
        Returns:
            Risk assessment.
        """
        # Get insights from other agents
        spending_contexts = self.get_shared_context(agent_name='SpendingGuard', limit=10)
        budget_contexts = self.get_shared_context(agent_name='BudgetAnalyzer', limit=10)
        trading_contexts = self.get_shared_context(agent_name='AlphaTrading', limit=10)
        
        # Analyze risk factors
        risk_score = 0.5  # Baseline
        risk_factors = []
        
        # Check for spending anomalies
        anomalies = [c for c in spending_contexts if c.get('data', {}).get('anomaly_detected')]
        if anomalies:
            risk_score += 0.2
            risk_factors.append('spending_anomalies_detected')
        
        # Check budget health
        budget_warnings = [c for c in budget_contexts if c.get('data', {}).get('warning')]
        if budget_warnings:
            risk_score += 0.15
            risk_factors.append('budget_warnings')
        
        # Check investment performance
        poor_performance = [c for c in trading_contexts if c.get('data', {}).get('performance', 0) < 0]
        if poor_performance:
            risk_score += 0.15
            risk_factors.append('poor_investment_performance')
        
        risk_assessment = {
            'loan_id': loan_id,
            'risk_score': min(risk_score, 1.0),
            'risk_factors': risk_factors,
            'recommendation': 'monitor' if risk_score < 0.7 else 'intervention_needed'
        }
        
        self.store_context('risk_assessment', risk_assessment, generate_embedding=True)
        
        return risk_assessment
