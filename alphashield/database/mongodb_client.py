"""MongoDB Atlas client for AlphaShield shared context storage."""
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database


class MongoDBClient:
    """MongoDB Atlas client for storing and retrieving agent context."""
    
    def __init__(self, connection_uri: Optional[str] = None):
        """Initialize MongoDB connection.
        
        Args:
            connection_uri: MongoDB connection string. If None, reads from env.
        """
        self.uri = connection_uri or os.getenv('MONGODB_URI')
        if not self.uri:
            raise ValueError("MongoDB URI not provided")
        
        self.client: MongoClient = MongoClient(self.uri)
        self.db: Database = self.client.alphashield
        
    def get_collection(self, name: str) -> Collection:
        """Get a collection by name."""
        return self.db[name]
    
    def store_loan(self, loan_data: Dict[str, Any]) -> str:
        """Store loan information.
        
        Args:
            loan_data: Loan details including amount, rate, borrower_id, etc.
            
        Returns:
            Inserted loan ID as string.
        """
        loans = self.get_collection('loans')
        loan_data['created_at'] = datetime.utcnow()
        loan_data['updated_at'] = datetime.utcnow()
        result = loans.insert_one(loan_data)
        return str(result.inserted_id)
    
    def get_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve loan by ID."""
        from bson import ObjectId
        loans = self.get_collection('loans')
        return loans.find_one({'_id': ObjectId(loan_id)})
    
    def update_loan(self, loan_id: str, updates: Dict[str, Any]) -> bool:
        """Update loan information."""
        from bson import ObjectId
        loans = self.get_collection('loans')
        updates['updated_at'] = datetime.utcnow()
        result = loans.update_one(
            {'_id': ObjectId(loan_id)},
            {'$set': updates}
        )
        return result.modified_count > 0
    
    def store_context(self, agent_name: str, context_type: str, 
                     data: Dict[str, Any], embedding: Optional[List[float]] = None) -> str:
        """Store agent context with optional embedding for semantic search.
        
        Args:
            agent_name: Name of the agent storing context
            context_type: Type of context (e.g., 'analysis', 'decision', 'alert')
            data: Context data
            embedding: Optional vector embedding for semantic search
            
        Returns:
            Inserted context ID as string.
        """
        contexts = self.get_collection('agent_contexts')
        context_doc = {
            'agent_name': agent_name,
            'context_type': context_type,
            'data': data,
            'timestamp': datetime.utcnow(),
        }
        if embedding:
            context_doc['embedding'] = embedding
            
        result = contexts.insert_one(context_doc)
        return str(result.inserted_id)
    
    def get_contexts(self, agent_name: Optional[str] = None,
                    context_type: Optional[str] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve contexts with optional filtering.
        
        Args:
            agent_name: Filter by agent name
            context_type: Filter by context type
            limit: Maximum number of results
            
        Returns:
            List of context documents.
        """
        contexts = self.get_collection('agent_contexts')
        query = {}
        if agent_name:
            query['agent_name'] = agent_name
        if context_type:
            query['context_type'] = context_type
            
        return list(contexts.find(query).sort('timestamp', -1).limit(limit))
    
    def store_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """Store transaction (investment, payment, spending)."""
        transactions = self.get_collection('transactions')
        transaction_data['timestamp'] = datetime.utcnow()
        result = transactions.insert_one(transaction_data)
        return str(result.inserted_id)
    
    def get_transactions(self, loan_id: Optional[str] = None,
                        transaction_type: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve transactions with optional filtering."""
        transactions = self.get_collection('transactions')
        query = {}
        if loan_id:
            query['loan_id'] = loan_id
        if transaction_type:
            query['type'] = transaction_type
            
        return list(transactions.find(query).sort('timestamp', -1).limit(limit))
    
    def close(self):
        """Close MongoDB connection."""
        self.client.close()
