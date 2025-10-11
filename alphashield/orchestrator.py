"""AlphaShield orchestrator for coordinating multi-agent system."""
from typing import Dict, Any, Optional
from alphashield.database.mongodb_client import MongoDBClient
from alphashield.database.embeddings import EmbeddingsClient
from alphashield.agents.lender_agent import LenderAgent
from alphashield.agents.alpha_trading_agent import AlphaTradingAgent
from alphashield.agents.spending_guard_agent import SpendingGuardAgent
from alphashield.agents.budget_analyzer_agent import BudgetAnalyzerAgent
from alphashield.agents.tax_optimizer_agent import TaxOptimizerAgent
from alphashield.agents.contract_review_agent import ContractReviewAgent


class AlphaShieldOrchestrator:
    """Orchestrates the 6 AI agents for self-funding loan management."""
    
    def __init__(self, mongodb_uri: Optional[str] = None, 
                 voyage_api_key: Optional[str] = None):
        """Initialize AlphaShield with all agents.
        
        Args:
            mongodb_uri: MongoDB connection string
            voyage_api_key: Voyage AI API key
        """
        # Initialize shared infrastructure
        self.db = MongoDBClient(mongodb_uri)
        self.embeddings = EmbeddingsClient(voyage_api_key) if voyage_api_key else None
        
        # Initialize all 6 agents
        self.lender = LenderAgent(self.db, self.embeddings)
        self.trading = AlphaTradingAgent(self.db, self.embeddings)
        self.spending_guard = SpendingGuardAgent(self.db, self.embeddings)
        self.budget_analyzer = BudgetAnalyzerAgent(self.db, self.embeddings)
        self.tax_optimizer = TaxOptimizerAgent(self.db, self.embeddings)
        self.contract_review = ContractReviewAgent(self.db, self.embeddings)
        
        self.agents = {
            'lender': self.lender,
            'trading': self.trading,
            'spending_guard': self.spending_guard,
            'budget_analyzer': self.budget_analyzer,
            'tax_optimizer': self.tax_optimizer,
            'contract_review': self.contract_review,
        }
    
    def originate_loan(self, borrower_id: str, principal: float,
                      interest_rate: float = 8.0, term_months: int = 36,
                      contract_terms: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Originate a new self-funding loan with full agent coordination.
        
        Args:
            borrower_id: Borrower identifier
            principal: Loan amount
            interest_rate: Annual interest rate (default 8%)
            term_months: Loan term in months
            contract_terms: Optional contract terms for review
            
        Returns:
            Complete loan origination results including all agent analyses.
        """
        # Step 1: Review contract terms if provided
        contract_review = None
        if contract_terms:
            temp_loan_data = {
                'principal': principal,
                'interest_rate': interest_rate,
                'term_months': term_months,
                'monthly_payment': principal * (interest_rate/1200) / (1 - (1 + interest_rate/1200)**(-term_months))
            }
            # Temporarily store for review
            temp_id = self.db.store_loan(temp_loan_data)
            contract_review = self.contract_review.review_loan_terms(temp_id, contract_terms)
            
            if not contract_review.get('recommended', False):
                return {
                    'status': 'rejected',
                    'reason': 'Contract terms not recommended',
                    'contract_review': contract_review
                }
        
        # Step 2: Originate loan through Lender agent
        loan_id = self.lender.originate_loan(
            borrower_id=borrower_id,
            principal=principal,
            interest_rate=interest_rate,
            term_months=term_months
        )
        
        # Step 3: Invest 60% through Alpha Trading agent
        investment_plan = self.trading.invest_loan_funds(loan_id, strategy='balanced')
        
        # Step 4: Get initial risk assessment
        risk_assessment = self.lender.assess_risk(loan_id)
        
        return {
            'status': 'success',
            'loan_id': loan_id,
            'principal': principal,
            'interest_rate': interest_rate,
            'split': {
                'investment': principal * 0.6,
                'borrower': principal * 0.4
            },
            'investment_plan': investment_plan,
            'risk_assessment': risk_assessment,
            'contract_review': contract_review,
        }
    
    def monitor_loan(self, loan_id: str, borrower_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Monitor loan with all agents providing insights.
        
        Args:
            loan_id: Loan to monitor
            borrower_data: Optional borrower data including income, expenses, transactions
            
        Returns:
            Comprehensive monitoring report from all agents.
        """
        borrower_data = borrower_data or {}
        
        # Portfolio metrics from Lender
        portfolio_metrics = self.lender.process(loan_id)
        
        # Investment performance from Alpha Trading
        investment_performance = self.trading.process(loan_id)
        risk_capacity = self.trading.assess_risk_capacity(loan_id)
        
        # Spending analysis from Spending Guard
        spending_analysis = None
        if 'transactions' in borrower_data:
            spending_analysis = self.spending_guard.process(
                loan_id,
                transactions=borrower_data['transactions']
            )
        
        # Budget analysis from Budget Analyzer
        budget_analysis = None
        if 'income' in borrower_data and 'expenses' in borrower_data:
            budget_analysis = self.budget_analyzer.process(
                loan_id,
                income=borrower_data['income'],
                expenses=borrower_data['expenses']
            )
        
        # Tax optimization from Tax Optimizer
        tax_optimization = None
        if 'income' in borrower_data and 'deductions' in borrower_data:
            tax_optimization = self.tax_optimizer.process(
                loan_id,
                income=borrower_data['income'],
                deductions=borrower_data['deductions'],
                filing_status=borrower_data.get('filing_status', 'single')
            )
        
        # Overall risk assessment
        risk_assessment = self.lender.assess_risk(loan_id)
        
        return {
            'loan_id': loan_id,
            'portfolio_metrics': portfolio_metrics,
            'investment': {
                'performance': investment_performance,
                'risk_capacity': risk_capacity,
            },
            'spending_analysis': spending_analysis,
            'budget_analysis': budget_analysis,
            'tax_optimization': tax_optimization,
            'risk_assessment': risk_assessment,
        }
    
    def get_borrower_recommendations(self, loan_id: str) -> Dict[str, Any]:
        """Get comprehensive recommendations for borrower from all agents.
        
        Args:
            loan_id: Loan to generate recommendations for
            
        Returns:
            Consolidated recommendations from all agents.
        """
        loan_data = self.db.get_loan(loan_id)
        if not loan_data:
            return {'error': 'Loan not found'}
        
        borrower_id = loan_data.get('borrower_id')
        
        # Get latest analyses from each agent
        recommendations = {
            'loan_id': loan_id,
            'borrower_id': borrower_id,
            'spending_recommendations': [],
            'budget_recommendations': [],
            'tax_recommendations': [],
            'investment_recommendations': [],
        }
        
        # Spending recommendations
        spending_contexts = self.spending_guard.get_shared_context(
            agent_name='SpendingGuard',
            limit=1
        )
        if spending_contexts:
            analysis = spending_contexts[0].get('data', {})
            recommendations['spending_recommendations'] = self.spending_guard.generate_recommendations(analysis)
        
        # Budget recommendations
        budget_contexts = self.budget_analyzer.get_shared_context(
            agent_name='BudgetAnalyzer',
            limit=1
        )
        if budget_contexts:
            analysis = budget_contexts[0].get('data', {})
            recommendations['budget_recommendations'] = analysis.get('recommendations', [])
        
        # Tax strategy
        tax_strategy = self.tax_optimizer.generate_tax_strategy(borrower_id, loan_id)
        recommendations['tax_recommendations'] = {
            'short_term': tax_strategy.get('short_term_actions', []),
            'long_term': tax_strategy.get('long_term_actions', []),
            'estimated_benefit': tax_strategy.get('estimated_annual_benefit', 0)
        }
        
        # Investment recommendations
        risk_capacity = self.trading.assess_risk_capacity(loan_id)
        recommendations['investment_recommendations'] = [risk_capacity.get('recommendation', 'maintain')]
        
        return recommendations
    
    def close(self):
        """Close all connections."""
        self.db.close()
