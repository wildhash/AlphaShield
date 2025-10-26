from __future__ import annotations

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from alphashield.utils.errors import ExecutionError
from alphashield.database.schemas import DecisionDoc


class InMemoryMongoStub:
    def __init__(self) -> None:
        self.loans: Dict[str, Dict[str, Any]] = {}
        self.decisions: List[Dict[str, Any]] = []

    def get_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        return self.loans.get(loan_id)

    def set_loan(self, loan: Dict[str, Any]) -> None:
        self.loans[loan["loan_id"]] = loan

    def store_agent_decision(self, decision: Dict[str, Any]) -> None:
        # Validate via Pydantic, augment timestamp if missing
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
    url = os.getenv("MONGO_URL") or os.getenv("MONGODB_URI")
    if not url:
        return InMemoryMongoStub()
    try:
        from pymongo import MongoClient  # type: ignore
        client = MongoClient(url)
        db = client.get_database()

        class _RealClient:
            def get_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
                return db.loans.find_one({"loan_id": loan_id})

            def set_loan(self, loan: Dict[str, Any]) -> None:
                db.loans.update_one({"loan_id": loan["loan_id"]}, {"$set": loan}, upsert=True)

            def store_agent_decision(self, decision: Dict[str, Any]) -> None:
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
