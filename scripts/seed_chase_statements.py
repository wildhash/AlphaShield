"""
MongoDB seed script for Chase credit card statements
Populates the database with credit card statement data from October 2024 to February 2025
"""

import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alphashield.database.mongodb_client import MongoDBClient


def load_json_file(filename):
    """Load JSON data from file"""
    with open(filename, 'r') as f:
        return json.load(f)


def seed_statements():
    """Seed the MongoDB database with credit card statement data"""
    
    # Connect to MongoDB
    mongo_client = MongoDBClient()
    collection = mongo_client.get_collection('credit_card_statements')
    
    # Statement files to load
    statement_files = [
        'chase_statement_202410.json',
        'chase_statement_202411.json',
        'chase_statement_202412.json',
        'chase_statement_202501.json',
        'chase_statement_202502.json'
    ]
    
    # Clear existing data (optional - remove if you want to append)
    print(f"Clearing existing data from credit_card_statements...")
    collection.delete_many({})
    
    # Load and insert each statement
    documents = []
    for filename in statement_files:
        try:
            print(f"Loading {filename}...")
            statement_data = load_json_file(filename)
            
            # Add metadata for tracking
            statement_data['_inserted_at'] = datetime.utcnow()
            statement_data['_source_file'] = filename
            
            documents.append(statement_data)
            print(f"✓ Loaded {filename}")
            
        except FileNotFoundError:
            print(f"✗ File not found: {filename}")
        except json.JSONDecodeError:
            print(f"✗ Invalid JSON in file: {filename}")
    
    # Insert all documents
    if documents:
        result = collection.insert_many(documents)
        print(f"\n✓ Successfully inserted {len(result.inserted_ids)} statements into MongoDB")
        print(f"  Database: alphashield")
        print(f"  Collection: credit_card_statements")
        
        # Create indexes for better query performance
        print("\nCreating indexes...")
        collection.create_index("statement_date")
        collection.create_index("account_information.account_number")
        collection.create_index("statement_period.start_date")
        collection.create_index("statement_period.end_date")
        collection.create_index([("transactions.transaction_date", 1)])
        print("✓ Indexes created")
        
        # Display summary statistics
        print("\n=== Summary Statistics ===")
        total_transactions = sum(len(doc.get('transactions', [])) for doc in documents)
        total_spending = sum(doc['spending_patterns']['total_new_purchases'] for doc in documents)
        total_interest = sum(doc['interest_charges']['total_interest_charged'] for doc in documents)
        
        print(f"Total Statements: {len(documents)}")
        print(f"Total Transactions: {total_transactions}")
        print(f"Total New Purchases: ${total_spending:,.2f}")
        print(f"Total Interest Charged: ${total_interest:,.2f}")
        print(f"Date Range: {documents[0]['statement_period']['start_date']} to {documents[-1]['statement_period']['end_date']}")
        
    else:
        print("\n✗ No documents to insert")
    
    # Close connection
    mongo_client.close()
    print("\n✓ Database connection closed")


if __name__ == "__main__":
    print("=" * 60)
    print("Chase Credit Card Statement Seeder")
    print("=" * 60)
    print()
    
    try:
        seed_statements()
        print("\n✓ Seeding completed successfully!")
    except Exception as e:
        print(f"\n✗ Error during seeding: {str(e)}")
        raise
