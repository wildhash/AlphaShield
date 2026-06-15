"""Context packet for agent orchestration."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ContextPacket:
    """Context packet passed through the orchestration DAG.

    Contains trace_id, user_id, loan_app_id, and accumulated context
    from each agent in the workflow.
    """

    trace_id: str
    user_id: str
    loan_app_id: str

    # Accumulated context from agents
    context: dict[str, Any] = field(default_factory=dict)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def add_context(self, agent_name: str, data: dict[str, Any]) -> None:
        """Add context from an agent.

        Args:
            agent_name: Name of the agent
            data: Context data from the agent
        """
        self.context[agent_name] = {
            "data": data,
            "timestamp": datetime.utcnow(),
            "input_hash": self._hash_data(data),
        }

    def get_context(self, agent_name: str) -> dict[str, Any] | None:
        """Get context from a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Context data if available, None otherwise
        """
        agent_ctx = self.context.get(agent_name)
        if agent_ctx:
            return agent_ctx.get("data")
        return None

    @staticmethod
    def _hash_data(data: dict[str, Any]) -> str:
        """Create a hash of the data for audit trail.

        Args:
            data: Data to hash

        Returns:
            SHA256 hash of the data
        """
        # Convert dict to sorted string for consistent hashing
        data_str = str(sorted(data.items()))
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "user_id": self.user_id,
            "loan_app_id": self.loan_app_id,
            "context": self.context,
            "timestamp": self.timestamp,
        }


def make_packet(trace_id: str, user_id: str, loan_app_id: str) -> ContextPacket:
    """Create a new context packet.

    Args:
        trace_id: Unique trace identifier for this execution
        user_id: User identifier
        loan_app_id: Loan application identifier

    Returns:
        New ContextPacket instance
    """
    return ContextPacket(
        trace_id=trace_id,
        user_id=user_id,
        loan_app_id=loan_app_id,
    )
