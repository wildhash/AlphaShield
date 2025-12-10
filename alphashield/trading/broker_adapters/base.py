"""Base broker adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class OrderStatus(str, Enum):
    """Order status enumeration."""
    
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderType(str, Enum):
    """Order type enumeration."""
    
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, Enum):
    """Order side enumeration."""
    
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """Order representation."""
    
    id: str
    ticker: str
    quantity: float
    side: OrderSide
    type: OrderType
    status: OrderStatus
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    filled_quantity: float = 0.0
    filled_avg_price: Optional[float] = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class Position:
    """Position representation."""
    
    ticker: str
    quantity: float
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


@dataclass
class Account:
    """Account information."""
    
    id: str
    cash: float
    portfolio_value: float
    buying_power: float
    equity: float
    last_equity: float
    multiplier: float = 1.0
    currency: str = "USD"


class BrokerAdapter(ABC):
    """Abstract base class for broker API adapters."""
    
    @abstractmethod
    def get_account(self) -> Account:
        """Get account information.
        
        Returns:
            Account object with current account state.
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get all current positions.
        
        Returns:
            List of Position objects.
        """
        pass
    
    @abstractmethod
    def get_position(self, ticker: str) -> Optional[Position]:
        """Get position for specific ticker.
        
        Args:
            ticker: Stock ticker symbol.
            
        Returns:
            Position object if exists, None otherwise.
        """
        pass
    
    @abstractmethod
    def submit_order(
        self,
        ticker: str,
        qty: float,
        side: OrderSide,
        type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "day",
    ) -> Order:
        """Submit an order.
        
        Args:
            ticker: Stock ticker symbol.
            qty: Quantity to trade.
            side: Buy or sell.
            type: Order type (market, limit, etc).
            limit_price: Limit price for limit orders.
            stop_price: Stop price for stop orders.
            time_in_force: Time in force (day, gtc, ioc, fok).
            
        Returns:
            Order object with submission details.
        """
        pass
    
    @abstractmethod
    def get_order(self, order_id: str) -> Order:
        """Get order status.
        
        Args:
            order_id: Order ID to query.
            
        Returns:
            Order object with current status.
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.
        
        Args:
            order_id: Order ID to cancel.
            
        Returns:
            True if cancelled successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_orders(
        self, 
        status: Optional[OrderStatus] = None,
        limit: int = 100
    ) -> List[Order]:
        """Get orders, optionally filtered by status.
        
        Args:
            status: Filter by order status.
            limit: Maximum number of orders to return.
            
        Returns:
            List of Order objects.
        """
        pass
    
    @abstractmethod
    def get_quote(self, ticker: str) -> Dict[str, float]:
        """Get real-time quote for ticker.
        
        Args:
            ticker: Stock ticker symbol.
            
        Returns:
            Dictionary with quote data (bid, ask, last, volume, etc).
        """
        pass
    
    @abstractmethod
    def close_position(self, ticker: str) -> Order:
        """Close entire position for ticker.
        
        Args:
            ticker: Stock ticker symbol.
            
        Returns:
            Order object for closing trade.
        """
        pass
    
    @abstractmethod
    def close_all_positions(self) -> List[Order]:
        """Close all positions.
        
        Returns:
            List of Order objects for all closing trades.
        """
        pass
