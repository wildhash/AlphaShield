"""Budget Analyzer agent for analyzing borrower budgets."""
from typing import Dict, Any, List

from alphashield.agents.base_agent import BaseAgent


class BudgetAnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing borrower budgets."""
    
    def __init__(self, db_client, embeddings_client=None):
        super().__init__("BudgetAnalyzer", db_client, embeddings_client)
        
    def analyze_budget(self, borrower_id: str, income: float, 
                      expenses: Dict[str, float]) -> Dict[str, Any]:
        """Analyze borrower budget for sustainability.
        
        Args:
            borrower_id: Borrower to analyze
            income: Monthly income
            expenses: Dictionary of expense categories and amounts
            
        Returns:
            Budget analysis results.
        """
        total_expenses = sum(expenses.values())
        discretionary_income = income - total_expenses
        expense_ratio = total_expenses / income if income > 0 else 0
        
        # Calculate recommended expense ratios (50/30/20 rule)
        recommended_needs = income * 0.50
        recommended_wants = income * 0.30
        recommended_savings = income * 0.20
        
        # Categorize expenses
        needs = ['housing', 'utilities', 'food', 'transportation', 'insurance', 'healthcare']
        actual_needs = sum(expenses.get(cat, 0) for cat in needs)
        actual_wants = total_expenses - actual_needs
        
        budget_health = 'healthy'
        warnings = []
        
        if expense_ratio > 0.90:
            budget_health = 'critical'
            warnings.append('Expenses exceed 90% of income - high default risk')
        elif expense_ratio > 0.80:
            budget_health = 'concerning'
            warnings.append('Limited discretionary income - monitor closely')
        
        if actual_needs > recommended_needs * 1.2:
            warnings.append('Essential expenses are too high - may need assistance')
        
        analysis = {
            'borrower_id': borrower_id,
            'monthly_income': income,
            'total_expenses': total_expenses,
            'discretionary_income': discretionary_income,
            'expense_ratio': expense_ratio,
            'actual_needs': actual_needs,
            'actual_wants': actual_wants,
            'budget_health': budget_health,
            'warnings': warnings,
            'warning': len(warnings) > 0,
            'recommendations': self._generate_budget_recommendations(
                income, expenses, actual_needs, actual_wants
            )
        }
        
        self.store_context('budget_analysis', analysis, generate_embedding=True)
        
        if warnings:
            self.log_action('budget_warning', {
                'borrower_id': borrower_id,
                'budget_health': budget_health,
                'warnings': warnings
            })
        
        return analysis
    
    def _generate_budget_recommendations(self, income: float, expenses: Dict[str, float],
                                        actual_needs: float, actual_wants: float) -> List[str]:
        """Generate budget optimization recommendations."""
        recommendations = []
        
        recommended_needs = income * 0.50
        recommended_wants = income * 0.30
        
        if actual_needs > recommended_needs:
            overage = actual_needs - recommended_needs
            recommendations.append(
                f"Reduce essential expenses by ${overage:.2f} per month if possible"
            )
        
        if actual_wants > recommended_wants:
            overage = actual_wants - recommended_wants
            recommendations.append(
                f"Reduce discretionary spending by ${overage:.2f} per month"
            )
        
        # Check specific high categories
        for category, amount in expenses.items():
            if amount > income * 0.30 and category in ['housing', 'transportation']:
                recommendations.append(
                    f"{category.capitalize()} costs are high - consider lower-cost alternatives"
                )
        
        if not recommendations:
            recommendations.append("Budget is well-balanced - maintain current spending")
        
        return recommendations
    
    def process(self, loan_id: str, **kwargs) -> Dict[str, Any]:
        """Process budget analysis for a loan.
        
        Args:
            loan_id: Loan to analyze
            **kwargs: Should include 'income' and 'expenses'
            
        Returns:
            Budget analysis results.
        """
        loan_data = self.get_loan(loan_id)
        if not loan_data:
            return {'error': 'Loan not found'}
        
        borrower_id = loan_data.get('borrower_id')
        income = kwargs.get('income', 0)
        expenses = kwargs.get('expenses', {})
        
        # Analyze budget
        analysis = self.analyze_budget(borrower_id, income, expenses)
        analysis['loan_id'] = loan_id
        
        # Check if loan payment is affordable
        monthly_payment = loan_data.get('monthly_payment', 0)
        total_with_payment = sum(expenses.values()) + monthly_payment
        payment_ratio = monthly_payment / income if income > 0 else 0
        
        analysis['loan_payment'] = monthly_payment
        analysis['payment_ratio'] = payment_ratio
        analysis['total_with_payment'] = total_with_payment
        analysis['payment_affordable'] = payment_ratio <= 0.15  # <15% of income
        
        if not analysis['payment_affordable']:
            analysis['warnings'].append(
                f"Loan payment is {payment_ratio*100:.1f}% of income - recommend restructuring"
            )
        
        return analysis
    
    def forecast_budget(self, borrower_id: str, months: int = 12) -> Dict[str, Any]:
        """Forecast budget sustainability over time.
        
        Args:
            borrower_id: Borrower to forecast
            months: Number of months to forecast
            
        Returns:
            Budget forecast.
        """
        # Get historical budget analyses
        contexts = self.get_shared_context(
            agent_name=self.name,
            context_type='budget_analysis',
            limit=6
        )
        
        # Simple projection based on recent trends
        if contexts:
            recent = contexts[0].get('data', {})
            expense_ratio = recent.get('expense_ratio', 0)
            
            forecast = {
                'borrower_id': borrower_id,
                'forecast_months': months,
                'projected_expense_ratio': expense_ratio,
                'sustainability': 'sustainable' if expense_ratio < 0.80 else 'at_risk',
                'recommendation': 'Monitor monthly' if expense_ratio < 0.80 else 'Intervention needed'
            }
        else:
            forecast = {
                'borrower_id': borrower_id,
                'message': 'Insufficient data for forecast'
            }
        
        self.store_context('budget_forecast', forecast, generate_embedding=True)
        
        return forecast
