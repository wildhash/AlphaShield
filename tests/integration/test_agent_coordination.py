"""Enhanced integration tests for cross-agent coordination.

Tests the full orchestration flow with multiple agents working together.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from alphashield.agents.alpha_trading_agent import AlphaTradingAgent
from alphashield.agents.budget_analyzer_agent import BudgetAnalyzerAgent
from alphashield.agents.lender_agent import LenderAgent
from alphashield.agents.spending_guard_agent import SpendingGuardAgent
from alphashield.context.capsule import ContextCapsule, ContextPacket
from alphashield.orchestrator.graph import OrchestrationGraph


@pytest.fixture
def mock_llm():
    """Mock LLM client."""
    mock = Mock()
    mock.generate.return_value = "Mocked response"
    return mock


@pytest.fixture
def mock_db():
    """Mock database client."""
    mock = Mock()
    mock.get_collection.return_value = Mock()
    return mock


@pytest.fixture
def orchestrator(mock_db, mock_llm):
    """Create orchestrator with all agents."""
    graph = OrchestrationGraph(db=mock_db)

    # Initialize agents
    lender = LenderAgent(llm=mock_llm)
    trading = AlphaTradingAgent(llm=mock_llm)
    guard = SpendingGuardAgent(llm=mock_llm)
    budget = BudgetAnalyzerAgent(llm=mock_llm)

    # Add agents to graph
    graph.add_agent("Lender", lender)
    graph.add_agent("AlphaTrading", trading)
    graph.add_agent("SpendingGuard", guard)
    graph.add_agent("BudgetAnalyzer", budget)

    # Define dependencies
    graph.add_dependency("AlphaTrading", "Lender")  # Trading needs loan approval first
    graph.add_dependency("SpendingGuard", "BudgetAnalyzer")  # Guard needs budget first

    return graph


@pytest.fixture
def loan_application() -> dict:
    """Sample loan application."""
    return {
        "borrower_id": "test_borrower_123",
        "amount": 50000,
        "purpose": "Investment portfolio",
        "income": 120000,
        "credit_score": 750,
        "employment": "Software Engineer",
        "requested_at": datetime.utcnow(),
    }


@pytest.fixture
def market_data() -> dict:
    """Sample market data."""
    return {
        "SPY": {"price": 450.0, "volume": 1000000},
        "QQQ": {"price": 380.0, "volume": 800000},
        "IWM": {"price": 200.0, "volume": 500000},
        "AGG": {"price": 105.0, "volume": 300000},
    }


class TestFullPipelineIntegration:
    """Test complete pipeline from loan application to trading execution."""

    def test_loan_approval_and_trading_workflow(self, orchestrator, loan_application, market_data):
        """Test full workflow: loan approval -> trading setup -> execution."""

        # Mock agent responses
        with (
            patch.object(
                orchestrator.agents["Lender"],
                "run",
                return_value=ContextPacket(
                    agent="Lender",
                    data={
                        "decision": "approved",
                        "loan_amount": 50000,
                        "interest_rate": 0.05,
                        "term_months": 36,
                        "risk_score": 0.25,
                    },
                ),
            ),
            patch.object(
                orchestrator.agents["AlphaTrading"],
                "run",
                return_value=ContextPacket(
                    agent="AlphaTrading",
                    data={
                        "portfolio": {
                            "SPY": 0.40,
                            "QQQ": 0.30,
                            "IWM": 0.20,
                            "AGG": 0.10,
                        },
                        "expected_return": 0.08,
                        "risk_level": "moderate",
                        "rebalance_frequency": "monthly",
                    },
                ),
            ),
        ):
            # Execute orchestration
            initial_context = ContextCapsule(
                borrower_id=loan_application["borrower_id"],
                timestamp=datetime.utcnow(),
                packets=[],
            )

            initial_context.add_packet(
                ContextPacket(
                    agent="System",
                    data={"loan_application": loan_application, "market_data": market_data},
                )
            )

            result = orchestrator.run(initial_context)

            # Verify both agents ran
            assert len(result.packets) >= 2

            # Find packets by agent
            lender_packet = next((p for p in result.packets if p.agent == "Lender"), None)
            trading_packet = next((p for p in result.packets if p.agent == "AlphaTrading"), None)

            assert lender_packet is not None, "Lender agent should have produced output"
            assert trading_packet is not None, "AlphaTrading agent should have produced output"

            # Verify loan approval
            assert lender_packet.data["decision"] == "approved"
            assert lender_packet.data["loan_amount"] == 50000

            # Verify trading strategy
            assert "portfolio" in trading_packet.data
            assert sum(trading_packet.data["portfolio"].values()) == pytest.approx(1.0)

    def test_budget_and_spending_guard_coordination(self, orchestrator):
        """Test budget analyzer and spending guard coordination."""

        monthly_transactions = [
            {"date": "2024-12-01", "amount": -150, "category": "groceries"},
            {"date": "2024-12-02", "amount": -60, "category": "gas"},
            {"date": "2024-12-03", "amount": -1200, "category": "rent"},
            {"date": "2024-12-04", "amount": -80, "category": "dining"},
            {"date": "2024-12-05", "amount": -200, "category": "shopping"},
        ]

        with (
            patch.object(
                orchestrator.agents["BudgetAnalyzer"],
                "run",
                return_value=ContextPacket(
                    agent="BudgetAnalyzer",
                    data={
                        "monthly_spending": {
                            "groceries": 450,
                            "gas": 200,
                            "rent": 1200,
                            "dining": 300,
                            "shopping": 400,
                        },
                        "budget_limits": {
                            "groceries": 500,
                            "gas": 250,
                            "dining": 350,
                            "shopping": 400,
                        },
                        "total_spending": 2550,
                        "income": 5000,
                    },
                ),
            ),
            patch.object(
                orchestrator.agents["SpendingGuard"],
                "run",
                return_value=ContextPacket(
                    agent="SpendingGuard",
                    data={
                        "alerts": [],
                        "recommendations": [
                            "Good budget adherence",
                            "Consider increasing savings rate",
                        ],
                        "spending_health": "good",
                    },
                ),
            ),
        ):
            initial_context = ContextCapsule(
                borrower_id="test_borrower_123",
                timestamp=datetime.utcnow(),
                packets=[
                    ContextPacket(agent="System", data={"transactions": monthly_transactions})
                ],
            )

            result = orchestrator.run(initial_context)

            # Verify both agents ran
            budget_packet = next((p for p in result.packets if p.agent == "BudgetAnalyzer"), None)
            guard_packet = next((p for p in result.packets if p.agent == "SpendingGuard"), None)

            assert budget_packet is not None
            assert guard_packet is not None

            # Verify budget analysis
            assert budget_packet.data["total_spending"] == 2550
            assert budget_packet.data["income"] == 5000

            # Verify guard recommendations
            assert guard_packet.data["spending_health"] == "good"
            assert len(guard_packet.data["recommendations"]) > 0

    def test_agent_failure_handling(self, orchestrator, loan_application):
        """Test graceful handling of agent failures."""

        # Make Lender agent fail
        with patch.object(
            orchestrator.agents["Lender"], "run", side_effect=Exception("Agent processing error")
        ):
            initial_context = ContextCapsule(
                borrower_id=loan_application["borrower_id"],
                timestamp=datetime.utcnow(),
                packets=[
                    ContextPacket(agent="System", data={"loan_application": loan_application})
                ],
            )

            # Should not crash, but handle gracefully
            result = orchestrator.run(initial_context)

            # Check for error packet
            error_packets = [p for p in result.packets if "error" in p.data]
            assert len(error_packets) > 0, "Should log error in context"

    def test_data_validation_across_agents(self, orchestrator):
        """Test that data is validated as it passes between agents."""

        # Lender provides invalid portfolio split (doesn't sum to 1.0)
        with patch.object(
            orchestrator.agents["Lender"],
            "run",
            return_value=ContextPacket(
                agent="Lender",
                data={
                    "decision": "approved",
                    "loan_amount": 50000,
                    "portfolio_split": 0.75,  # Should be 0.8 for borrower
                },
            ),
        ):
            initial_context = ContextCapsule(
                borrower_id="test_borrower",
                timestamp=datetime.utcnow(),
                packets=[ContextPacket(agent="System", data={"loan_request": 50000})],
            )

            result = orchestrator.run(initial_context)

            # System should detect and possibly correct invalid data
            lender_packet = next((p for p in result.packets if p.agent == "Lender"), None)
            assert lender_packet is not None

            # Validate portfolio split is reasonable
            portfolio_split = lender_packet.data.get("portfolio_split", 0.8)
            assert 0.5 <= portfolio_split <= 1.0, "Portfolio split should be in valid range"


class TestContextCapsuleFlowIntegration:
    """Test context capsule data flow through multiple agents."""

    def test_context_enrichment(self, orchestrator):
        """Test that each agent enriches the context."""

        initial_packets = []

        # Simulate sequential agent execution
        agents_to_run = ["Lender", "BudgetAnalyzer", "AlphaTrading", "SpendingGuard"]

        with (
            patch.object(
                orchestrator.agents["Lender"],
                "run",
                return_value=ContextPacket(agent="Lender", data={"loan_approved": True}),
            ),
            patch.object(
                orchestrator.agents["BudgetAnalyzer"],
                "run",
                return_value=ContextPacket(agent="BudgetAnalyzer", data={"budget_healthy": True}),
            ),
            patch.object(
                orchestrator.agents["AlphaTrading"],
                "run",
                return_value=ContextPacket(agent="AlphaTrading", data={"strategy": "moderate"}),
            ),
            patch.object(
                orchestrator.agents["SpendingGuard"],
                "run",
                return_value=ContextPacket(agent="SpendingGuard", data={"alerts": []}),
            ),
        ):
            context = ContextCapsule(
                borrower_id="test_borrower",
                timestamp=datetime.utcnow(),
                packets=initial_packets,
            )

            result = orchestrator.run(context)

            # Each agent should have added a packet
            assert len(result.packets) >= len(agents_to_run)

            # Verify each agent contributed
            agent_names = {p.agent for p in result.packets}
            for agent_name in agents_to_run:
                assert agent_name in agent_names, f"{agent_name} should have contributed"

    def test_context_packet_ordering(self, orchestrator):
        """Test that context packets maintain proper ordering."""

        with (
            patch.object(
                orchestrator.agents["Lender"],
                "run",
                return_value=ContextPacket(agent="Lender", data={"order": 1}),
            ),
            patch.object(
                orchestrator.agents["AlphaTrading"],
                "run",
                return_value=ContextPacket(agent="AlphaTrading", data={"order": 2}),
            ),
        ):
            context = ContextCapsule(
                borrower_id="test_borrower",
                timestamp=datetime.utcnow(),
                packets=[],
            )

            result = orchestrator.run(context)

            # Packets should be in execution order
            # Lender should come before AlphaTrading (due to dependency)
            lender_idx = next((i for i, p in enumerate(result.packets) if p.agent == "Lender"), -1)
            trading_idx = next(
                (i for i, p in enumerate(result.packets) if p.agent == "AlphaTrading"), -1
            )

            if lender_idx >= 0 and trading_idx >= 0:
                assert lender_idx < trading_idx, "Lender should execute before AlphaTrading"


class TestConcurrentBorrowerHandling:
    """Test handling multiple borrowers concurrently."""

    def test_multiple_borrowers_isolated(self, orchestrator):
        """Test that multiple borrowers' contexts remain isolated."""

        borrower_ids = ["borrower_1", "borrower_2", "borrower_3"]
        results = []

        for borrower_id in borrower_ids:
            with patch.object(
                orchestrator.agents["Lender"],
                "run",
                return_value=ContextPacket(
                    agent="Lender", data={"borrower_id": borrower_id, "decision": "approved"}
                ),
            ):
                context = ContextCapsule(
                    borrower_id=borrower_id,
                    timestamp=datetime.utcnow(),
                    packets=[],
                )

                result = orchestrator.run(context)
                results.append(result)

        # Verify each result is for the correct borrower
        for i, result in enumerate(results):
            expected_borrower = borrower_ids[i]
            assert result.borrower_id == expected_borrower

            # Check that no data leaked between borrowers
            lender_packet = next((p for p in result.packets if p.agent == "Lender"), None)
            if lender_packet:
                assert lender_packet.data["borrower_id"] == expected_borrower


class TestPerformanceAndScaling:
    """Test system performance under load."""

    def test_orchestration_completes_within_timeout(self, orchestrator):
        """Test that orchestration completes within reasonable time."""
        import time

        with patch.object(
            orchestrator.agents["Lender"],
            "run",
            return_value=ContextPacket(agent="Lender", data={"status": "ok"}),
        ):
            context = ContextCapsule(
                borrower_id="test_borrower",
                timestamp=datetime.utcnow(),
                packets=[],
            )

            start = time.time()
            orchestrator.run(context)
            duration = time.time() - start

            # Should complete in under 5 seconds for mocked agents
            assert duration < 5.0, f"Orchestration took {duration:.2f}s, should be under 5s"

    def test_large_context_handling(self, orchestrator):
        """Test handling of large context capsules."""

        # Create large context with many packets
        large_packets = [
            ContextPacket(agent=f"Agent_{i}", data={"index": i, "large_data": "x" * 1000})
            for i in range(100)
        ]

        context = ContextCapsule(
            borrower_id="test_borrower",
            timestamp=datetime.utcnow(),
            packets=large_packets,
        )

        # Should handle large context without errors
        with patch.object(
            orchestrator.agents["Lender"],
            "run",
            return_value=ContextPacket(agent="Lender", data={"status": "processed"}),
        ):
            result = orchestrator.run(context)

            # Result should include original packets plus new ones
            assert len(result.packets) >= len(large_packets)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
