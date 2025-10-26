"""Financial context capsule for shared agent context."""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class ContextCapsule:
    """Aggregated financial context for a user.
    
    Contains rolling features from Mongo and top-k similar case IDs
    from vector store for shared agent context.
    """
    user_id: str
    
    # Rolling financial features from MongoDB
    rolling_features: Dict[str, Any] = field(default_factory=dict)
    # e.g., {
    #   'avg_monthly_income': float,
    #   'avg_monthly_spending': float,
    #   'credit_score': int,
    #   'debt_to_income_ratio': float,
    #   'payment_history_score': float,
    #   'spending_volatility': float,
    # }
    
    # Top-k similar case IDs from vector store
    similar_case_ids: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'user_id': self.user_id,
            'rolling_features': self.rolling_features,
            'similar_case_ids': self.similar_case_ids,
            'timestamp': self.timestamp,
        }


def build_financial_capsule(
    user_id: str,
    db_client=None,
    embeddings_client=None,
    top_k: int = 5
) -> ContextCapsule:
    """Build a financial context capsule for a user.
    
    Reads from MongoDB to aggregate rolling features and fetches top-k
    similar cases from vector store (IDs only).
    
    Args:
        user_id: User identifier
        db_client: MongoDB client for reading financial data
        embeddings_client: Embeddings client for vector similarity search
        top_k: Number of similar cases to retrieve
        
    Returns:
        ContextCapsule with aggregated financial context
    """
    rolling_features = {}
    similar_case_ids = []
    
    if db_client:
        # Aggregate rolling features from MongoDB
        # This would typically query user's historical data
        try:
            # Get user's financial history
            contexts = db_client.get_collection('agent_contexts').find(
                {'data.borrower_id': user_id}
            ).sort('timestamp', -1).limit(50)
            
            # Aggregate features
            income_values = []
            spending_values = []
            credit_scores = []
            
            for ctx in contexts:
                data = ctx.get('data', {})
                if 'monthly_gross_income' in data:
                    income_values.append(data['monthly_gross_income'])
                if 'average_monthly_spending' in data:
                    spending_values.append(data['average_monthly_spending'])
                if 'credit_score' in data:
                    credit_scores.append(data['credit_score'])
            
            # Calculate rolling averages
            if income_values:
                rolling_features['avg_monthly_income'] = sum(income_values) / len(income_values)
            if spending_values:
                rolling_features['avg_monthly_spending'] = sum(spending_values) / len(spending_values)
            if credit_scores:
                rolling_features['credit_score'] = int(sum(credit_scores) / len(credit_scores))
            
            # Calculate debt-to-income ratio if we have both
            if income_values and spending_values:
                avg_income = rolling_features['avg_monthly_income']
                avg_spending = rolling_features['avg_monthly_spending']
                if avg_income > 0:
                    rolling_features['debt_to_income_ratio'] = avg_spending / avg_income
        except Exception:
            # If aggregation fails, continue with empty features
            pass
    
    if embeddings_client:
        # Fetch similar cases from vector store
        try:
            # Create a query embedding from user context
            query_text = f"user_id:{user_id} financial_profile"
            # This would do semantic search for similar borrower profiles
            # For now, we'll return empty list as it requires vector DB setup
            similar_case_ids = []
        except Exception:
            # If vector search fails, continue with empty list
            pass
    
    return ContextCapsule(
        user_id=user_id,
        rolling_features=rolling_features,
        similar_case_ids=similar_case_ids,
    )
