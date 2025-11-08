"""MongoDB Atlas client for AlphaShield shared context storage."""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

try:
    from alphashield.utils.errors import ExecutionError
except ImportError:
    # Fallback if errors module doesn't exist
    class ExecutionError(Exception):
        pass

try:
    from alphashield.database.schemas import DecisionDoc
except ImportError:
    # Fallback if schemas module doesn't exist yet
    DecisionDoc = None  # type: ignore


class MongoDBClient:
    """MongoDB Atlas client for storing and retrieving agent context."""
    
    def __init__(self, connection_uri: Optional[str] = None):
        """Initialize MongoDB connection.
        
        Args:
            connection_uri: MongoDB connection string. If None, reads from env.
        """
        self.uri = connection_uri or os.getenv('MONGODB_URI') or os.getenv('MONGO_URL')
        if not self.uri:
            raise ValueError("MongoDB URI not provided")
        
        self.client: MongoClient = MongoClient(self.uri)
        self.db: Database = self.client.alphashield
        
    def get_collection(self, name: str) -> Collection:
        """Get a collection by name."""
        return self.db[name]
    
    # Original API methods
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
        """Retrieve loan by ID (supports both ObjectId and string loan_id field)."""
        from bson import ObjectId
        loans = self.get_collection('loans')
        # Try ObjectId first
        try:
            return loans.find_one({'_id': ObjectId(loan_id)})
        except Exception:
            # Fallback to loan_id field
            return loans.find_one({'loan_id': loan_id})
    
    def set_loan(self, loan: Dict[str, Any]) -> None:
        """Set/update loan information (upsert by loan_id)."""
        loans = self.get_collection('loans')
        loan_id = loan.get('loan_id')
        if not loan_id:
            raise ValueError("loan must have 'loan_id' field")
        loan['updated_at'] = datetime.utcnow()
        loans.update_one({'loan_id': loan_id}, {'$set': loan}, upsert=True)
    
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
    
    def store_agent_decision(self, decision: Dict[str, Any]) -> None:
        """Store agent decision with validation."""
        try:
            if "timestamp" not in decision:
                decision["timestamp"] = datetime.utcnow()
            if DecisionDoc:
                DecisionDoc(**decision)  # validation
            decisions = self.get_collection('decisions')
            decisions.update_one(
                {
                    "agent_id": decision["agent_id"],
                    "loan_id": decision["loan_id"],
                    "timestamp": decision["timestamp"],
                },
                {"$setOnInsert": decision},
                upsert=True,
            )
        except Exception as e:
            raise ExecutionError(f"decision validation/store failed: {e}")
    
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


class InMemoryMongoStub:
    """In-memory stub for MongoDB client when no connection is available."""
    
    def __init__(self) -> None:
        self.loans: Dict[str, Dict[str, Any]] = {}
        self.decisions: List[Dict[str, Any]] = []
        self.contexts: List[Dict[str, Any]] = []
        self.transactions: List[Dict[str, Any]] = []

    def get_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        return self.loans.get(loan_id)

    def set_loan(self, loan: Dict[str, Any]) -> None:
        loan_id = loan.get("loan_id")
        if loan_id:
            self.loans[loan_id] = loan

    def store_agent_decision(self, decision: Dict[str, Any]) -> None:
        try:
            if "timestamp" not in decision:
                decision["timestamp"] = datetime.utcnow()
            if DecisionDoc:
                DecisionDoc(**decision)  # validation
            # idempotency check
            key = (decision["agent_id"], decision["loan_id"], str(decision["timestamp"])[:16])
            if any((d.get("agent_id"), d.get("loan_id"), str(d.get("timestamp"))[:16]) == key for d in self.decisions):
                return
            self.decisions.append(dict(decision))
        except Exception as e:
            raise ExecutionError(f"decision validation/store failed: {e}")

    def store_context(self, agent_name: str, context_type: str,
                     data: Dict[str, Any], embedding: Optional[List[float]] = None) -> str:
        context_doc = {
            'agent_name': agent_name,
            'context_type': context_type,
            'data': data,
            'timestamp': datetime.utcnow(),
        }
        if embedding:
            context_doc['embedding'] = embedding
        self.contexts.append(context_doc)
        return str(len(self.contexts) - 1)

    def get_contexts(self, agent_name: Optional[str] = None,
                    context_type: Optional[str] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        filtered = self.contexts
        if agent_name:
            filtered = [c for c in filtered if c.get('agent_name') == agent_name]
        if context_type:
            filtered = [c for c in filtered if c.get('context_type') == context_type]
        return sorted(filtered, key=lambda x: x.get('timestamp', datetime.min), reverse=True)[:limit]

    def store_transaction(self, transaction_data: Dict[str, Any]) -> str:
        transaction_data['timestamp'] = datetime.utcnow()
        self.transactions.append(transaction_data)
        return str(len(self.transactions) - 1)

    def get_transactions(self, loan_id: Optional[str] = None,
                        transaction_type: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        filtered = self.transactions
        if loan_id:
            filtered = [t for t in filtered if t.get('loan_id') == loan_id]
        if transaction_type:
            filtered = [t for t in filtered if t.get('type') == transaction_type]
        return sorted(filtered, key=lambda x: x.get('timestamp', datetime.min), reverse=True)[:limit]

    def close(self):
        pass


def get_mongo_client():
    """Factory function that returns appropriate MongoDB client."""
    url = os.getenv("MONGO_URL") or os.getenv("MONGODB_URI")
    if not url:
        return InMemoryMongoStub()
    try:
        return MongoDBClient(url)
    except Exception:
        # Fallback to stub
        return InMemoryMongoStub()
