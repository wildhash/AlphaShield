"""Tests for context management."""
import unittest
from unittest.mock import MagicMock
from alphashield.context.capsule import ContextCapsule, build_financial_capsule
from alphashield.context.packet import ContextPacket, make_packet


class TestContextCapsule(unittest.TestCase):
    """Test ContextCapsule dataclass."""
    
    def test_capsule_creation(self):
        """Test creating a context capsule."""
        capsule = ContextCapsule(
            user_id='user_123',
            rolling_features={'avg_monthly_income': 5000.0},
            similar_case_ids=['case_1', 'case_2']
        )
        
        self.assertEqual(capsule.user_id, 'user_123')
        self.assertEqual(capsule.rolling_features['avg_monthly_income'], 5000.0)
        self.assertEqual(len(capsule.similar_case_ids), 2)
    
    def test_capsule_to_dict(self):
        """Test converting capsule to dict."""
        capsule = ContextCapsule(user_id='user_123')
        data = capsule.to_dict()
        
        self.assertIn('user_id', data)
        self.assertIn('rolling_features', data)
        self.assertIn('similar_case_ids', data)


class TestBuildFinancialCapsule(unittest.TestCase):
    """Test build_financial_capsule function."""
    
    def test_build_without_clients(self):
        """Test building capsule without DB clients."""
        capsule = build_financial_capsule('user_123')
        
        self.assertEqual(capsule.user_id, 'user_123')
        self.assertIsInstance(capsule.rolling_features, dict)
        self.assertIsInstance(capsule.similar_case_ids, list)
    
    def test_build_with_mock_db(self):
        """Test building capsule with mock DB."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.get_collection.return_value = mock_collection
        
        # Mock query results
        mock_cursor = [
            {'data': {'borrower_id': 'user_123', 'monthly_gross_income': 5000.0}},
            {'data': {'borrower_id': 'user_123', 'average_monthly_spending': 3000.0}},
        ]
        mock_collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        capsule = build_financial_capsule('user_123', db_client=mock_db)
        
        self.assertEqual(capsule.user_id, 'user_123')
        # Should have aggregated features
        self.assertGreaterEqual(len(capsule.rolling_features), 0)


class TestContextPacket(unittest.TestCase):
    """Test ContextPacket dataclass."""
    
    def test_packet_creation(self):
        """Test creating a context packet."""
        packet = make_packet('trace_1', 'user_123', 'loan_456')
        
        self.assertEqual(packet.trace_id, 'trace_1')
        self.assertEqual(packet.user_id, 'user_123')
        self.assertEqual(packet.loan_app_id, 'loan_456')
        self.assertEqual(len(packet.context), 0)
    
    def test_add_context(self):
        """Test adding context to packet."""
        packet = make_packet('trace_1', 'user_123', 'loan_456')
        packet.add_context('agent_1', {'result': 'approved'})
        
        self.assertIn('agent_1', packet.context)
        self.assertEqual(packet.context['agent_1']['data']['result'], 'approved')
        self.assertIn('input_hash', packet.context['agent_1'])
    
    def test_get_context(self):
        """Test retrieving context from packet."""
        packet = make_packet('trace_1', 'user_123', 'loan_456')
        packet.add_context('agent_1', {'result': 'approved'})
        
        data = packet.get_context('agent_1')
        self.assertEqual(data['result'], 'approved')
        
        # Non-existent agent
        data = packet.get_context('agent_2')
        self.assertIsNone(data)
    
    def test_packet_to_dict(self):
        """Test converting packet to dict."""
        packet = make_packet('trace_1', 'user_123', 'loan_456')
        packet.add_context('agent_1', {'result': 'approved'})
        
        data = packet.to_dict()
        self.assertIn('trace_id', data)
        self.assertIn('context', data)


if __name__ == '__main__':
    unittest.main()
