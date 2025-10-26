"""Tests for orchestrator graph."""
import unittest
from unittest.mock import MagicMock, patch
from alphashield.orchestrator.graph import execute, OriginationBundle, StorageClient


class TestOriginationBundle(unittest.TestCase):
    """Test OriginationBundle dataclass."""
    
    def test_bundle_creation(self):
        """Test creating origination bundle."""
        bundle = OriginationBundle(
            trace_id='trace_1',
            loan_app_id='loan_456',
            user_id='user_123'
        )
        
        self.assertEqual(bundle.trace_id, 'trace_1')
        self.assertEqual(bundle.loan_app_id, 'loan_456')
        self.assertEqual(bundle.user_id, 'user_123')
        self.assertEqual(len(bundle.audit_trail), 0)
    
    def test_bundle_to_dict(self):
        """Test converting bundle to dict."""
        bundle = OriginationBundle(
            trace_id='trace_1',
            loan_app_id='loan_456',
            user_id='user_123'
        )
        
        data = bundle.to_dict()
        self.assertIn('trace_id', data)
        self.assertIn('loan_app_id', data)
        self.assertIn('audit_trail', data)


class TestStorageClient(unittest.TestCase):
    """Test StorageClient."""
    
    def test_store_bundle_without_db(self):
        """Test storing bundle without DB."""
        storage = StorageClient()
        bundle = OriginationBundle(
            trace_id='trace_1',
            loan_app_id='loan_456',
            user_id='user_123'
        )
        
        bundle_id = storage.store_bundle(bundle)
        self.assertEqual(bundle_id, 'trace_1')
    
    def test_store_bundle_with_mock_db(self):
        """Test storing bundle with mock DB."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.get_collection.return_value = mock_collection
        
        mock_result = MagicMock()
        mock_result.inserted_id = 'bundle_123'
        mock_collection.insert_one.return_value = mock_result
        
        storage = StorageClient(mock_db)
        bundle = OriginationBundle(
            trace_id='trace_1',
            loan_app_id='loan_456',
            user_id='user_123'
        )
        
        bundle_id = storage.store_bundle(bundle)
        self.assertEqual(bundle_id, 'bundle_123')


class TestOrchestratorExecution(unittest.TestCase):
    """Test orchestrator DAG execution."""
    
    def test_execute_without_db(self):
        """Test executing orchestrator without DB."""
        bundle = execute(
            trace_id='trace_1',
            user_id='user_123',
            loan_app_id='loan_456'
        )
        
        self.assertEqual(bundle.trace_id, 'trace_1')
        self.assertEqual(bundle.user_id, 'user_123')
        self.assertEqual(bundle.loan_app_id, 'loan_456')
        
        # Check that all phases completed
        self.assertIn('approved', bundle.underwriting)
        self.assertIn('coverage_ratio', bundle.coverage)
        self.assertIn('principal', bundle.offer)
        self.assertIn('compliant', bundle.compliance)
        
        # Check audit trail
        self.assertGreater(len(bundle.audit_trail), 0)
        
        # Verify node ordering
        node_names = [event['node'] for event in bundle.audit_trail]
        self.assertIn('intake_doc', node_names)
        self.assertIn('identity_fraud', node_names)
        self.assertIn('underwriting', node_names)
        self.assertIn('risk_bridge', node_names)
        self.assertIn('offer', node_names)
        self.assertIn('compliance', node_names)
    
    def test_execute_with_short_term_relief(self):
        """Test execution in short-term relief mode."""
        bundle = execute(
            trace_id='trace_2',
            user_id='user_123',
            loan_app_id='loan_456',
            short_term_relief=True
        )
        
        # Should trigger contract review
        self.assertIsNotNone(bundle.contract_review)
        self.assertTrue(bundle.loan_app.get('short_term_relief', False))
    
    def test_execute_with_low_credit_score(self):
        """Test execution with low credit score triggers contract review."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.get_collection.return_value = mock_collection
        
        # Mock low credit score
        mock_collection.find.return_value.sort.return_value.limit.return_value = [
            {'data': {'credit_score': 640}}
        ]
        mock_collection.insert_one.return_value = MagicMock(inserted_id='bundle_123')
        
        bundle = execute(
            trace_id='trace_3',
            user_id='user_123',
            loan_app_id='loan_456',
            db_client=mock_db
        )
        
        # Should trigger contract review for low credit
        self.assertIsNotNone(bundle.contract_review)
    
    def test_audit_trail_contains_hashes(self):
        """Test that audit trail contains input hashes."""
        bundle = execute(
            trace_id='trace_4',
            user_id='user_123',
            loan_app_id='loan_456'
        )
        
        for event in bundle.audit_trail:
            self.assertIn('node', event)
            self.assertIn('payload_id', event)
            self.assertIn('input_hash', event)
            self.assertIn('status', event)
            self.assertEqual(event['status'], 'success')


if __name__ == '__main__':
    unittest.main()
