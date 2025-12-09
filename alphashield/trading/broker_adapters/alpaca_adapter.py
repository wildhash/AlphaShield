"""Alpaca API adapter for live trading."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from .base import (
    Account,
    BrokerAdapter,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)

logger = logging.getLogger(__name__)


class AlpacaAdapter(BrokerAdapter):
    """Alpaca Markets API adapter.
    
    Supports both paper trading and live trading environments.
    
    Environment Variables:
        ALPACA_API_KEY: Alpaca API key
        ALPACA_SECRET_KEY: Alpaca secret key
        ALPACA_BASE_URL: Base URL (paper or live)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        paper: bool = True,
    ):
        """Initialize Alpaca adapter.
        
        Args:
            api_key: Alpaca API key (or from ALPACA_API_KEY env var).
            secret_key: Alpaca secret key (or from ALPACA_SECRET_KEY env var).
            base_url: Base URL override (or from ALPACA_BASE_URL env var).
            paper: Use paper trading environment (default True).
        """
        # Import alpaca-py library
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.trading.requests import (
                LimitOrderRequest,
                MarketOrderRequest,
                StopLimitOrderRequest,
                StopOrderRequest,
            )
            from alpaca.trading.enums import (
                OrderSide as AlpacaOrderSide,
                TimeInForce,
                OrderStatus as AlpacaOrderStatus,
            )
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockLatestQuoteRequest
            
            self._trading_client_class = TradingClient
            self._market_order_class = MarketOrderRequest
            self._limit_order_class = LimitOrderRequest
            self._stop_order_class = StopOrderRequest
            self._stop_limit_order_class = StopLimitOrderRequest
            self._alpaca_order_side = AlpacaOrderSide
            self._alpaca_time_in_force = TimeInForce
            self._alpaca_order_status = AlpacaOrderStatus
            self._stock_client_class = StockHistoricalDataClient
            self._quote_request_class = StockLatestQuoteRequest
            
        except ImportError as e:
            raise ImportError(
                "alpaca-py is required for AlpacaAdapter. "
                "Install with: pip install alpaca-py"
            ) from e
        
        # Get credentials
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")
        
        if not self.api_key or not self.secret_key:
            raise ValueError(
                "Alpaca API credentials required. "
                "Set ALPACA_API_KEY and ALPACA_SECRET_KEY env vars."
            )
        
        # Determine base URL
        if base_url:
            self.base_url = base_url
        elif os.getenv("ALPACA_BASE_URL"):
            self.base_url = os.getenv("ALPACA_BASE_URL")
        else:
            # Default based on paper flag
            self.base_url = (
                "https://paper-api.alpaca.markets"
                if paper
                else "https://api.alpaca.markets"
            )
        
        self.paper = paper
        
        # Initialize clients
        self.trading_client = self._trading_client_class(
            api_key=self.api_key,
            secret_key=self.secret_key,
            paper=paper,
        )
        
        self.data_client = self._stock_client_class(
            api_key=self.api_key,
            secret_key=self.secret_key,
        )
        
        logger.info(
            f"Initialized Alpaca adapter (paper={paper}, base_url={self.base_url})"
        )
    
    def get_account(self) -> Account:
        """Get account information."""
        try:
            acc = self.trading_client.get_account()
            
            return Account(
                id=acc.id,
                cash=float(acc.cash),
                portfolio_value=float(acc.portfolio_value),
                buying_power=float(acc.buying_power),
                equity=float(acc.equity),
                last_equity=float(acc.last_equity),
                multiplier=float(acc.multiplier),
                currency=acc.currency,
            )
        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            raise
    
    def get_positions(self) -> List[Position]:
        """Get all current positions."""
        try:
            positions = self.trading_client.get_all_positions()
            
            return [
                Position(
                    ticker=pos.symbol,
                    quantity=float(pos.qty),
                    avg_entry_price=float(pos.avg_entry_price),
                    current_price=float(pos.current_price),
                    market_value=float(pos.market_value),
                    unrealized_pnl=float(pos.unrealized_pl),
                    unrealized_pnl_pct=float(pos.unrealized_plpc),
                )
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise
    
    def get_position(self, ticker: str) -> Optional[Position]:
        """Get position for specific ticker."""
        try:
            pos = self.trading_client.get_open_position(ticker)
            
            return Position(
                ticker=pos.symbol,
                quantity=float(pos.qty),
                avg_entry_price=float(pos.avg_entry_price),
                current_price=float(pos.current_price),
                market_value=float(pos.market_value),
                unrealized_pnl=float(pos.unrealized_pl),
                unrealized_pnl_pct=float(pos.unrealized_plpc),
            )
        except Exception as e:
            if "position does not exist" in str(e).lower():
                return None
            logger.error(f"Failed to get position for {ticker}: {e}")
            raise
    
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
        """Submit an order."""
        try:
            # Convert our types to Alpaca types
            alpaca_side = (
                self._alpaca_order_side.BUY
                if side == OrderSide.BUY
                else self._alpaca_order_side.SELL
            )
            
            # Map time_in_force
            tif_map = {
                "day": self._alpaca_time_in_force.DAY,
                "gtc": self._alpaca_time_in_force.GTC,
                "ioc": self._alpaca_time_in_force.IOC,
                "fok": self._alpaca_time_in_force.FOK,
            }
            alpaca_tif = tif_map.get(time_in_force.lower(), self._alpaca_time_in_force.DAY)
            
            # Create order request based on type
            if type == OrderType.MARKET:
                order_request = self._market_order_class(
                    symbol=ticker,
                    qty=qty,
                    side=alpaca_side,
                    time_in_force=alpaca_tif,
                )
            elif type == OrderType.LIMIT:
                if limit_price is None:
                    raise ValueError("limit_price required for limit orders")
                order_request = self._limit_order_class(
                    symbol=ticker,
                    qty=qty,
                    side=alpaca_side,
                    time_in_force=alpaca_tif,
                    limit_price=limit_price,
                )
            elif type == OrderType.STOP:
                if stop_price is None:
                    raise ValueError("stop_price required for stop orders")
                order_request = self._stop_order_class(
                    symbol=ticker,
                    qty=qty,
                    side=alpaca_side,
                    time_in_force=alpaca_tif,
                    stop_price=stop_price,
                )
            elif type == OrderType.STOP_LIMIT:
                if limit_price is None or stop_price is None:
                    raise ValueError("limit_price and stop_price required for stop-limit orders")
                order_request = self._stop_limit_order_class(
                    symbol=ticker,
                    qty=qty,
                    side=alpaca_side,
                    time_in_force=alpaca_tif,
                    limit_price=limit_price,
                    stop_price=stop_price,
                )
            else:
                raise ValueError(f"Unsupported order type: {type}")
            
            # Submit order
            alpaca_order = self.trading_client.submit_order(order_request)
            
            return self._convert_order(alpaca_order)
            
        except Exception as e:
            logger.error(f"Failed to submit order for {ticker}: {e}")
            # Return rejected order
            return Order(
                id="",
                ticker=ticker,
                quantity=qty,
                side=side,
                type=type,
                status=OrderStatus.REJECTED,
                limit_price=limit_price,
                stop_price=stop_price,
                error_message=str(e),
            )
    
    def get_order(self, order_id: str) -> Order:
        """Get order status."""
        try:
            alpaca_order = self.trading_client.get_order_by_id(order_id)
            return self._convert_order(alpaca_order)
        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Cancelled order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def get_orders(
        self, 
        status: Optional[OrderStatus] = None,
        limit: int = 100
    ) -> List[Order]:
        """Get orders, optionally filtered by status."""
        try:
            from alpaca.trading.requests import GetOrdersRequest
            
            # Map our status to Alpaca status
            alpaca_status = None
            if status:
                status_map = {
                    OrderStatus.PENDING: self._alpaca_order_status.PENDING_NEW,
                    OrderStatus.SUBMITTED: self._alpaca_order_status.ACCEPTED,
                    OrderStatus.ACCEPTED: self._alpaca_order_status.ACCEPTED,
                    OrderStatus.FILLED: self._alpaca_order_status.FILLED,
                    OrderStatus.PARTIALLY_FILLED: self._alpaca_order_status.PARTIALLY_FILLED,
                    OrderStatus.CANCELLED: self._alpaca_order_status.CANCELED,
                    OrderStatus.REJECTED: self._alpaca_order_status.REJECTED,
                    OrderStatus.EXPIRED: self._alpaca_order_status.EXPIRED,
                }
                alpaca_status = status_map.get(status)
            
            request = GetOrdersRequest(
                status=alpaca_status,
                limit=limit,
            )
            
            alpaca_orders = self.trading_client.get_orders(request)
            
            return [self._convert_order(order) for order in alpaca_orders]
            
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise
    
    def get_quote(self, ticker: str) -> Dict[str, float]:
        """Get real-time quote for ticker."""
        try:
            request = self._quote_request_class(symbol_or_symbols=ticker)
            quotes = self.data_client.get_stock_latest_quote(request)
            quote = quotes[ticker]
            
            return {
                "bid": float(quote.bid_price),
                "ask": float(quote.ask_price),
                "bid_size": float(quote.bid_size),
                "ask_size": float(quote.ask_size),
                "last": float((quote.bid_price + quote.ask_price) / 2),  # Midpoint
            }
        except Exception as e:
            logger.error(f"Failed to get quote for {ticker}: {e}")
            raise
    
    def close_position(self, ticker: str) -> Order:
        """Close entire position for ticker."""
        try:
            # Get current position
            position = self.get_position(ticker)
            if not position:
                raise ValueError(f"No position exists for {ticker}")
            
            # Submit market order to close
            side = OrderSide.SELL if position.quantity > 0 else OrderSide.BUY
            
            return self.submit_order(
                ticker=ticker,
                qty=abs(position.quantity),
                side=side,
                type=OrderType.MARKET,
            )
        except Exception as e:
            logger.error(f"Failed to close position for {ticker}: {e}")
            raise
    
    def close_all_positions(self) -> List[Order]:
        """Close all positions."""
        try:
            positions = self.get_positions()
            orders = []
            
            for position in positions:
                try:
                    order = self.close_position(position.ticker)
                    orders.append(order)
                except Exception as e:
                    logger.error(f"Failed to close position {position.ticker}: {e}")
            
            return orders
        except Exception as e:
            logger.error(f"Failed to close all positions: {e}")
            raise
    
    def _convert_order(self, alpaca_order) -> Order:
        """Convert Alpaca order to our Order type."""
        # Map Alpaca status to our status
        status_map = {
            self._alpaca_order_status.NEW: OrderStatus.SUBMITTED,
            self._alpaca_order_status.PENDING_NEW: OrderStatus.PENDING,
            self._alpaca_order_status.ACCEPTED: OrderStatus.ACCEPTED,
            self._alpaca_order_status.FILLED: OrderStatus.FILLED,
            self._alpaca_order_status.PARTIALLY_FILLED: OrderStatus.PARTIALLY_FILLED,
            self._alpaca_order_status.CANCELED: OrderStatus.CANCELLED,
            self._alpaca_order_status.REJECTED: OrderStatus.REJECTED,
            self._alpaca_order_status.EXPIRED: OrderStatus.EXPIRED,
        }
        
        status = status_map.get(alpaca_order.status, OrderStatus.PENDING)
        
        # Map side
        side = (
            OrderSide.BUY
            if alpaca_order.side == self._alpaca_order_side.BUY
            else OrderSide.SELL
        )
        
        # Map order type
        type_str = str(alpaca_order.order_type).lower()
        if "market" in type_str:
            order_type = OrderType.MARKET
        elif "limit" in type_str and "stop" in type_str:
            order_type = OrderType.STOP_LIMIT
        elif "stop" in type_str:
            order_type = OrderType.STOP
        else:
            order_type = OrderType.LIMIT
        
        return Order(
            id=alpaca_order.id,
            ticker=alpaca_order.symbol,
            quantity=float(alpaca_order.qty),
            side=side,
            type=order_type,
            status=status,
            limit_price=float(alpaca_order.limit_price) if alpaca_order.limit_price else None,
            stop_price=float(alpaca_order.stop_price) if alpaca_order.stop_price else None,
            filled_quantity=float(alpaca_order.filled_qty) if alpaca_order.filled_qty else 0.0,
            filled_avg_price=float(alpaca_order.filled_avg_price) if alpaca_order.filled_avg_price else None,
            submitted_at=alpaca_order.submitted_at,
            filled_at=alpaca_order.filled_at,
        )
