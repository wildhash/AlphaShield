"""Tests for populate_sample_data script."""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from populate_sample_data import populate_sample_data


class TestPopulateSampleData(unittest.TestCase):
    """Test populate_sample_data script functionality."""
    
    @patch('populate_sample_data.MongoDBClient')
    def test_populate_sample_data_structure(self, mock_mongo_class):
        """Test that populate_sample_data creates correct document structures."""
        # Setup mocks
        mock_client = MagicMock()
        mock_mongo_class.return_value = mock_client
        
        # Mock collections
        mock_brokerage_collection = MagicMock()
        mock_credit_card_collection = MagicMock()
        mock_credit_report_collection = MagicMock()
        
        # Configure the mock to return different collections
        def get_collection_side_effect(name):
            if name == 'brokerage_statements':
                return mock_brokerage_collection
            elif name == 'credit_card_statements':
                return mock_credit_card_collection
            elif name == 'credit_reports':
                return mock_credit_report_collection
        
        mock_client.get_collection.side_effect = get_collection_side_effect
        
        # Mock insert_one return values
        mock_brokerage_collection.insert_one.return_value.inserted_id = 'brokerage_123'
        mock_credit_card_collection.insert_one.return_value.inserted_id = 'credit_card_456'
        mock_credit_report_collection.insert_one.return_value.inserted_id = 'credit_report_789'
        
        # Run the function
        result = populate_sample_data()
        
        # Verify MongoDB client was instantiated
        mock_mongo_class.assert_called_once()
        
        # Verify all three collections were accessed
        self.assertEqual(mock_client.get_collection.call_count, 3)
        
        # Verify insert_one was called on each collection
        mock_brokerage_collection.insert_one.assert_called_once()
        mock_credit_card_collection.insert_one.assert_called_once()
        mock_credit_report_collection.insert_one.assert_called_once()
        
        # Verify return structure
        self.assertIn('brokerage_id', result)
        self.assertIn('credit_card_id', result)
        self.assertIn('credit_report_id', result)
        self.assertEqual(result['brokerage_id'], 'brokerage_123')
        self.assertEqual(result['credit_card_id'], 'credit_card_456')
        self.assertEqual(result['credit_report_id'], 'credit_report_789')
    
    @patch('populate_sample_data.MongoDBClient')
    def test_brokerage_statement_structure(self, mock_mongo_class):
        """Test brokerage statement has correct structure."""
        mock_client = MagicMock()
        mock_mongo_class.return_value = mock_client
        
        mock_collection = MagicMock()
        mock_collection.insert_one.return_value.inserted_id = 'test_id'
        mock_client.get_collection.return_value = mock_collection
        
        populate_sample_data()
        
        # Get the call to insert_one for brokerage statement
        call_args = mock_collection.insert_one.call_args_list[0][0][0]
        
        # Verify key fields
        self.assertEqual(call_args['document_type'], 'Brokerage_Account_Statement')
        self.assertEqual(call_args['financial_institution'], 'Fidelity Investments')
        self.assertIn('account_information', call_args)
        self.assertIn('positions', call_args)
        self.assertEqual(len(call_args['positions']), 2)
        self.assertIn('created_at', call_args)
        self.assertIn('updated_at', call_args)
    
    @patch('populate_sample_data.MongoDBClient')
    def test_credit_card_statement_structure(self, mock_mongo_class):
        """Test credit card statement has correct structure."""
        mock_client = MagicMock()
        mock_mongo_class.return_value = mock_client
        
        mock_collection = MagicMock()
        mock_collection.insert_one.return_value.inserted_id = 'test_id'
        mock_client.get_collection.return_value = mock_collection
        
        populate_sample_data()
        
        # Get the call to insert_one for credit card statement
        call_args = mock_collection.insert_one.call_args_list[1][0][0]
        
        # Verify key fields
        self.assertEqual(call_args['document_type'], 'Credit_Card_Statement')
        self.assertEqual(call_args['issuer'], 'JPMorgan Chase Bank, N.A.')
        self.assertIn('red_flags', call_args)
        self.assertEqual(len(call_args['red_flags']), 3)
        self.assertIn('spending_by_category', call_args)
        self.assertIn('created_at', call_args)
        self.assertIn('updated_at', call_args)
    
    @patch('populate_sample_data.MongoDBClient')
    def test_credit_report_structure(self, mock_mongo_class):
        """Test credit report has correct structure."""
        mock_client = MagicMock()
        mock_mongo_class.return_value = mock_client
        
        mock_collection = MagicMock()
        mock_collection.insert_one.return_value.inserted_id = 'test_id'
        mock_client.get_collection.return_value = mock_collection
        
        populate_sample_data()
        
        # Get the call to insert_one for credit report
        call_args = mock_collection.insert_one.call_args_list[2][0][0]
        
        # Verify key fields
        self.assertEqual(call_args['document_type'], 'Credit_Report')
        self.assertEqual(call_args['bureau'], 'Experian')
        self.assertIn('credit_score', call_args)
        self.assertEqual(call_args['credit_score']['score'], 585)
        self.assertIn('risk_indicators', call_args)
        self.assertIn('alerts_and_warnings', call_args)
        self.assertEqual(len(call_args['alerts_and_warnings']), 3)
        self.assertIn('created_at', call_args)
        self.assertIn('updated_at', call_args)


if __name__ == '__main__':
    unittest.main()
