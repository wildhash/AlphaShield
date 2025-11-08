from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field


class LoanDoc(BaseModel):
    loan_id: str
    principal: float
    rate: float
    term_months: int
    borrower_id: str
    monthly_payment: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DecisionDoc(BaseModel):
    agent_id: str
    loan_id: str
    timestamp: datetime
    allocation: Dict[str, float]
    coverage_ratio: float
    metrics: Dict[str, Any]
    rationale: List[str]
    policy_version: Optional[int] = None
