"""Tax Optimizer agent for optimizing borrower tax strategy."""
from typing import Dict, Any, List
from datetime import datetime

from alphashield.agents.base_agent import BaseAgent


class TaxOptimizerAgent(BaseAgent):
    """Agent responsible for optimizing tax strategy."""
    
    def __init__(self, db_client, embeddings_client=None):
        super().__init__("TaxOptimizer", db_client, embeddings_client)
        
    def analyze_tax_situation(self, borrower_id: str, income: float,
                             deductions: Dict[str, float],
                             filing_status: str = 'single') -> Dict[str, Any]:
        """Analyze borrower tax situation and identify optimization opportunities.
        
        Args:
            borrower_id: Borrower to analyze
            income: Annual income
            deductions: Dictionary of deduction categories and amounts
            filing_status: Tax filing status
            
        Returns:
            Tax analysis and optimization recommendations.
        """
        # Calculate taxable income
        standard_deduction = {
            'single': 13850,
            'married': 27700,
            'head_of_household': 20800
        }
        
        std_deduction = standard_deduction.get(filing_status, 13850)
        total_itemized = sum(deductions.values())
        
        # Use higher of standard or itemized
        deduction_amount = max(std_deduction, total_itemized)
        taxable_income = max(0, income - deduction_amount)
        
        # Simplified tax calculation (2024 brackets)
        tax_owed = self._calculate_tax(taxable_income, filing_status)
        effective_rate = (tax_owed / income * 100) if income > 0 else 0
        
        # Identify optimization opportunities
        opportunities = []
        potential_savings = 0
        
        # Check if itemizing would be beneficial
        if total_itemized < std_deduction and total_itemized > 0:
            gap = std_deduction - total_itemized
            opportunities.append({
                'category': 'deductions',
                'description': f'Increase deductible expenses by ${gap:.2f} to benefit from itemizing',
                'potential_savings': gap * 0.22  # Assuming 22% bracket
            })
        
        # Check retirement contributions
        retirement_contrib = deductions.get('retirement', 0)
        max_401k = 22500
        if retirement_contrib < max_401k:
            additional_possible = min(max_401k - retirement_contrib, income * 0.10)
            opportunities.append({
                'category': 'retirement',
                'description': f'Increase 401(k) contributions by ${additional_possible:.2f}',
                'potential_savings': additional_possible * 0.22
            })
            potential_savings += additional_possible * 0.22
        
        # Check HSA eligibility
        if 'hsa' not in deductions:
            opportunities.append({
                'category': 'hsa',
                'description': 'Consider Health Savings Account for tax-free medical savings',
                'potential_savings': 4150 * 0.22  # Max HSA * tax rate
            })
            potential_savings += 4150 * 0.22
        
        analysis = {
            'borrower_id': borrower_id,
            'annual_income': income,
            'filing_status': filing_status,
            'deduction_used': deduction_amount,
            'deduction_type': 'itemized' if total_itemized > std_deduction else 'standard',
            'taxable_income': taxable_income,
            'estimated_tax': tax_owed,
            'effective_rate': effective_rate,
            'optimization_opportunities': opportunities,
            'potential_annual_savings': potential_savings
        }
        
        self.store_context('tax_analysis', analysis, generate_embedding=True)
        
        self.log_action('tax_analysis_complete', {
            'borrower_id': borrower_id,
            'opportunities_found': len(opportunities),
            'potential_savings': potential_savings
        })
        
        return analysis
    
    def _calculate_tax(self, taxable_income: float, filing_status: str) -> float:
        """Calculate federal tax owed using 2024 tax brackets."""
        # Simplified 2024 single filer brackets
        brackets = {
            'single': [
                (11600, 0.10),
                (47150, 0.12),
                (100525, 0.22),
                (191950, 0.24),
                (243725, 0.32),
                (609350, 0.35),
                (float('inf'), 0.37)
            ]
        }
        
        tax_brackets = brackets.get(filing_status, brackets['single'])
        tax = 0
        previous_bracket = 0
        
        for bracket_limit, rate in tax_brackets:
            if taxable_income > bracket_limit:
                tax += (bracket_limit - previous_bracket) * rate
                previous_bracket = bracket_limit
            else:
                tax += (taxable_income - previous_bracket) * rate
                break
        
        return tax
    
    def process(self, loan_id: str, **kwargs) -> Dict[str, Any]:
        """Process tax optimization for a loan.
        
        Args:
            loan_id: Loan to process
            **kwargs: Should include 'income', 'deductions', 'filing_status'
            
        Returns:
            Tax optimization results.
        """
        loan_data = self.get_loan(loan_id)
        if not loan_data:
            return {'error': 'Loan not found'}
        
        borrower_id = loan_data.get('borrower_id')
        income = kwargs.get('income', 0)
        deductions = kwargs.get('deductions', {})
        filing_status = kwargs.get('filing_status', 'single')
        
        # Analyze tax situation
        analysis = self.analyze_tax_situation(borrower_id, income, deductions, filing_status)
        analysis['loan_id'] = loan_id
        
        # Check if loan interest is deductible
        loan_interest = loan_data.get('interest_rate', 0) * loan_data.get('outstanding_balance', 0) / 100
        if loan_interest > 0:
            analysis['loan_interest_paid'] = loan_interest
            analysis['loan_interest_deductible'] = False  # Personal loans typically not deductible
            analysis['note'] = 'Personal loan interest is not tax deductible'
        
        return analysis
    
    def generate_tax_strategy(self, borrower_id: str, loan_id: str) -> Dict[str, Any]:
        """Generate comprehensive tax strategy for borrower.
        
        Args:
            borrower_id: Borrower to strategize for
            loan_id: Associated loan
            
        Returns:
            Tax strategy recommendations.
        """
        # Get recent analyses
        contexts = self.get_shared_context(
            agent_name=self.name,
            context_type='tax_analysis',
            limit=3
        )
        
        strategy = {
            'borrower_id': borrower_id,
            'loan_id': loan_id,
            'short_term_actions': [],
            'long_term_actions': [],
            'estimated_annual_benefit': 0
        }
        
        if contexts:
            latest = contexts[0].get('data', {})
            opportunities = latest.get('optimization_opportunities', [])
            
            for opp in opportunities:
                action = {
                    'category': opp.get('category'),
                    'action': opp.get('description'),
                    'savings': opp.get('potential_savings', 0)
                }
                
                if opp.get('category') in ['retirement', 'hsa']:
                    strategy['long_term_actions'].append(action)
                else:
                    strategy['short_term_actions'].append(action)
                
                strategy['estimated_annual_benefit'] += opp.get('potential_savings', 0)
        
        self.store_context('tax_strategy', strategy, generate_embedding=True)
        
        return strategy
