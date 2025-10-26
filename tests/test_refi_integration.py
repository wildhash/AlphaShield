"""Integration test for refi happy-path."""
import unittest
from unittest.mock import MagicMock
from alphashield.orchestrator.graph import execute


class TestRefiHappyPath(unittest.TestCase):
    """Integration test for complete refi orchestration."""
    
    def setUp(self):
        """Set up mock database."""
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_db.get_collection.return_value = self.mock_collection
        
        # Mock synthetic borrower data
        self.mock_collection.find.return_value.sort.return_value.limit.return_value = [
            {
                'data': {
                    'borrower_id': 'synthetic_123',
                    'credit_score': 720,
                    'monthly_gross_income': 6000.0,
                    'average_monthly_spending': 3500.0,
                    'debt_to_income_ratio': 0.30,
                }
            }
        ]
        
        # Mock insert result
        mock_insert = MagicMock()
        mock_insert.inserted_id = 'bundle_456'
        self.mock_collection.insert_one.return_value = mock_insert
    
    def test_refi_happy_path(self):
        """Test complete refi orchestration happy path."""
        # Execute orchestrator with synthetic borrower
        bundle = execute(
            trace_id='test_trace_123',
            user_id='synthetic_123',
            loan_app_id='loan_789',
            db_client=self.mock_db
        )
        
        # Verify bundle structure
        self.assertIsNotNone(bundle)
        self.assertEqual(bundle.trace_id, 'test_trace_123')
        self.assertEqual(bundle.user_id, 'synthetic_123')
        self.assertEqual(bundle.loan_app_id, 'loan_789')
        
        # Verify all phases completed
        self.assertIn('approved', bundle.underwriting)
        self.assertTrue(bundle.underwriting['approved'])
        
        # Verify coverage ratio
        self.assertIn('coverage_ratio', bundle.coverage)
        coverage_ratio = bundle.coverage['coverage_ratio']
        self.assertGreaterEqual(coverage_ratio, 1.30, 
                               f"Coverage ratio {coverage_ratio} below minimum 1.30")
        
        # Verify allocation constraints
        allocation = bundle.coverage.get('allocation', {})
        for asset, weight in allocation.items():
            self.assertLessEqual(weight, 0.40, 
                               f"{asset} weight {weight} exceeds max 0.40")
            self.assertGreaterEqual(weight, 0.0,
                                  f"{asset} weight {weight} is negative")
        
        # Verify allocation sums to ~1.0
        total_weight = sum(allocation.values())
        self.assertAlmostEqual(total_weight, 1.0, places=1,
                              msg=f"Total allocation {total_weight} not close to 1.0")
        
        # Verify offer generated
        self.assertIn('principal', bundle.offer)
        self.assertIn('interest_rate', bundle.offer)
        self.assertGreater(bundle.offer['principal'], 0)
        
        # Verify compliance passed
        self.assertIn('compliant', bundle.compliance)
        self.assertTrue(bundle.compliance['compliant'])
        
        # Verify audit trail
        self.assertGreater(len(bundle.audit_trail), 0)
        
        # Check required nodes are present
        node_names = {event['node'] for event in bundle.audit_trail}
        required_nodes = {'intake_doc', 'identity_fraud', 'underwriting', 
                         'risk_bridge', 'offer', 'compliance'}
        self.assertTrue(required_nodes.issubset(node_names),
                       f"Missing nodes: {required_nodes - node_names}")
        
        # Verify all events succeeded
        for event in bundle.audit_trail:
            self.assertEqual(event['status'], 'success',
                           f"Node {event['node']} failed")
        
        # Verify fairness (interest rate reasonable)
        interest_rate = bundle.offer.get('interest_rate', 0)
        self.assertLessEqual(interest_rate, 12.0,
                           f"Interest rate {interest_rate}% too high")
        self.assertGreaterEqual(interest_rate, 5.0,
                              f"Interest rate {interest_rate}% suspiciously low")
        
        # Verify bundle was persisted
        self.mock_collection.insert_one.assert_called_once()
    
    def test_refi_with_contract_review(self):
        """Test refi with contract review triggered."""
        # Mock lower credit score to trigger review
        self.mock_collection.find.return_value.sort.return_value.limit.return_value = [
            {'data': {'credit_score': 640}}
        ]
        
        bundle = execute(
            trace_id='test_trace_124',
            user_id='synthetic_124',
            loan_app_id='loan_790',
            db_client=self.mock_db
        )
        
        # Should include contract review
        self.assertIsNotNone(bundle.contract_review)
        self.assertIn('reviewed', bundle.contract_review)
        
        # Contract review node should be in audit trail
        node_names = {event['node'] for event in bundle.audit_trail}
        self.assertIn('contract_review', node_names)
    
    def test_refi_short_term_relief(self):
        """Test refi in short-term relief mode."""
        bundle = execute(
            trace_id='test_trace_125',
            user_id='synthetic_125',
            loan_app_id='loan_791',
            db_client=self.mock_db,
            short_term_relief=True
        )
        
        # Should trigger contract review
        self.assertIsNotNone(bundle.contract_review)
        
        # Should be marked as short-term relief
        self.assertTrue(bundle.loan_app.get('short_term_relief', False))
    
    def test_emergency_allocation(self):
        """Test that emergency cash allocation is maintained."""
        bundle = execute(
            trace_id='test_trace_126',
            user_id='synthetic_126',
            loan_app_id='loan_792',
            db_client=self.mock_db
        )
        
        allocation = bundle.coverage.get('allocation', {})
        
        # Should have minimum cash allocation (bonds typically serve as cash)
        bonds_allocation = allocation.get('bonds', 0.0)
        self.assertGreaterEqual(bonds_allocation, 0.05,
                               f"Bonds allocation {bonds_allocation} below minimum 0.05")


if __name__ == '__main__':
    unittest.main()
