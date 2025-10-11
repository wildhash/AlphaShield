"""Loan models for AlphaShield system."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class LoanStatus(Enum):
    """Loan status enumeration."""
    PENDING = "pending"
    ACTIVE = "active"
    PAID_OFF = "paid_off"
    DEFAULTED = "defaulted"


@dataclass
class LoanSplit:
    """Represents the 60/40 split of loan funds."""
    total_amount: float
    investment_amount: float  # 60%
    borrower_amount: float    # 40%
    
    @classmethod
    def from_total(cls, total: float) -> 'LoanSplit':
        """Create loan split from total amount.
        
        Args:
            total: Total loan amount
            
        Returns:
            LoanSplit with 60% to investment, 40% to borrower.
        """
        return cls(
            total_amount=total,
            investment_amount=total * 0.6,
            borrower_amount=total * 0.4
        )


@dataclass
class Loan:
    """Represents a self-funding loan in the AlphaShield system."""
    borrower_id: str
    principal: float
    interest_rate: float
    term_months: int
    status: LoanStatus = LoanStatus.PENDING
    loan_id: Optional[str] = None
    created_at: Optional[datetime] = None
    split: Optional[LoanSplit] = None
    investment_balance: float = 0.0
    outstanding_balance: float = 0.0
    monthly_payment: float = 0.0
    
    def __post_init__(self):
        """Initialize computed fields."""
        if self.split is None:
            self.split = LoanSplit.from_total(self.principal)
        if self.outstanding_balance == 0.0:
            self.outstanding_balance = self.principal
        if self.monthly_payment == 0.0:
            self.monthly_payment = self.calculate_monthly_payment()
        if self.investment_balance == 0.0:
            self.investment_balance = self.split.investment_amount
            
    def calculate_monthly_payment(self) -> float:
        """Calculate monthly payment using standard amortization formula.
        
        Returns:
            Monthly payment amount.
        """
        if self.interest_rate == 0:
            return self.principal / self.term_months
        
        monthly_rate = self.interest_rate / 12 / 100
        numerator = self.principal * monthly_rate * (1 + monthly_rate) ** self.term_months
        denominator = (1 + monthly_rate) ** self.term_months - 1
        return numerator / denominator
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert loan to dictionary for storage."""
        return {
            'borrower_id': self.borrower_id,
            'principal': self.principal,
            'interest_rate': self.interest_rate,
            'term_months': self.term_months,
            'status': self.status.value,
            'split': {
                'total_amount': self.split.total_amount,
                'investment_amount': self.split.investment_amount,
                'borrower_amount': self.split.borrower_amount,
            },
            'investment_balance': self.investment_balance,
            'outstanding_balance': self.outstanding_balance,
            'monthly_payment': self.monthly_payment,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Loan':
        """Create loan from dictionary."""
        split = LoanSplit(**data['split']) if 'split' in data else None
        status = LoanStatus(data.get('status', 'pending'))
        
        return cls(
            loan_id=str(data.get('_id', '')),
            borrower_id=data['borrower_id'],
            principal=data['principal'],
            interest_rate=data['interest_rate'],
            term_months=data['term_months'],
            status=status,
            split=split,
            investment_balance=data.get('investment_balance', 0.0),
            outstanding_balance=data.get('outstanding_balance', 0.0),
            monthly_payment=data.get('monthly_payment', 0.0),
            created_at=data.get('created_at'),
        )
