"""Contract Review agent for analyzing loan contracts."""
from typing import Dict, Any, List

from alphashield.agents.base_agent import BaseAgent


class ContractReviewAgent(BaseAgent):
    """Agent responsible for analyzing and reviewing loan contracts."""
    
    def __init__(self, db_client, embeddings_client=None):
        super().__init__("ContractReview", db_client, embeddings_client)
        
    def review_loan_terms(self, loan_id: str, contract_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Review loan contract terms for fairness and compliance.
        
        Args:
            loan_id: Loan to review
            contract_terms: Contract terms to analyze
            
        Returns:
            Contract review results.
        """
        loan_data = self.get_loan(loan_id)
        if not loan_data:
            return {'error': 'Loan not found'}
        
        # Extract key terms
        interest_rate = contract_terms.get('interest_rate', loan_data.get('interest_rate'))
        term_months = contract_terms.get('term_months', loan_data.get('term_months'))
        fees = contract_terms.get('fees', {})
        penalties = contract_terms.get('penalties', {})
        
        # Analyze fairness
        issues = []
        warnings = []
        highlights = []
        
        # Check interest rate (AlphaShield targets 8% vs predatory 24%)
        if interest_rate > 15:
            issues.append(f"Interest rate of {interest_rate}% is high - AlphaShield standard is 8%")
        elif interest_rate <= 10:
            highlights.append(f"Interest rate of {interest_rate}% is favorable (below 10%)")
        
        # Check for excessive fees
        origination_fee = fees.get('origination', 0)
        if origination_fee > 0.05 * loan_data.get('principal', 0):
            issues.append(f"Origination fee is excessive (>{5}% of loan amount)")
        
        # Check prepayment penalties
        prepayment_penalty = penalties.get('prepayment', 0)
        if prepayment_penalty > 0:
            warnings.append("Prepayment penalty detected - borrower cannot pay off early without cost")
        else:
            highlights.append("No prepayment penalty - borrower can pay off early")
        
        # Check late payment fees
        late_fee = penalties.get('late_payment', 0)
        monthly_payment = loan_data.get('monthly_payment', 0)
        if late_fee > 0.05 * monthly_payment:
            warnings.append(f"Late fee is high (>{5}% of monthly payment)")
        
        # Calculate APR including fees
        total_fees = sum(fees.values())
        effective_rate = self._calculate_apr(
            loan_data.get('principal', 0),
            monthly_payment,
            term_months,
            total_fees
        )
        
        review = {
            'loan_id': loan_id,
            'stated_interest_rate': interest_rate,
            'effective_apr': effective_rate,
            'term_months': term_months,
            'fees': fees,
            'penalties': penalties,
            'issues': issues,
            'warnings': warnings,
            'highlights': highlights,
            'overall_rating': self._calculate_rating(issues, warnings),
            'compliant': len(issues) == 0,
            'recommended': len(issues) == 0 and interest_rate <= 10
        }
        
        self.store_context('contract_review', review, generate_embedding=True)
        
        if issues:
            self.log_action('contract_issues_found', {
                'loan_id': loan_id,
                'issue_count': len(issues),
                'issues': issues
            })
        
        return review
    
    def _calculate_apr(self, principal: float, monthly_payment: float, 
                      term_months: int, fees: float) -> float:
        """Calculate effective APR including fees."""
        if principal == 0 or term_months == 0:
            return 0
        
        # Simplified APR calculation
        total_paid = monthly_payment * term_months + fees
        total_interest = total_paid - principal
        
        # Approximate APR
        apr = (total_interest / principal) / (term_months / 12) * 100
        
        return apr
    
    def _calculate_rating(self, issues: List[str], warnings: List[str]) -> str:
        """Calculate overall contract rating."""
        if len(issues) > 2:
            return 'poor'
        elif len(issues) > 0:
            return 'fair'
        elif len(warnings) > 2:
            return 'good'
        else:
            return 'excellent'
    
    def process(self, loan_id: str, **kwargs) -> Dict[str, Any]:
        """Process contract review for a loan.
        
        Args:
            loan_id: Loan to review
            **kwargs: Should include 'contract_terms'
            
        Returns:
            Contract review results.
        """
        contract_terms = kwargs.get('contract_terms', {})
        return self.review_loan_terms(loan_id, contract_terms)
    
    def compare_to_market(self, loan_id: str) -> Dict[str, Any]:
        """Compare loan terms to market alternatives.
        
        Args:
            loan_id: Loan to compare
            
        Returns:
            Market comparison results.
        """
        loan_data = self.get_loan(loan_id)
        if not loan_data:
            return {'error': 'Loan not found'}
        
        interest_rate = loan_data.get('interest_rate', 0)
        
        # Market benchmarks
        market_rates = {
            'predatory_lenders': 24.0,
            'credit_cards': 19.99,
            'personal_loans': 12.0,
            'alphashield_target': 8.0,
            'prime_rate': 5.5
        }
        
        comparison = {
            'loan_id': loan_id,
            'loan_rate': interest_rate,
            'market_rates': market_rates,
            'savings_vs_predatory': (market_rates['predatory_lenders'] - interest_rate),
            'position': 'competitive' if interest_rate <= market_rates['personal_loans'] else 'expensive'
        }
        
        # Calculate potential savings
        principal = loan_data.get('principal', 0)
        term_years = loan_data.get('term_months', 36) / 12
        
        comparison['annual_savings_vs_predatory'] = principal * (
            market_rates['predatory_lenders'] - interest_rate
        ) / 100
        
        comparison['total_savings_vs_predatory'] = (
            comparison['annual_savings_vs_predatory'] * term_years
        )
        
        self.store_context('market_comparison', comparison, generate_embedding=True)
        
        return comparison
    
    def generate_recommendations(self, review: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on contract review.
        
        Args:
            review: Contract review results
            
        Returns:
            List of recommendations.
        """
        recommendations = []
        
        if review.get('issues'):
            recommendations.append("Address contract issues before proceeding")
            for issue in review['issues']:
                recommendations.append(f"- {issue}")
        
        if review.get('warnings'):
            recommendations.append("Consider the following warnings:")
            for warning in review['warnings']:
                recommendations.append(f"- {warning}")
        
        if review.get('effective_apr', 0) > review.get('stated_interest_rate', 0) + 2:
            recommendations.append("Effective APR is significantly higher than stated rate due to fees")
        
        if review.get('recommended'):
            recommendations.append("Contract terms are favorable - recommended to proceed")
        
        return recommendations
