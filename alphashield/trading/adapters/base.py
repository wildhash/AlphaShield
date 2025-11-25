"""
Base Broker Adapter Interface

Defines the abstract interface for all broker adapters to ensure
consistent behavior across different trading platforms.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional


class OrderStatus(Enum):
    """Order execution status."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSide(Enum):
    """Order direction."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order execution type."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class TimeInForce(Enum):
    """Order time-in-force."""
    DAY = "day"
    GTC = "gtc"  # Good 'til cancelled
    IOC = "ioc"  # Immediate or cancel
    FOK = "fok"  # Fill or kill
    OPG = "opg"  # Market on open
    CLS = "cls"  # Market on close


@dataclass
class Position:
    """Represents a portfolio position."""
    symbol: str
    quantity: Decimal
    avg_entry_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    current_price: Decimal
    cost_basis: Decimal
    side: str  # "long" or "short"
    asset_class: str = "equity"
    exchange: str = ""
    
    @property
    def is_profitable(self) -> bool:
        """Check if position is currently profitable."""
        return self.unrealized_pnl > 0


@dataclass
class Order:
    """Represents a trading order."""
    id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    filled_quantity: Decimal = Decimal("0")
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    time_in_force: TimeInForce = TimeInForce.DAY
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    filled_avg_price: Optional[Decimal] = None
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_active(self) -> bool:
        """Check if order is still active."""
        return self.status in (OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL)


@dataclass
class AccountInfo:
    """Account summary information."""
    account_id: str
    status: str
    currency: str = "USD"
    buying_power: Decimal = Decimal("0")
    cash: Decimal = Decimal("0")
    portfolio_value: Decimal = Decimal("0")
    equity: Decimal = Decimal("0")
    last_equity: Decimal = Decimal("0")
    long_market_value: Decimal = Decimal("0")
    short_market_value: Decimal = Decimal("0")
    initial_margin: Decimal = Decimal("0")
    maintenance_margin: Decimal = Decimal("0")
    daytrade_count: int = 0
    pattern_day_trader: bool = False
    trading_blocked: bool = False
    transfers_blocked: bool = False
    account_blocked: bool = False


@dataclass
class Bar:
    """Price bar (OHLCV) data."""
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    vwap: Optional[Decimal] = None
    trade_count: Optional[int] = None


@dataclass
class Quote:
    """Real-time quote data."""
    symbol: str
    timestamp: datetime
    bid: Decimal
    bid_size: int
    ask: Decimal
    ask_size: int
    
    @property
    def spread(self) -> Decimal:
        """Calculate bid-ask spread."""
        return self.ask - self.bid
    
    @property
    def mid_price(self) -> Decimal:
        """Calculate mid-point price."""
        return (self.bid + self.ask) / 2


class BrokerAdapter(ABC):
    """
    Abstract base class for broker adapters.
    
    All broker implementations must inherit from this class and
    implement all abstract methods to ensure consistent behavior.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the broker.
        
        Returns:
            True if connection successful, False otherwise.
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the broker."""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if currently connected to the broker."""
        pass
    
    # Account Methods
    @abstractmethod
    async def get_account(self) -> AccountInfo:
        """Get account information and balances."""
        pass
    
    @abstractmethod
    async def get_buying_power(self) -> Decimal:
        """Get current buying power."""
        pass
    
    # Position Methods
    @abstractmethod
    async def get_positions(self) -> list[Position]:
        """Get all current positions."""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol."""
        pass
    
    @abstractmethod
    async def close_position(self, symbol: str) -> Order:
        """Close entire position for a symbol."""
        pass
    
    @abstractmethod
    async def close_all_positions(self) -> list[Order]:
        """Close all positions."""
        pass
    
    # Order Methods
    @abstractmethod
    async def submit_order(
        self,
        symbol: str,
        quantity: Decimal,
        side: OrderSide,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        client_order_id: Optional[str] = None,
    ) -> Order:
        """
        Submit a new order.
        
        Args:
            symbol: Trading symbol
            quantity: Number of shares/units
            side: Buy or sell
            order_type: Market, limit, stop, etc.
            limit_price: Limit price (required for limit orders)
            stop_price: Stop price (required for stop orders)
            time_in_force: Order duration
            client_order_id: Optional custom order ID
            
        Returns:
            Order object with submitted order details.
        """
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        pass
    
    @abstractmethod
    async def get_orders(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        after: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> list[Order]:
        """Get list of orders with optional filters."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Returns:
            True if cancellation request accepted.
        """
        pass
    
    @abstractmethod
    async def cancel_all_orders(self) -> int:
        """
        Cancel all open orders.
        
        Returns:
            Number of orders cancelled.
        """
        pass
    
    # Market Data Methods
    @abstractmethod
    async def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[Bar]:
        """
        Get historical price bars.
        
        Args:
            symbol: Trading symbol
            timeframe: Bar timeframe (e.g., "1Min", "1Hour", "1Day")
            start: Start datetime
            end: End datetime (defaults to now)
            limit: Maximum number of bars
            
        Returns:
            List of Bar objects.
        """
        pass
    
    @abstractmethod
    async def get_latest_bar(self, symbol: str) -> Optional[Bar]:
        """Get the latest price bar for a symbol."""
        pass
    
    @abstractmethod
    async def get_latest_quote(self, symbol: str) -> Optional[Quote]:
        """Get the latest quote for a symbol."""
        pass
    
    @abstractmethod
    async def get_latest_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        """Get latest quotes for multiple symbols."""
        pass
    
    # Utility Methods
    @abstractmethod
    async def is_market_open(self) -> bool:
        """Check if the market is currently open."""
        pass
    
    @abstractmethod
    async def get_clock(self) -> dict[str, Any]:
        """Get market clock information."""
        pass


class BrokerError(Exception):
    """Base exception for broker errors."""
    pass


class ConnectionError(BrokerError):
    """Error connecting to broker."""
    pass


class OrderError(BrokerError):
    """Error submitting or managing orders."""
    pass


class InsufficientFundsError(OrderError):
    """Insufficient funds to execute order."""
    pass


class InvalidOrderError(OrderError):
    """Invalid order parameters."""
    pass


class PositionError(BrokerError):
    """Error managing positions."""
    pass


class MarketDataError(BrokerError):
    """Error fetching market data."""
    pass
