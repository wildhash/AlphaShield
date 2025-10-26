from __future__ import annotations

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from alphashield.utils.errors import ExecutionError
from alphashield.database.schemas import DecisionDoc


class InMemoryMongoStub:
    def __init__(self) -> None:
        """
        Initialize the in-memory MongoDB stub.
        
        Creates empty in-memory storage structures:
        - `loans`: mapping of loan_id to loan data
        - `decisions`: list of stored decision records
        """
        self.loans: Dict[str, Dict[str, Any]] = {}
        self.decisions: List[Dict[str, Any]] = []

    def get_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """
        Return the loan record for the given loan_id from the in-memory store.
        
        Parameters:
            loan_id (str): Identifier of the loan to retrieve.
        
        Returns:
            dict: The loan data for the given loan_id, or None if no matching loan exists.
        """
        return self.loans.get(loan_id)

    def set_loan(self, loan: Dict[str, Any]) -> None:
        """
        Store or update a loan entry in the in-memory store using its loan_id.
        
        Parameters:
            loan (Dict[str, Any]): Loan document containing a "loan_id" key; the loan is stored under loan["loan_id"], replacing any existing entry with the same id.
        """
        self.loans[loan["loan_id"]] = loan

    def store_agent_decision(self, decision: Dict[str, Any]) -> None:
        # Validate via Pydantic, augment timestamp if missing
        """
        Store a validated agent decision in the in-memory decisions list with minute-level idempotency.
        
        If `timestamp` is missing, a UTC timestamp is added. The decision is validated against DecisionDoc and appended to self.decisions only if there is no existing decision with the same `agent_id`, `loan_id`, and the same timestamp truncated to the minute. If a duplicate is detected, the function returns without modifying storage.
        
        Parameters:
            decision (Dict[str, Any]): Mapping containing decision fields. Must include `agent_id` and `loan_id`; `timestamp` is optional.
        
        Raises:
            ExecutionError: If validation or storage fails.
        """
        try:
            if "timestamp" not in decision:
                decision["timestamp"] = datetime.utcnow()
            DecisionDoc(**decision)  # validation
            # idempotency: unique (agent_id, loan_id, timestamp minute) simplistic
            key = (decision["agent_id"], decision["loan_id"], str(decision["timestamp"])[:16])
            if any((d.get("agent_id"), d.get("loan_id"), str(d.get("timestamp"))[:16]) == key for d in self.decisions):
                return
            self.decisions.append(dict(decision))
        except Exception as e:
            raise ExecutionError(f"decision validation/store failed: {e}")


def get_mongo_client():
    """
    Obtain a database client configured from environment or an in-memory fallback.
    
    If the environment contains MONGO_URL or MONGODB_URI, returns a MongoDB-backed client using pymongo; if the URL is missing or any setup error occurs, returns an InMemoryMongoStub. The returned client exposes the methods `get_loan(loan_id)`, `set_loan(loan)`, and `store_agent_decision(decision)`.
    
    Returns:
        client: An object exposing `get_loan(loan_id)`, `set_loan(loan)`, and `store_agent_decision(decision)`; backed by MongoDB when a connection URL is configured, otherwise an `InMemoryMongoStub`.
    """
    url = os.getenv("MONGO_URL") or os.getenv("MONGODB_URI")
    if not url:
        return InMemoryMongoStub()
    try:
        from pymongo import MongoClient  # type: ignore
        client = MongoClient(url)
        db = client.get_database()

        class _RealClient:
            def get_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
                """
                Retrieve a loan document by its loan_id.
                
                Parameters:
                    loan_id (str): The loan identifier to look up.
                
                Returns:
                    Optional[Dict[str, Any]]: The loan document as a dictionary if found, otherwise None.
                """
                return db.loans.find_one({"loan_id": loan_id})

            def set_loan(self, loan: Dict[str, Any]) -> None:
                """
                Upserts the provided loan document into the loans collection using its loan_id as the key.
                
                Parameters:
                    loan (Dict[str, Any]): Loan document to store; must include a "loan_id" key. The document will replace existing fields for that loan_id or be inserted if none exists.
                """
                db.loans.update_one({"loan_id": loan["loan_id"]}, {"$set": loan}, upsert=True)

            def store_agent_decision(self, decision: Dict[str, Any]) -> None:
                """
                Store an agent decision, validating it and ensuring idempotent persistence.
                
                If the `decision` has no "timestamp", one is assigned using the current UTC time. The decision is validated against the DecisionDoc schema and then persisted; if a decision with the same `agent_id`, `loan_id`, and `timestamp` already exists, the call leaves storage unchanged.
                
                Parameters:
                    decision (Dict[str, Any]): A decision record containing at minimum `agent_id` and `loan_id`; may include `timestamp` and other decision fields.
                
                Raises:
                    ExecutionError: If validation or storage fails.
                """
                try:
                    if "timestamp" not in decision:
                        decision["timestamp"] = datetime.utcnow()
                    DecisionDoc(**decision)
                    db.decisions.update_one(
                        {
                            "agent_id": decision["agent_id"],
                            "loan_id": decision["loan_id"],
                            "timestamp": decision["timestamp"],
                        },
                        {"$setOnInsert": decision},
                        upsert=True,
                    )
                except Exception as e:
                    raise ExecutionError(f"mongo store failed: {e}")

        return _RealClient()
    except Exception:
        # Fallback to stub
        return InMemoryMongoStub()