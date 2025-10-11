"""Spending Guard agent for detecting spending anomalies."""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import statistics

from alphashield.agents.base_agent import BaseAgent


class SpendingGuardAgent(BaseAgent):
    """Agent responsible for detecting spending anomalies."""
    
    def __init__(self, db_client, embeddings_client=None):
        super().__init__("SpendingGuard", db_client, embeddings_client)
        
    def analyze_spending(self, borrower_id: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze borrower spending for anomalies.
        
        Args:
            borrower_id: Borrower to analyze
            transactions: List of spending transactions
            
        Returns:
            Anomaly detection results.
        """
        if not transactions:
            return {'borrower_id': borrower_id, 'message': 'No transactions to analyze'}
        
        # Calculate spending statistics
        amounts = [t.get('amount', 0) for t in transactions]
        categories = {}
        
        for t in transactions:
            cat = t.get('category', 'uncategorized')
            categories[cat] = categories.get(cat, 0) + t.get('amount', 0)
        
        avg_amount = statistics.mean(amounts) if amounts else 0
        std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0
        
        # Detect anomalies (spending > 2 standard deviations above mean)
        threshold = avg_amount + (2 * std_dev)
        anomalies = [t for t in transactions if t.get('amount', 0) > threshold]
        
        # Flag high-risk categories
        high_risk_categories = ['gambling', 'luxury', 'crypto']
        risky_spending = sum(categories.get(cat, 0) for cat in high_risk_categories)
        total_spending = sum(amounts)
        risk_ratio = risky_spending / total_spending if total_spending > 0 else 0
        
        analysis = {
            'borrower_id': borrower_id,
            'total_transactions': len(transactions),
            'total_spending': total_spending,
            'average_transaction': avg_amount,
            'anomalies_detected': len(anomalies),
            'anomaly_details': anomalies[:5],  # Top 5 anomalies
            'risky_spending_ratio': risk_ratio,
            'categories': categories,
            'alert_level': 'high' if len(anomalies) > 3 or risk_ratio > 0.3 else 'low',
            'anomaly_detected': len(anomalies) > 0 or risk_ratio > 0.3
        }
        
        # Store analysis
        self.store_context('spending_analysis', analysis, generate_embedding=True)
        
        if analysis['anomaly_detected']:
            self.log_action('anomaly_detected', {
                'borrower_id': borrower_id,
                'anomaly_count': len(anomalies),
                'risk_ratio': risk_ratio
            })
        
        return analysis
    
    def process(self, loan_id: str, **kwargs) -> Dict[str, Any]:
        """Process spending monitoring for a loan.
        
        Args:
            loan_id: Loan to monitor
            **kwargs: Should include 'transactions' list
            
        Returns:
            Spending monitoring results.
        """
        loan_data = self.get_loan(loan_id)
        if not loan_data:
            return {'error': 'Loan not found'}
        
        borrower_id = loan_data.get('borrower_id')
        transactions = kwargs.get('transactions', [])
        
        # Analyze spending patterns
        analysis = self.analyze_spending(borrower_id, transactions)
        analysis['loan_id'] = loan_id
        
        # Check for rapid spending after loan disbursement
        recent_transactions = [
            t for t in transactions 
            if (datetime.utcnow() - t.get('timestamp', datetime.utcnow())).days <= 7
        ]
        
        if recent_transactions:
            recent_total = sum(t.get('amount', 0) for t in recent_transactions)
            borrower_amount = loan_data.get('split', {}).get('borrower_amount', 0)
            
            if recent_total > borrower_amount * 0.5:  # Spent >50% in first week
                analysis['rapid_spending_warning'] = True
                analysis['alert_level'] = 'high'
                
                self.log_action('rapid_spending_detected', {
                    'loan_id': loan_id,
                    'borrower_id': borrower_id,
                    'amount_spent': recent_total,
                    'percentage_of_loan': (recent_total / borrower_amount) * 100
                })
        
        return analysis
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate spending recommendations based on analysis.
        
        Args:
            analysis: Spending analysis results
            
        Returns:
            List of recommendations.
        """
        recommendations = []
        
        if analysis.get('anomaly_detected'):
            recommendations.append("Review unusual transactions with borrower")
        
        if analysis.get('risky_spending_ratio', 0) > 0.2:
            recommendations.append("High-risk spending detected - recommend financial counseling")
        
        if analysis.get('rapid_spending_warning'):
            recommendations.append("Rapid spending after loan disbursement - conduct check-in")
        
        if not recommendations:
            recommendations.append("Spending patterns appear normal - continue monitoring")
        
        return recommendations
