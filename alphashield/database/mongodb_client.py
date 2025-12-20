"""MongoDB Atlas client for AlphaShield shared context storage."""
from __future__ import annotations

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

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
    """
    MongoDB client wrapper supporting both real MongoDB and in-memory stub.
    
    For backward compatibility, this class can be instantiated directly,
    or use get_mongo_client() to get an appropriate client based on environment.
    """
    
    def __init__(self, connection_uri: Optional[str] = None) -> None:
        """
        Initialize MongoDB client.
        
        Args:
            connection_uri: MongoDB connection URI. If not provided, uses
                           MONGO_URL or MONGODB_URI environment variable.
                           If no URI available, uses in-memory stub.
        """
        self._uri = connection_uri or os.getenv("MONGO_URL") or os.getenv("MONGODB_URI")
        self._client = None
        self._db = None
        self._use_stub = False
        
        if self._uri:
            try:
                from pymongo import MongoClient as PyMongoClient  # type: ignore
                self._client = PyMongoClient(self._uri)
                self._db = self._client.get_database()
            except Exception:
                self._use_stub = True
        else:
            self._use_stub = True
        
        # In-memory storage for stub mode
        if self._use_stub:
            self._loans: Dict[str, Dict[str, Any]] = {}
            self._decisions: List[Dict[str, Any]] = []
            self._contexts: List[Dict[str, Any]] = []
            self._transactions: List[Dict[str, Any]] = []

    def get_collection(self, name: str):
        """Get a collection by name."""
        if self._use_stub:
            raise NotImplementedError("get_collection not available in stub mode")
        return self._db[name]

    def get_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get loan by ID."""
        if self._use_stub:
            return self._loans.get(loan_id)
        
        from bson import ObjectId
        # Try ObjectId first
        try:
            return self._db.loans.find_one({'_id': ObjectId(loan_id)})
        except Exception:
            # Fallback to loan_id field
            return self._db.loans.find_one({'loan_id': loan_id})

    def set_loan(self, loan: Dict[str, Any]) -> None:
        """Store or update a loan."""
        loan_id = loan.get("loan_id")
        if not loan_id:
            raise ValueError("loan must have 'loan_id' field")
        
        if self._use_stub:
            self._loans[loan_id] = loan
        else:
            loan['updated_at'] = datetime.utcnow()
            self._db.loans.update_one(
                {"loan_id": loan_id}, 
                {"$set": loan}, 
                upsert=True
            )

    def store_loan(self, loan_data: Dict[str, Any]) -> str:
        """Store loan information.
        
        Args:
            loan_data: Loan details including amount, rate, borrower_id, etc.
            
        Returns:
            Inserted loan ID as string.
        """
        if self._use_stub:
            loan_id = loan_data.get('loan_id', str(len(self._loans)))
            loan_data['loan_id'] = loan_id
            loan_data['created_at'] = datetime.utcnow()
            loan_data['updated_at'] = datetime.utcnow()
            self._loans[loan_id] = loan_data
            return loan_id
        else:
            loan_data['created_at'] = datetime.utcnow()
            loan_data['updated_at'] = datetime.utcnow()
            result = self._db.loans.insert_one(loan_data)
            return str(result.inserted_id)

    def update_loan(self, loan_id: str, updates: Dict[str, Any]) -> bool:
        """Update loan information."""
        if self._use_stub:
            if loan_id in self._loans:
                self._loans[loan_id].update(updates)
                return True
            return False
        else:
            from bson import ObjectId
            updates['updated_at'] = datetime.utcnow()
            result = self._db.loans.update_one(
                {'_id': ObjectId(loan_id)},
                {'$set': updates}
            )
            return result.modified_count > 0

    def store_agent_decision(self, decision: Dict[str, Any]) -> None:
        """Store agent decision with validation."""
        try:
            if "timestamp" not in decision:
                decision["timestamp"] = datetime.utcnow()
            if DecisionDoc:
                DecisionDoc(**decision)  # validation
            
            if self._use_stub:
                # idempotency: unique (agent_id, loan_id, timestamp minute)
                key = (decision["agent_id"], decision["loan_id"], str(decision["timestamp"])[:16])
                if any((d.get("agent_id"), d.get("loan_id"), str(d.get("timestamp"))[:16]) == key 
                       for d in self._decisions):
                    return
                self._decisions.append(dict(decision))
            else:
                self._db.decisions.update_one(
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

    def store_context(self, agent_name: str, context_type: str,
                     data: Dict[str, Any], embedding: Optional[List[float]] = None) -> str:
        """Store agent context with optional embedding for semantic search."""
        context_doc = {
            'agent_name': agent_name,
            'context_type': context_type,
            'data': data,
            'timestamp': datetime.utcnow(),
        }
        if embedding:
            context_doc['embedding'] = embedding
        
        if self._use_stub:
            self._contexts.append(context_doc)
            return str(len(self._contexts) - 1)
        else:
            result = self._db.contexts.insert_one(context_doc)
            return str(result.inserted_id)

    def get_contexts(self, agent_name: Optional[str] = None,
                    context_type: Optional[str] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """Get agent contexts with optional filtering."""
        if self._use_stub:
            filtered = self._contexts
            if agent_name:
                filtered = [c for c in filtered if c.get('agent_name') == agent_name]
            if context_type:
                filtered = [c for c in filtered if c.get('context_type') == context_type]
            return sorted(filtered, key=lambda x: x.get('timestamp', datetime.min), reverse=True)[:limit]
        else:
            query = {}
            if agent_name:
                query['agent_name'] = agent_name
            if context_type:
                query['context_type'] = context_type
            return list(self._db.contexts.find(query).sort('timestamp', -1).limit(limit))

    def store_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """Store transaction (investment, payment, spending)."""
        transaction_data['timestamp'] = datetime.utcnow()
        
        if self._use_stub:
            self._transactions.append(transaction_data)
            return str(len(self._transactions) - 1)
        else:
            result = self._db.transactions.insert_one(transaction_data)
            return str(result.inserted_id)

    def get_transactions(self, loan_id: Optional[str] = None,
                        transaction_type: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get transactions with optional filtering."""
        if self._use_stub:
            filtered = self._transactions
            if loan_id:
                filtered = [t for t in filtered if t.get('loan_id') == loan_id]
            if transaction_type:
                filtered = [t for t in filtered if t.get('type') == transaction_type]
            return sorted(filtered, key=lambda x: x.get('timestamp', datetime.min), reverse=True)[:limit]
        else:
            query = {}
            if loan_id:
                query['loan_id'] = loan_id
            if transaction_type:
                query['type'] = transaction_type
            return list(self._db.transactions.find(query).sort('timestamp', -1).limit(limit))

    def get_database(self):
        """Get the underlying database object."""
        if self._use_stub:
            return self
        return self._db
    
    def close(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()


# Legacy alias for backward compatibility
InMemoryMongoStub = MongoDBClient


def get_mongo_client() -> MongoDBClient:
    """
    Factory function to get a MongoDB client.
    
    Returns:
        MongoDBClient instance configured based on environment.
    """
    return MongoDBClient()
