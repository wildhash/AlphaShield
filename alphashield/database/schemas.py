from __future__ import annotations

from datetime import datetime
from typing import Any

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
    allocation: dict[str, float]
    coverage_ratio: float
    metrics: dict[str, Any]
    rationale: list[str]
    policy_version: int | None = None
