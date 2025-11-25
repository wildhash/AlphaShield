"""
Tests for Alpaca Broker Adapter

Tests the AlpacaAdapter implementation with mocked Alpaca SDK responses.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Add parent to path for imports
sys.path.insert(0, "/workspaces/AlphaShield")

from alphashield.trading.adapters.base import (
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)


class TestAlpacaAdapterBase:
    """Test base adapter functionality."""
    
    def test_order_side_enum(self):
        """Test OrderSide enum values."""
        assert OrderSide.BUY.value == "buy"
        assert OrderSide.SELL.value == "sell"
    
    def test_order_status_enum(self):
        """Test OrderStatus enum values."""
        assert OrderStatus.PENDING.value == "pending"
        assert OrderStatus.FILLED.value == "filled"
        assert OrderStatus.CANCELLED.value == "cancelled"
    
    def test_order_type_enum(self):
        """Test OrderType enum values."""
        assert OrderType.MARKET.value == "market"
        assert OrderType.LIMIT.value == "limit"
        assert OrderType.STOP.value == "stop"
    
    def test_time_in_force_enum(self):
        """Test TimeInForce enum values."""
        assert TimeInForce.DAY.value == "day"
        assert TimeInForce.GTC.value == "gtc"


class TestPosition:
    """Test Position dataclass."""
    
    def test_position_creation(self):
        """Test creating a Position."""
        from alphashield.trading.adapters.base import Position
        
        pos = Position(
            symbol="AAPL",
            quantity=Decimal("100"),
            avg_entry_price=Decimal("150.00"),
            market_value=Decimal("16000.00"),
            unrealized_pnl=Decimal("1000.00"),
            unrealized_pnl_pct=Decimal("6.67"),
            current_price=Decimal("160.00"),
            cost_basis=Decimal("15000.00"),
            side="long",
        )
        
        assert pos.symbol == "AAPL"
        assert pos.quantity == Decimal("100")
        assert pos.is_profitable is True
    
    def test_position_unprofitable(self):
        """Test unprofitable position."""
        from alphashield.trading.adapters.base import Position
        
        pos = Position(
            symbol="MSFT",
            quantity=Decimal("50"),
            avg_entry_price=Decimal("400.00"),
            market_value=Decimal("19000.00"),
            unrealized_pnl=Decimal("-1000.00"),
            unrealized_pnl_pct=Decimal("-5.00"),
            current_price=Decimal("380.00"),
            cost_basis=Decimal("20000.00"),
            side="long",
        )
        
        assert pos.is_profitable is False


class TestOrder:
    """Test Order dataclass."""
    
    def test_order_creation(self):
        """Test creating an Order."""
        from alphashield.trading.adapters.base import Order
        
        order = Order(
            id="order-123",
            client_order_id="client-456",
            symbol="SPY",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("10"),
            status=OrderStatus.FILLED,
        )
        
        assert order.id == "order-123"
        assert order.is_filled is True
        assert order.is_active is False
    
    def test_order_active(self):
        """Test active order detection."""
        from alphashield.trading.adapters.base import Order
        
        order = Order(
            id="order-789",
            client_order_id="client-012",
            symbol="QQQ",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("20"),
            limit_price=Decimal("400.00"),
            status=OrderStatus.SUBMITTED,
        )
        
        assert order.is_active is True
        assert order.is_filled is False


class TestQuote:
    """Test Quote dataclass."""
    
    def test_quote_spread(self):
        """Test quote spread calculation."""
        from alphashield.trading.adapters.base import Quote
        
        quote = Quote(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            bid=Decimal("150.00"),
            bid_size=100,
            ask=Decimal("150.05"),
            ask_size=200,
        )
        
        assert quote.spread == Decimal("0.05")
        assert quote.mid_price == Decimal("150.025")


class TestAccountInfo:
    """Test AccountInfo dataclass."""
    
    def test_account_info_creation(self):
        """Test creating AccountInfo."""
        from alphashield.trading.adapters.base import AccountInfo
        
        account = AccountInfo(
            account_id="acc-123",
            status="ACTIVE",
            buying_power=Decimal("50000.00"),
            cash=Decimal("25000.00"),
            portfolio_value=Decimal("100000.00"),
            equity=Decimal("100000.00"),
        )
        
        assert account.account_id == "acc-123"
        assert account.buying_power == Decimal("50000.00")
        assert account.pattern_day_trader is False


class TestBar:
    """Test Bar dataclass."""
    
    def test_bar_creation(self):
        """Test creating a Bar."""
        from alphashield.trading.adapters.base import Bar
        
        bar = Bar(
            symbol="SPY",
            timestamp=datetime.now(timezone.utc),
            open=Decimal("450.00"),
            high=Decimal("452.00"),
            low=Decimal("449.00"),
            close=Decimal("451.50"),
            volume=1000000,
        )
        
        assert bar.symbol == "SPY"
        assert bar.high > bar.low


class TestAlpacaAdapterInit:
    """Test AlpacaAdapter initialization."""
    
    def test_adapter_init_defaults(self):
        """Test adapter initialization with defaults."""
        from alphashield.trading.adapters.alpaca_adapter import AlpacaAdapter
        
        adapter = AlpacaAdapter()
        
        assert adapter.paper is True
        assert adapter.base_url == "https://paper-api.alpaca.markets"
        assert adapter.timeout == 30
        assert adapter.max_retries == 3
    
    def test_adapter_init_live(self):
        """Test adapter initialization for live trading."""
        from alphashield.trading.adapters.alpaca_adapter import AlpacaAdapter
        
        adapter = AlpacaAdapter(
            api_key="test-key",
            secret_key="test-secret",
            paper=False,
        )
        
        assert adapter.paper is False
        assert adapter.base_url == "https://api.alpaca.markets"
    
    def test_adapter_init_custom_settings(self):
        """Test adapter initialization with custom settings."""
        from alphashield.trading.adapters.alpaca_adapter import AlpacaAdapter
        
        adapter = AlpacaAdapter(
            api_key="custom-key",
            secret_key="custom-secret",
            timeout=60,
            max_retries=5,
        )
        
        assert adapter.api_key == "custom-key"
        assert adapter.timeout == 60
        assert adapter.max_retries == 5


class TestAlpacaAdapterMocked:
    """Test AlpacaAdapter with mocked Alpaca SDK."""
    
    @pytest.fixture
    def mock_alpaca_sdk(self):
        """Create mock Alpaca SDK modules."""
        # Mock the alpaca modules
        mock_trading_client = MagicMock()
        mock_data_client = MagicMock()
        
        return {
            "trading_client": mock_trading_client,
            "data_client": mock_data_client,
        }
    
    @pytest.mark.asyncio
    async def test_connect_without_credentials(self):
        """Test connection fails without credentials."""
        from alphashield.trading.adapters.alpaca_adapter import AlpacaAdapter
        from alphashield.trading.adapters.base import ConnectionError
        
        adapter = AlpacaAdapter(api_key="", secret_key="")
        
        # Mock the alpaca import to succeed
        adapter._alpaca_imported = True
        adapter._TradingClient = MagicMock()
        adapter._StockHistoricalDataClient = MagicMock()
        
        with pytest.raises(ConnectionError, match="API key and secret key are required"):
            await adapter.connect()
    
    @pytest.mark.asyncio
    async def test_get_positions_not_connected(self):
        """Test get_positions fails when not connected."""
        from alphashield.trading.adapters.alpaca_adapter import AlpacaAdapter
        from alphashield.trading.adapters.base import ConnectionError
        
        adapter = AlpacaAdapter(api_key="test", secret_key="test")
        adapter._connected = False
        adapter._client = None
        
        with pytest.raises(ConnectionError, match="Not connected"):
            await adapter.get_positions()
    
    @pytest.mark.asyncio
    async def test_submit_order_invalid_quantity(self):
        """Test submit_order fails with invalid quantity."""
        from alphashield.trading.adapters.alpaca_adapter import AlpacaAdapter
        from alphashield.trading.adapters.base import InvalidOrderError
        
        adapter = AlpacaAdapter(api_key="test", secret_key="test")
        adapter._connected = True
        adapter._client = MagicMock()
        adapter._alpaca_imported = True
        
        with pytest.raises(InvalidOrderError, match="Quantity must be positive"):
            await adapter.submit_order(
                symbol="AAPL",
                quantity=Decimal("-10"),
                side=OrderSide.BUY,
            )
    
    @pytest.mark.asyncio
    async def test_submit_order_limit_without_price(self):
        """Test submit_order fails for limit order without price."""
        from alphashield.trading.adapters.alpaca_adapter import AlpacaAdapter
        from alphashield.trading.adapters.base import InvalidOrderError
        
        adapter = AlpacaAdapter(api_key="test", secret_key="test")
        adapter._connected = True
        adapter._client = MagicMock()
        adapter._alpaca_imported = True
        
        with pytest.raises(InvalidOrderError, match="requires limit_price"):
            await adapter.submit_order(
                symbol="AAPL",
                quantity=Decimal("10"),
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
            )
    
    @pytest.mark.asyncio
    async def test_submit_order_stop_without_price(self):
        """Test submit_order fails for stop order without price."""
        from alphashield.trading.adapters.alpaca_adapter import AlpacaAdapter
        from alphashield.trading.adapters.base import InvalidOrderError
        
        adapter = AlpacaAdapter(api_key="test", secret_key="test")
        adapter._connected = True
        adapter._client = MagicMock()
        adapter._alpaca_imported = True
        
        with pytest.raises(InvalidOrderError, match="requires stop_price"):
            await adapter.submit_order(
                symbol="AAPL",
                quantity=Decimal("10"),
                side=OrderSide.BUY,
                order_type=OrderType.STOP,
            )


class TestAlpacaAdapterHelpers:
    """Test AlpacaAdapter helper methods."""
    
    def test_map_order_status(self):
        """Test order status mapping."""
        from alphashield.trading.adapters.alpaca_adapter import AlpacaAdapter
        
        adapter = AlpacaAdapter()
        
        assert adapter._map_order_status("filled") == OrderStatus.FILLED
        assert adapter._map_order_status("canceled") == OrderStatus.CANCELLED
        assert adapter._map_order_status("new") == OrderStatus.SUBMITTED
        assert adapter._map_order_status("partially_filled") == OrderStatus.PARTIAL
        assert adapter._map_order_status("unknown_status") == OrderStatus.PENDING
    
    def test_map_order_type(self):
        """Test order type mapping."""
        from alphashield.trading.adapters.alpaca_adapter import AlpacaAdapter
        
        adapter = AlpacaAdapter()
        
        assert adapter._map_order_type("market") == OrderType.MARKET
        assert adapter._map_order_type("limit") == OrderType.LIMIT
        assert adapter._map_order_type("stop") == OrderType.STOP
        assert adapter._map_order_type("stop_limit") == OrderType.STOP_LIMIT
        assert adapter._map_order_type("unknown") == OrderType.MARKET


class TestAlpacaAdapterExceptions:
    """Test AlpacaAdapter exception handling."""
    
    def test_broker_error_hierarchy(self):
        """Test exception class hierarchy."""
        from alphashield.trading.adapters.base import (
            BrokerError,
            ConnectionError,
            OrderError,
            InsufficientFundsError,
            InvalidOrderError,
            PositionError,
            MarketDataError,
        )
        
        assert issubclass(ConnectionError, BrokerError)
        assert issubclass(OrderError, BrokerError)
        assert issubclass(InsufficientFundsError, OrderError)
        assert issubclass(InvalidOrderError, OrderError)
        assert issubclass(PositionError, BrokerError)
        assert issubclass(MarketDataError, BrokerError)


# Integration test (requires actual Alpaca credentials)
@pytest.mark.skip(reason="Requires actual Alpaca API credentials")
class TestAlpacaAdapterIntegration:
    """Integration tests for AlpacaAdapter with real API."""
    
    @pytest.mark.asyncio
    async def test_connect_paper(self):
        """Test connecting to paper trading."""
        from alphashield.trading.adapters.alpaca_adapter import AlpacaAdapter
        import os
        
        adapter = AlpacaAdapter(
            api_key=os.environ.get("ALPACA_API_KEY"),
            secret_key=os.environ.get("ALPACA_SECRET_KEY"),
            paper=True,
        )
        
        connected = await adapter.connect()
        assert connected is True
        
        account = await adapter.get_account()
        assert account.account_id is not None
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_get_market_data(self):
        """Test fetching market data."""
        from alphashield.trading.adapters.alpaca_adapter import AlpacaAdapter
        from datetime import timedelta
        import os
        
        adapter = AlpacaAdapter(
            api_key=os.environ.get("ALPACA_API_KEY"),
            secret_key=os.environ.get("ALPACA_SECRET_KEY"),
            paper=True,
        )
        
        await adapter.connect()
        
        # Get recent bars
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=5)
        
        bars = await adapter.get_bars(
            symbol="SPY",
            timeframe="1Day",
            start=start,
            end=end,
        )
        
        assert len(bars) > 0
        assert bars[0].symbol == "SPY"
        
        await adapter.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
