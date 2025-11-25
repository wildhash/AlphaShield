from __future__ import annotations

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from alphashield.utils.errors import ExecutionError
from alphashield.database.schemas import DecisionDoc


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

    def get_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get loan by ID."""
        if self._use_stub:
            return self._loans.get(loan_id)
        return self._db.loans.find_one({"loan_id": loan_id})

    def set_loan(self, loan: Dict[str, Any]) -> None:
        """Store or update a loan."""
        if self._use_stub:
            self._loans[loan["loan_id"]] = loan
        else:
            self._db.loans.update_one(
                {"loan_id": loan["loan_id"]}, 
                {"$set": loan}, 
                upsert=True
            )

    def store_agent_decision(self, decision: Dict[str, Any]) -> None:
        """Store an agent decision with validation."""
        try:
            if "timestamp" not in decision:
                decision["timestamp"] = datetime.utcnow()
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
