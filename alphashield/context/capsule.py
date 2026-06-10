"""Financial context capsule for shared agent context."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ContextCapsule:
    """Aggregated financial context for a user.

    Contains rolling features from Mongo and top-k similar case IDs
    from vector store for shared agent context.
    """
    user_id: str | None = None

    # Rolling financial features from MongoDB
    rolling_features: dict[str, Any] = field(default_factory=dict)
    # e.g., {
    #   'avg_monthly_income': float,
    #   'avg_monthly_spending': float,
    #   'credit_score': int,
    #   'debt_to_income_ratio': float,
    #   'payment_history_score': float,
    #   'spending_volatility': float,
    # }

    # Top-k similar case IDs from vector store
    similar_case_ids: list[str] = field(default_factory=list)

    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    borrower_id: str | None = None
    packets: list[ContextPacket] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Keep legacy borrower_id and user_id accessors aligned."""
        if self.user_id is None and self.borrower_id is None:
            raise ValueError("Either user_id or borrower_id must be provided")
        if self.user_id is None:
            self.user_id = self.borrower_id
        if self.borrower_id is None:
            self.borrower_id = self.user_id

    def add_packet(self, packet: ContextPacket) -> None:
        """Append an orchestration packet."""
        self.packets.append(packet)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            'user_id': self.user_id,
            'borrower_id': self.borrower_id,
            'rolling_features': self.rolling_features,
            'similar_case_ids': self.similar_case_ids,
            'packets': [packet.to_dict() for packet in self.packets],
            'timestamp': self.timestamp,
        }


@dataclass
class ContextPacket:
    """Compatibility packet used by orchestration integration tests."""

    agent: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert packet to dictionary."""
        return {
            'agent': self.agent,
            'data': self.data,
            'timestamp': self.timestamp,
        }


def build_financial_capsule(
    user_id: str,
    db_client=None,
    embeddings_client=None,
    top_k: int = 5
) -> ContextCapsule:
    """Build a financial context capsule for a user.

    Reads from MongoDB to aggregate rolling features and fetches top-k
    similar cases from vector store (IDs only).

    Args:
        user_id: User identifier
        db_client: MongoDB client for reading financial data
        embeddings_client: Embeddings client for vector similarity search
        top_k: Number of similar cases to retrieve

    Returns:
        ContextCapsule with aggregated financial context
    """
    rolling_features = {}
    similar_case_ids = []

    if db_client:
        # Aggregate rolling features from MongoDB
        # This would typically query user's historical data
        try:
            # Get user's financial history
            contexts = db_client.get_collection('agent_contexts').find(
                {'data.borrower_id': user_id}
            ).sort('timestamp', -1).limit(50)

            # Aggregate features
            income_values = []
            spending_values = []
            credit_scores = []

            for ctx in contexts:
                data = ctx.get('data', {})
                if 'monthly_gross_income' in data:
                    income_values.append(data['monthly_gross_income'])
                if 'average_monthly_spending' in data:
                    spending_values.append(data['average_monthly_spending'])
                if 'credit_score' in data:
                    credit_scores.append(data['credit_score'])

            # Calculate rolling averages
            if income_values:
                rolling_features['avg_monthly_income'] = sum(income_values) / len(income_values)
            if spending_values:
                rolling_features['avg_monthly_spending'] = sum(spending_values) / len(spending_values)
            if credit_scores:
                rolling_features['credit_score'] = int(sum(credit_scores) / len(credit_scores))

            # Calculate debt-to-income ratio if we have both
            if income_values and spending_values:
                avg_income = rolling_features['avg_monthly_income']
                avg_spending = rolling_features['avg_monthly_spending']
                if avg_income > 0:
                    rolling_features['debt_to_income_ratio'] = avg_spending / avg_income
        except Exception:
            # If aggregation fails, continue with empty features
            pass

    if embeddings_client:
        # This would do semantic search for similar borrower profiles.
        # For now, return an empty list until vector DB setup is available.
        similar_case_ids = []

    return ContextCapsule(
        user_id=user_id,
        rolling_features=rolling_features,
        similar_case_ids=similar_case_ids,
    )
