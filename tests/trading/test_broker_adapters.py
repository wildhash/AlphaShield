"""Tests for broker adapters."""

from unittest.mock import patch

import pytest

from alphashield.trading.broker_adapters import (
    AlpacaAdapter,
    OrderSide,
    OrderStatus,
    OrderType,
    PaperTradingAdapter,
)


class TestPaperTradingAdapter:
    """Test paper trading adapter."""

    def test_initialization(self):
        """Test adapter initialization."""
        adapter = PaperTradingAdapter(initial_cash=100_000.0)

        account = adapter.get_account()
        assert account.cash == 100_000.0
        assert account.portfolio_value == 100_000.0

    def test_submit_market_order_buy(self):
        """Test submitting a market buy order."""
        adapter = PaperTradingAdapter(initial_cash=100_000.0)
        adapter.set_price("AAPL", 150.0)

        order = adapter.submit_order(
            ticker="AAPL",
            qty=100,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
        )

        assert order.status == OrderStatus.FILLED
        assert order.ticker == "AAPL"
        assert order.quantity == 100
        assert order.filled_quantity == 100

        # Check cash decreased
        account = adapter.get_account()
        assert account.cash < 100_000.0

        # Check position created
        position = adapter.get_position("AAPL")
        assert position is not None
        assert position.quantity == 100

    def test_submit_market_order_sell(self):
        """Test submitting a market sell order."""
        adapter = PaperTradingAdapter(initial_cash=100_000.0)
        adapter.set_price("AAPL", 150.0)

        # First buy
        adapter.submit_order(
            ticker="AAPL",
            qty=100,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
        )

        # Then sell
        order = adapter.submit_order(
            ticker="AAPL",
            qty=50,
            side=OrderSide.SELL,
            type=OrderType.MARKET,
        )

        assert order.status == OrderStatus.FILLED
        assert order.quantity == 50

        # Check position reduced
        position = adapter.get_position("AAPL")
        assert position is not None
        assert position.quantity == 50

    def test_insufficient_funds(self):
        """Test order rejection due to insufficient funds."""
        adapter = PaperTradingAdapter(initial_cash=1_000.0)
        adapter.set_price("AAPL", 150.0)

        # Try to buy 100 shares (needs $15,000+)
        order = adapter.submit_order(
            ticker="AAPL",
            qty=100,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
        )

        assert order.status == OrderStatus.REJECTED
        assert "Insufficient funds" in order.error_message

    def test_insufficient_shares(self):
        """Test order rejection due to insufficient shares."""
        adapter = PaperTradingAdapter(initial_cash=100_000.0)
        adapter.set_price("AAPL", 150.0)

        # Try to sell without owning shares
        order = adapter.submit_order(
            ticker="AAPL",
            qty=100,
            side=OrderSide.SELL,
            type=OrderType.MARKET,
        )

        assert order.status == OrderStatus.REJECTED
        assert "Insufficient shares" in order.error_message

    def test_get_positions(self):
        """Test getting all positions."""
        adapter = PaperTradingAdapter(initial_cash=100_000.0)
        adapter.set_prices({"AAPL": 150.0, "GOOGL": 2800.0})

        # Buy multiple positions
        adapter.submit_order("AAPL", 100, OrderSide.BUY, OrderType.MARKET)
        adapter.submit_order("GOOGL", 10, OrderSide.BUY, OrderType.MARKET)

        positions = adapter.get_positions()
        assert len(positions) == 2

        tickers = {pos.ticker for pos in positions}
        assert "AAPL" in tickers
        assert "GOOGL" in tickers

    def test_close_position(self):
        """Test closing a position."""
        adapter = PaperTradingAdapter(initial_cash=100_000.0)
        adapter.set_price("AAPL", 150.0)

        # Buy shares
        adapter.submit_order("AAPL", 100, OrderSide.BUY, OrderType.MARKET)

        # Close position
        order = adapter.close_position("AAPL")

        assert order.status == OrderStatus.FILLED
        assert order.side == OrderSide.SELL
        assert order.quantity == 100

        # Position should be closed
        position = adapter.get_position("AAPL")
        assert position is None

    def test_get_quote(self):
        """Test getting a quote."""
        adapter = PaperTradingAdapter()
        adapter.set_price("AAPL", 150.0)

        quote = adapter.get_quote("AAPL")

        assert "bid" in quote
        assert "ask" in quote
        assert "last" in quote
        assert quote["last"] == 150.0
        assert quote["bid"] < quote["ask"]


@pytest.mark.skip(reason="Requires Alpaca API credentials")
class TestAlpacaAdapter:
    """Test Alpaca adapter (requires credentials)."""

    def test_initialization_without_credentials(self):
        """Test that initialization fails without credentials."""
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ValueError, match="credentials required"),
        ):
            AlpacaAdapter()

    @patch.dict(
        "os.environ",
        {
            "ALPACA_API_KEY": "test_key",
            "ALPACA_SECRET_KEY": "test_secret",
        },
    )
    def test_initialization_with_env_vars(self):
        """Test initialization with environment variables."""
        # This will still fail without alpaca-py installed
        # but tests that env var loading works
        try:
            adapter = AlpacaAdapter()
            assert adapter.api_key == "test_key"
            assert adapter.secret_key == "test_secret"
            assert adapter.paper is True
        except ImportError:
            pytest.skip("alpaca-py not installed")

    @patch.dict(
        "os.environ",
        {
            "ALPACA_API_KEY": "test_key",
            "ALPACA_SECRET_KEY": "test_secret",
        },
    )
    def test_paper_vs_live_urls(self):
        """Test that paper and live mode use different URLs."""
        try:
            paper_adapter = AlpacaAdapter(paper=True)
            assert "paper" in paper_adapter.base_url.lower()

            live_adapter = AlpacaAdapter(paper=False)
            assert "paper" not in live_adapter.base_url.lower()
        except ImportError:
            pytest.skip("alpaca-py not installed")


class TestExecutionEngineWithBrokers:
    """Test execution engine with broker adapters."""

    def test_execution_engine_with_paper_adapter(self):
        """Test execution engine integration with paper adapter."""
        from alphashield.trading.execution_engine import ExecutionEngine

        adapter = PaperTradingAdapter(initial_cash=100_000.0)
        adapter.set_prices(
            {
                "AAPL": 150.0,
                "GOOGL": 2800.0,
                "MSFT": 370.0,
            }
        )

        engine = ExecutionEngine(broker=adapter)

        # Test rebalance
        target_weights = {
            "AAPL": 0.4,
            "GOOGL": 0.3,
            "MSFT": 0.3,
        }

        confirmations = engine.execute_rebalance(
            current_positions={},
            target_weights=target_weights,
            total_value=100_000.0,
        )

        # Should have 3 buy orders
        assert len(confirmations) == 3
        assert "AAPL" in confirmations
        assert "GOOGL" in confirmations
        assert "MSFT" in confirmations

        # Check that positions were created
        positions = adapter.get_positions()
        assert len(positions) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
