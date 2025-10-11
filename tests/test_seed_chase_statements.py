"""Tests for seed_chase_statements script."""
import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import json

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from seed_chase_statements import load_json_file, seed_statements


class TestSeedChaseStatements(unittest.TestCase):
    """Test seed_chase_statements script functionality."""
    
    def test_load_json_file(self):
        """Test JSON file loading."""
        test_data = {"test": "data", "value": 123}
        mock_file_content = json.dumps(test_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            result = load_json_file('test.json')
            self.assertEqual(result, test_data)
    
    @patch('seed_chase_statements.MongoDBClient')
    @patch('seed_chase_statements.load_json_file')
    def test_seed_statements_success(self, mock_load_json, mock_mongo_class):
        """Test successful seeding of statements."""
        # Setup mocks
        mock_client = MagicMock()
        mock_mongo_class.return_value = mock_client
        
        mock_collection = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        
        # Mock insert_many return
        mock_collection.insert_many.return_value.inserted_ids = ['id1', 'id2', 'id3', 'id4', 'id5']
        
        # Mock load_json_file to return sample statement data
        mock_statement = {
            "document_type": "Credit_Card_Statement",
            "issuer": "JPMorgan Chase Bank, N.A.",
            "statement_date": "2024-10-31",
            "statement_period": {
                "start_date": "2024-10-01",
                "end_date": "2024-10-31"
            },
            "transactions": [
                {"amount": 100, "category": "Shopping"},
                {"amount": 50, "category": "Dining"}
            ],
            "spending_patterns": {
                "total_new_purchases": 150.00
            },
            "interest_charges": {
                "total_interest_charged": 25.00
            }
        }
        mock_load_json.return_value = mock_statement
        
        # Run the function
        seed_statements()
        
        # Verify MongoDB client was instantiated
        mock_mongo_class.assert_called_once()
        
        # Verify collection was accessed
        mock_client.get_collection.assert_called_with('credit_card_statements')
        
        # Verify delete_many was called to clear existing data
        mock_collection.delete_many.assert_called_once_with({})
        
        # Verify insert_many was called
        mock_collection.insert_many.assert_called_once()
        
        # Verify indexes were created
        self.assertEqual(mock_collection.create_index.call_count, 5)
        
        # Verify connection was closed
        mock_client.close.assert_called_once()
    
    @patch('seed_chase_statements.MongoDBClient')
    @patch('seed_chase_statements.load_json_file')
    def test_seed_statements_with_metadata(self, mock_load_json, mock_mongo_class):
        """Test that metadata fields are added to documents."""
        # Setup mocks
        mock_client = MagicMock()
        mock_mongo_class.return_value = mock_client
        
        mock_collection = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        
        mock_collection.insert_many.return_value.inserted_ids = ['id1']
        
        # Mock statement data
        mock_statement = {
            "document_type": "Credit_Card_Statement",
            "statement_date": "2024-10-31",
            "statement_period": {"start_date": "2024-10-01", "end_date": "2024-10-31"},
            "transactions": [],
            "spending_patterns": {"total_new_purchases": 0},
            "interest_charges": {"total_interest_charged": 0}
        }
        mock_load_json.return_value = mock_statement
        
        # Run the function
        seed_statements()
        
        # Get the documents that were inserted
        call_args = mock_collection.insert_many.call_args[0][0]
        
        # Verify metadata was added
        for doc in call_args:
            self.assertIn('_inserted_at', doc)
            self.assertIn('_source_file', doc)
    
    @patch('seed_chase_statements.MongoDBClient')
    @patch('seed_chase_statements.load_json_file')
    def test_seed_statements_handles_missing_files(self, mock_load_json, mock_mongo_class):
        """Test that missing files are handled gracefully."""
        # Setup mocks
        mock_client = MagicMock()
        mock_mongo_class.return_value = mock_client
        
        mock_collection = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        
        # Mock load_json_file to raise FileNotFoundError
        mock_load_json.side_effect = FileNotFoundError("File not found")
        
        # Run the function - should not raise exception
        seed_statements()
        
        # Verify no documents were inserted
        mock_collection.insert_many.assert_not_called()
        
        # Verify connection was still closed
        mock_client.close.assert_called_once()
    
    @patch('seed_chase_statements.MongoDBClient')
    @patch('seed_chase_statements.load_json_file')
    def test_seed_statements_handles_invalid_json(self, mock_load_json, mock_mongo_class):
        """Test that invalid JSON is handled gracefully."""
        # Setup mocks
        mock_client = MagicMock()
        mock_mongo_class.return_value = mock_client
        
        mock_collection = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        
        # Mock load_json_file to raise JSONDecodeError
        mock_load_json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        # Run the function - should not raise exception
        seed_statements()
        
        # Verify no documents were inserted
        mock_collection.insert_many.assert_not_called()
        
        # Verify connection was still closed
        mock_client.close.assert_called_once()
    
    @patch('seed_chase_statements.MongoDBClient')
    @patch('seed_chase_statements.load_json_file')
    def test_seed_statements_creates_correct_indexes(self, mock_load_json, mock_mongo_class):
        """Test that correct indexes are created."""
        # Setup mocks
        mock_client = MagicMock()
        mock_mongo_class.return_value = mock_client
        
        mock_collection = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        
        mock_collection.insert_many.return_value.inserted_ids = ['id1']
        
        # Mock statement data
        mock_statement = {
            "document_type": "Credit_Card_Statement",
            "statement_date": "2024-10-31",
            "statement_period": {"start_date": "2024-10-01", "end_date": "2024-10-31"},
            "transactions": [],
            "spending_patterns": {"total_new_purchases": 0},
            "interest_charges": {"total_interest_charged": 0}
        }
        mock_load_json.return_value = mock_statement
        
        # Run the function
        seed_statements()
        
        # Verify indexes were created with correct fields
        index_calls = mock_collection.create_index.call_args_list
        
        # Should have 5 index creation calls
        self.assertEqual(len(index_calls), 5)
        
        # Check that the correct fields were indexed
        indexed_fields = [call[0][0] for call in index_calls]
        self.assertIn("statement_date", indexed_fields)
        self.assertIn("account_information.account_number", indexed_fields)
        self.assertIn("statement_period.start_date", indexed_fields)
        self.assertIn("statement_period.end_date", indexed_fields)
        self.assertIn([("transactions.transaction_date", 1)], indexed_fields)


if __name__ == '__main__':
    unittest.main()
