"""Daily guard runner for spending anomaly detection."""
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from alphashield.agents.spending_guard.agent import SpendingGuardAgent, GuardEvent
from alphashield.orchestrator.graph import execute


class GuardRunner:
    """Runner for daily spending guard checks.
    
    Loads recent transactions, runs guard analysis, and enqueues
    micro-refi tasks for high-severity events.
    """
    
    def __init__(self, db_client=None, embeddings_client=None):
        """Initialize guard runner.
        
        Args:
            db_client: MongoDB client for data access
            embeddings_client: Embeddings client for vector search
        """
        self.db = db_client
        self.embeddings = embeddings_client
        self.guard = SpendingGuardAgent()
    
    def run_daily_check(self) -> List[GuardEvent]:
        """Run daily spending guard check for all active loans.
        
        Returns:
            List of all guard events detected
        """
        all_events = []
        
        if not self.db:
            return all_events
        
        # Get all active loans
        loans = self.db.get_collection('loans').find({'status': 'active'})
        
        for loan in loans:
            user_id = loan.get('borrower_id')
            loan_id = str(loan.get('_id'))
            
            # Get recent transactions (last 30 days)
            transactions = self._get_recent_transactions(user_id, days=30)
            
            if not transactions:
                continue
            
            # Get user baseline
            baseline = self._get_user_baseline(user_id)
            
            # Run guard analysis
            events = self.guard.analyze_transactions(transactions, baseline)
            
            # Process high-severity events
            for event in events:
                if event.severity in ['high', 'critical']:
                    self._handle_high_severity_event(user_id, loan_id, event)
            
            all_events.extend(events)
        
        return all_events
    
    def _get_recent_transactions(self, user_id: str, days: int = 30) -> List[dict]:
        """Get recent transactions for a user.
        
        Args:
            user_id: User identifier
            days: Number of days to look back
            
        Returns:
            List of transaction dicts
        """
        if not self.db:
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query transactions from agent contexts
        contexts = self.db.get_collection('agent_contexts').find({
            'data.borrower_id': user_id,
            'timestamp': {'$gte': cutoff_date},
            'context_type': 'spending_analysis'
        })
        
        transactions = []
        for ctx in contexts:
            data = ctx.get('data', {})
            if 'transactions' in data:
                transactions.extend(data['transactions'])
        
        return transactions
    
    def _get_user_baseline(self, user_id: str) -> Optional[dict]:
        """Get user spending baseline stats.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with baseline stats or None
        """
        if not self.db:
            return None
        
        # Get historical spending data
        contexts = self.db.get_collection('agent_contexts').find({
            'data.borrower_id': user_id,
            'context_type': 'budget_analysis'
        }).sort('timestamp', -1).limit(1)
        
        for ctx in contexts:
            data = ctx.get('data', {})
            return {
                'avg_weekly_spending': data.get('average_monthly_spending', 0.0) / 4.0,
                'avg_monthly_spending': data.get('average_monthly_spending', 0.0),
            }
        
        return None
    
    def _handle_high_severity_event(self, user_id: str, loan_id: str, event: GuardEvent) -> None:
        """Handle high-severity guard event.
        
        Enqueues a micro-refi task if action is 'micro_refi'.
        
        Args:
            user_id: User identifier
            loan_id: Loan identifier
            event: GuardEvent with high/critical severity
        """
        if event.suggested_action == 'micro_refi':
            # Enqueue micro-refi orchestration task
            trace_id = f"guard-refi-{uuid.uuid4()}"
            
            # Execute orchestrator in short-term relief mode
            try:
                bundle = execute(
                    trace_id=trace_id,
                    user_id=user_id,
                    loan_app_id=loan_id,
                    db_client=self.db,
                    embeddings_client=self.embeddings,
                    short_term_relief=True
                )
                
                # Log the micro-refi event
                if self.db:
                    self.db.get_collection('guard_events').insert_one({
                        'user_id': user_id,
                        'loan_id': loan_id,
                        'event_type': event.event_type,
                        'severity': event.severity,
                        'action_taken': 'micro_refi',
                        'trace_id': trace_id,
                        'bundle_id': bundle.trace_id,
                        'timestamp': datetime.utcnow(),
                    })
            except Exception as e:
                # Log error but don't fail
                if self.db:
                    self.db.get_collection('guard_errors').insert_one({
                        'user_id': user_id,
                        'loan_id': loan_id,
                        'error': str(e),
                        'timestamp': datetime.utcnow(),
                    })


def main():
    """Main entry point for guard runner script."""
    from alphashield.database.mongodb_client import MongoDBClient
    from alphashield.database.embeddings import EmbeddingsClient
    import os
    
    # Initialize clients
    mongodb_uri = os.getenv('MONGODB_URI')
    voyage_key = os.getenv('VOYAGE_API_KEY')
    
    db_client = MongoDBClient(mongodb_uri) if mongodb_uri else None
    embeddings_client = EmbeddingsClient(voyage_key) if voyage_key else None
    
    # Run guard
    runner = GuardRunner(db_client, embeddings_client)
    events = runner.run_daily_check()
    
    print(f"Guard check complete. Found {len(events)} events.")
    print(f"High/Critical events: {sum(1 for e in events if e.severity in ['high', 'critical'])}")


if __name__ == '__main__':
    main()
