"""Tests for spending guard agent."""
import unittest
from datetime import datetime, timedelta
from alphashield.agents.spending_guard.agent import SpendingGuardAgent, GuardEvent


class TestGuardEvent(unittest.TestCase):
    """Test GuardEvent dataclass."""
    
    def test_event_creation(self):
        """Test creating a guard event."""
        event = GuardEvent(
            event_type='anomaly',
            severity='high',
            suggested_action='alert',
            category='dining',
            amount=500.0
        )
        
        self.assertEqual(event.event_type, 'anomaly')
        self.assertEqual(event.severity, 'high')
        self.assertEqual(event.suggested_action, 'alert')
        self.assertIsNotNone(event.timestamp)


class TestSpendingGuardAgent(unittest.TestCase):
    """Test spending guard agent."""
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = SpendingGuardAgent()
        
        self.assertEqual(agent.mad_threshold, 3.0)
        self.assertEqual(agent.high_multiplier, 5.0)
        self.assertEqual(agent.critical_multiplier, 7.0)
    
    def test_analyze_empty_transactions(self):
        """Test analyzing empty transaction list."""
        agent = SpendingGuardAgent()
        events = agent.analyze_transactions([])
        
        self.assertEqual(len(events), 0)
    
    def test_mad_anomaly_detection(self):
        """Test MAD-based anomaly detection."""
        agent = SpendingGuardAgent()
        
        # Normal transactions with one outlier
        transactions = [
            {'category': 'dining', 'amount': 50.0, 'date': '2024-01-01'},
            {'category': 'dining', 'amount': 55.0, 'date': '2024-01-02'},
            {'category': 'dining', 'amount': 48.0, 'date': '2024-01-03'},
            {'category': 'dining', 'amount': 52.0, 'date': '2024-01-04'},
            {'category': 'dining', 'amount': 500.0, 'date': '2024-01-05'},  # Outlier
        ]
        
        events = agent.analyze_transactions(transactions)
        
        # Should detect the outlier
        self.assertGreater(len(events), 0)
        
        # Check for anomaly event
        anomaly_events = [e for e in events if e.event_type == 'anomaly']
        self.assertGreater(len(anomaly_events), 0)
        
        # High amount should have high severity
        high_severity = [e for e in anomaly_events if e.severity in ['high', 'critical']]
        self.assertGreater(len(high_severity), 0)
    
    def test_velocity_spike_detection(self):
        """Test velocity spike detection."""
        agent = SpendingGuardAgent()
        
        # Create transactions with velocity spike
        base_date = datetime.now()
        transactions = []
        
        # Normal spending for first 23 days
        for i in range(23):
            transactions.append({
                'category': 'various',
                'amount': 50.0,
                'date': (base_date - timedelta(days=30-i)).isoformat()
            })
        
        # Velocity spike in last 7 days
        for i in range(7):
            transactions.append({
                'category': 'various',
                'amount': 300.0,
                'date': (base_date - timedelta(days=7-i)).isoformat()
            })
        
        baseline = {'avg_weekly_spending': 350.0}
        events = agent.analyze_transactions(transactions, baseline)
        
        # Should detect velocity spike
        velocity_events = [e for e in events if e.event_type == 'velocity_spike']
        self.assertGreater(len(velocity_events), 0)
    
    def test_high_risk_category_detection(self):
        """Test high-risk category detection."""
        agent = SpendingGuardAgent()
        
        transactions = [
            {'category': 'gambling', 'amount': 150.0, 'date': '2024-01-01'},
            {'category': 'casino', 'amount': 200.0, 'date': '2024-01-02'},
            {'category': 'dining', 'amount': 50.0, 'date': '2024-01-03'},
        ]
        
        events = agent.analyze_transactions(transactions)
        
        # Should detect high-risk categories
        risk_events = [e for e in events if e.event_type == 'high_risk_category']
        self.assertGreater(len(risk_events), 0)
    
    def test_severity_levels(self):
        """Test different severity levels based on deviation."""
        agent = SpendingGuardAgent()
        
        # Create transactions with more gradual values for MAD to work
        transactions = [
            {'category': 'dining', 'amount': 48.0, 'date': '2024-01-01'},
            {'category': 'dining', 'amount': 50.0, 'date': '2024-01-02'},
            {'category': 'dining', 'amount': 52.0, 'date': '2024-01-03'},
            {'category': 'dining', 'amount': 51.0, 'date': '2024-01-04'},
            {'category': 'dining', 'amount': 49.0, 'date': '2024-01-05'},
            {'category': 'dining', 'amount': 500.0, 'date': '2024-01-06'},  # Extreme outlier
        ]
        
        events = agent.analyze_transactions(transactions)
        
        # Should have high or critical severity for the outlier
        high_severity = [e for e in events if e.severity in ['high', 'critical']]
        self.assertGreater(len(high_severity), 0, "Should detect high severity anomaly")
        
        # Check that extreme outlier has appropriate action
        extreme_events = [e for e in events if e.amount >= 500.0]
        self.assertGreater(len(extreme_events), 0, "Should detect extreme outlier")



if __name__ == '__main__':
    unittest.main()
