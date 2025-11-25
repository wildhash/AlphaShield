"""
Alpaca Broker Adapter

Production-ready adapter for Alpaca Markets API integration.
Supports both paper and live trading with full feature set.

Features:
- Async/await throughout for non-blocking I/O
- Comprehensive error handling and retry logic
- Rate limiting compliance
- Position and order management
- Real-time and historical market data
- Account monitoring

Usage:
    from alphashield.trading.adapters import AlpacaAdapter
    
    adapter = AlpacaAdapter(
        api_key="your-key",
        secret_key="your-secret",
        paper=True  # Use paper trading
    )
    
    await adapter.connect()
    positions = await adapter.get_positions()
    order = await adapter.submit_order(
        symbol="SPY",
        quantity=Decimal("10"),
        side=OrderSide.BUY
    )
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from .base import (
    AccountInfo,
    Bar,
    BrokerAdapter,
    BrokerError,
    ConnectionError,
    InsufficientFundsError,
    InvalidOrderError,
    MarketDataError,
    Order,
    OrderError,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    PositionError,
    Quote,
    TimeInForce,
)


logger = logging.getLogger(__name__)


class AlpacaAdapter(BrokerAdapter):
    """
    Alpaca Markets broker adapter.
    
    Implements the BrokerAdapter interface for Alpaca's trading API.
    Supports both paper and live trading environments.
    
    Attributes:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        base_url: API base URL (paper or live)
        data_url: Market data API URL
    """
    
    PAPER_URL = "https://paper-api.alpaca.markets"
    LIVE_URL = "https://api.alpaca.markets"
    DATA_URL = "https://data.alpaca.markets"
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE = 200
    REQUEST_INTERVAL = 60 / MAX_REQUESTS_PER_MINUTE
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize Alpaca adapter.
        
        Args:
            api_key: Alpaca API key (defaults to ALPACA_API_KEY env var)
            secret_key: Alpaca secret key (defaults to ALPACA_SECRET_KEY env var)
            paper: Use paper trading if True, live trading if False
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.api_key = api_key or os.environ.get("ALPACA_API_KEY", "")
        self.secret_key = secret_key or os.environ.get("ALPACA_SECRET_KEY", "")
        self.paper = paper
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.base_url = self.PAPER_URL if paper else self.LIVE_URL
        self.data_url = self.DATA_URL
        
        self._client: Optional[Any] = None
        self._data_client: Optional[Any] = None
        self._connected = False
        self._last_request_time = 0.0
        
        # Import alpaca-py lazily to avoid import errors if not installed
        self._alpaca_imported = False
        
    async def _ensure_alpaca_imported(self) -> None:
        """Lazily import alpaca-py modules."""
        if self._alpaca_imported:
            return
            
        try:
            # Import Alpaca SDK
            from alpaca.trading.client import TradingClient
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.live import StockDataStream
            from alpaca.trading.requests import (
                GetOrdersRequest,
                LimitOrderRequest,
                MarketOrderRequest,
                StopLimitOrderRequest,
                StopOrderRequest,
                TrailingStopOrderRequest,
            )
            from alpaca.trading.enums import (
                OrderSide as AlpacaOrderSide,
                OrderType as AlpacaOrderType,
                TimeInForce as AlpacaTimeInForce,
                QueryOrderStatus,
            )
            from alpaca.data.requests import (
                StockBarsRequest,
                StockLatestBarRequest,
                StockLatestQuoteRequest,
            )
            from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
            
            self._TradingClient = TradingClient
            self._StockHistoricalDataClient = StockHistoricalDataClient
            self._StockDataStream = StockDataStream
            self._GetOrdersRequest = GetOrdersRequest
            self._LimitOrderRequest = LimitOrderRequest
            self._MarketOrderRequest = MarketOrderRequest
            self._StopLimitOrderRequest = StopLimitOrderRequest
            self._StopOrderRequest = StopOrderRequest
            self._TrailingStopOrderRequest = TrailingStopOrderRequest
            self._AlpacaOrderSide = AlpacaOrderSide
            self._AlpacaOrderType = AlpacaOrderType
            self._AlpacaTimeInForce = AlpacaTimeInForce
            self._QueryOrderStatus = QueryOrderStatus
            self._StockBarsRequest = StockBarsRequest
            self._StockLatestBarRequest = StockLatestBarRequest
            self._StockLatestQuoteRequest = StockLatestQuoteRequest
            self._TimeFrame = TimeFrame
            self._TimeFrameUnit = TimeFrameUnit
            
            self._alpaca_imported = True
            logger.info("Alpaca SDK imported successfully")
            
        except ImportError as e:
            raise ImportError(
                "alpaca-py package not installed. "
                "Install with: pip install alpaca-py"
            ) from e
    
    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.REQUEST_INTERVAL:
            await asyncio.sleep(self.REQUEST_INTERVAL - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def _execute_with_retry(self, func, *args, **kwargs) -> Any:
        """Execute a function with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                await self._rate_limit()
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        raise last_error
    
    # Connection Methods
    async def connect(self) -> bool:
        """
        Establish connection to Alpaca.
        
        Returns:
            True if connection successful.
            
        Raises:
            ConnectionError: If connection fails.
        """
        try:
            await self._ensure_alpaca_imported()
            
            if not self.api_key or not self.secret_key:
                raise ConnectionError("Alpaca API key and secret key are required")
            
            # Initialize trading client
            self._client = self._TradingClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                paper=self.paper,
            )
            
            # Initialize data client
            self._data_client = self._StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
            )
            
            # Verify connection by fetching account
            account = self._client.get_account()
            self._connected = True
            
            env = "paper" if self.paper else "live"
            logger.info(f"Connected to Alpaca ({env}), account: {account.id}")
            return True
            
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to Alpaca: {e}") from e
    
    async def disconnect(self) -> None:
        """Disconnect from Alpaca."""
        self._client = None
        self._data_client = None
        self._connected = False
        logger.info("Disconnected from Alpaca")
    
    async def is_connected(self) -> bool:
        """Check if connected to Alpaca."""
        if not self._connected or not self._client:
            return False
        try:
            self._client.get_account()
            return True
        except Exception:
            self._connected = False
            return False
    
    # Account Methods
    async def get_account(self) -> AccountInfo:
        """Get account information."""
        if not self._client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            account = await self._execute_with_retry(self._client.get_account)
            return AccountInfo(
                account_id=str(account.id),
                status=account.status.value if hasattr(account.status, 'value') else str(account.status),
                currency=account.currency or "USD",
                buying_power=Decimal(str(account.buying_power)),
                cash=Decimal(str(account.cash)),
                portfolio_value=Decimal(str(account.portfolio_value)),
                equity=Decimal(str(account.equity)),
                last_equity=Decimal(str(account.last_equity)),
                long_market_value=Decimal(str(account.long_market_value)),
                short_market_value=Decimal(str(account.short_market_value)),
                initial_margin=Decimal(str(account.initial_margin)),
                maintenance_margin=Decimal(str(account.maintenance_margin)),
                daytrade_count=account.daytrade_count or 0,
                pattern_day_trader=account.pattern_day_trader or False,
                trading_blocked=account.trading_blocked or False,
                transfers_blocked=account.transfers_blocked or False,
                account_blocked=account.account_blocked or False,
            )
        except Exception as e:
            raise BrokerError(f"Failed to get account: {e}") from e
    
    async def get_buying_power(self) -> Decimal:
        """Get current buying power."""
        account = await self.get_account()
        return account.buying_power
    
    # Position Methods
    async def get_positions(self) -> list[Position]:
        """Get all current positions."""
        if not self._client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            positions = await self._execute_with_retry(self._client.get_all_positions)
            return [self._convert_position(p) for p in positions]
        except Exception as e:
            raise PositionError(f"Failed to get positions: {e}") from e
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol."""
        if not self._client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            position = await self._execute_with_retry(
                self._client.get_open_position,
                symbol.upper()
            )
            return self._convert_position(position)
        except Exception as e:
            if "position does not exist" in str(e).lower():
                return None
            raise PositionError(f"Failed to get position for {symbol}: {e}") from e
    
    async def close_position(self, symbol: str) -> Order:
        """Close entire position for a symbol."""
        if not self._client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            order = await self._execute_with_retry(
                self._client.close_position,
                symbol.upper()
            )
            return self._convert_order(order)
        except Exception as e:
            raise PositionError(f"Failed to close position for {symbol}: {e}") from e
    
    async def close_all_positions(self) -> list[Order]:
        """Close all positions."""
        if not self._client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            orders = await self._execute_with_retry(self._client.close_all_positions)
            return [self._convert_order(o) for o in orders]
        except Exception as e:
            raise PositionError(f"Failed to close all positions: {e}") from e
    
    # Order Methods
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
            quantity: Number of shares
            side: Buy or sell
            order_type: Market, limit, stop, etc.
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders
            time_in_force: Order duration
            client_order_id: Optional custom order ID
            
        Returns:
            Order object with submitted order details.
        """
        if not self._client:
            raise ConnectionError("Not connected to Alpaca")
        
        # Validate inputs
        if quantity <= 0:
            raise InvalidOrderError("Quantity must be positive")
        
        if order_type in (OrderType.LIMIT, OrderType.STOP_LIMIT) and limit_price is None:
            raise InvalidOrderError(f"{order_type.value} order requires limit_price")
        
        if order_type in (OrderType.STOP, OrderType.STOP_LIMIT) and stop_price is None:
            raise InvalidOrderError(f"{order_type.value} order requires stop_price")
        
        try:
            # Map to Alpaca types
            alpaca_side = (
                self._AlpacaOrderSide.BUY 
                if side == OrderSide.BUY 
                else self._AlpacaOrderSide.SELL
            )
            alpaca_tif = self._map_time_in_force(time_in_force)
            
            # Generate client order ID if not provided
            if not client_order_id:
                client_order_id = f"alphashield-{uuid.uuid4().hex[:8]}"
            
            # Create appropriate order request
            if order_type == OrderType.MARKET:
                request = self._MarketOrderRequest(
                    symbol=symbol.upper(),
                    qty=float(quantity),
                    side=alpaca_side,
                    time_in_force=alpaca_tif,
                    client_order_id=client_order_id,
                )
            elif order_type == OrderType.LIMIT:
                request = self._LimitOrderRequest(
                    symbol=symbol.upper(),
                    qty=float(quantity),
                    side=alpaca_side,
                    time_in_force=alpaca_tif,
                    limit_price=float(limit_price),
                    client_order_id=client_order_id,
                )
            elif order_type == OrderType.STOP:
                request = self._StopOrderRequest(
                    symbol=symbol.upper(),
                    qty=float(quantity),
                    side=alpaca_side,
                    time_in_force=alpaca_tif,
                    stop_price=float(stop_price),
                    client_order_id=client_order_id,
                )
            elif order_type == OrderType.STOP_LIMIT:
                request = self._StopLimitOrderRequest(
                    symbol=symbol.upper(),
                    qty=float(quantity),
                    side=alpaca_side,
                    time_in_force=alpaca_tif,
                    limit_price=float(limit_price),
                    stop_price=float(stop_price),
                    client_order_id=client_order_id,
                )
            elif order_type == OrderType.TRAILING_STOP:
                request = self._TrailingStopOrderRequest(
                    symbol=symbol.upper(),
                    qty=float(quantity),
                    side=alpaca_side,
                    time_in_force=alpaca_tif,
                    trail_percent=float(stop_price) if stop_price else 1.0,
                    client_order_id=client_order_id,
                )
            else:
                raise InvalidOrderError(f"Unsupported order type: {order_type}")
            
            order = await self._execute_with_retry(self._client.submit_order, request)
            logger.info(f"Order submitted: {order.id} - {side.value} {quantity} {symbol}")
            return self._convert_order(order)
            
        except Exception as e:
            error_str = str(e).lower()
            if "insufficient" in error_str:
                raise InsufficientFundsError(f"Insufficient funds for order: {e}") from e
            raise OrderError(f"Failed to submit order: {e}") from e
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        if not self._client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            order = await self._execute_with_retry(
                self._client.get_order_by_id,
                order_id
            )
            return self._convert_order(order)
        except Exception as e:
            if "order not found" in str(e).lower():
                return None
            raise OrderError(f"Failed to get order {order_id}: {e}") from e
    
    async def get_orders(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        after: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> list[Order]:
        """Get list of orders with optional filters."""
        if not self._client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            request_params = {
                "limit": limit,
            }
            
            if status:
                request_params["status"] = self._QueryOrderStatus(status)
            if after:
                request_params["after"] = after
            if until:
                request_params["until"] = until
                
            request = self._GetOrdersRequest(**request_params)
            orders = await self._execute_with_retry(
                self._client.get_orders,
                request
            )
            return [self._convert_order(o) for o in orders]
        except Exception as e:
            raise OrderError(f"Failed to get orders: {e}") from e
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if not self._client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            await self._execute_with_retry(self._client.cancel_order_by_id, order_id)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to cancel order {order_id}: {e}")
            return False
    
    async def cancel_all_orders(self) -> int:
        """Cancel all open orders."""
        if not self._client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            result = await self._execute_with_retry(self._client.cancel_orders)
            cancelled = len(result) if result else 0
            logger.info(f"Cancelled {cancelled} orders")
            return cancelled
        except Exception as e:
            raise OrderError(f"Failed to cancel all orders: {e}") from e
    
    # Market Data Methods
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
        """
        if not self._data_client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            tf = self._parse_timeframe(timeframe)
            end = end or datetime.now(timezone.utc)
            
            request = self._StockBarsRequest(
                symbol_or_symbols=symbol.upper(),
                timeframe=tf,
                start=start,
                end=end,
                limit=limit,
            )
            
            bars_data = await self._execute_with_retry(
                self._data_client.get_stock_bars,
                request
            )
            
            bars = []
            if symbol.upper() in bars_data:
                for bar in bars_data[symbol.upper()]:
                    bars.append(Bar(
                        symbol=symbol.upper(),
                        timestamp=bar.timestamp,
                        open=Decimal(str(bar.open)),
                        high=Decimal(str(bar.high)),
                        low=Decimal(str(bar.low)),
                        close=Decimal(str(bar.close)),
                        volume=bar.volume,
                        vwap=Decimal(str(bar.vwap)) if bar.vwap else None,
                        trade_count=bar.trade_count,
                    ))
            
            return bars
            
        except Exception as e:
            raise MarketDataError(f"Failed to get bars for {symbol}: {e}") from e
    
    async def get_latest_bar(self, symbol: str) -> Optional[Bar]:
        """Get the latest price bar for a symbol."""
        if not self._data_client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            request = self._StockLatestBarRequest(
                symbol_or_symbols=symbol.upper()
            )
            
            bars_data = await self._execute_with_retry(
                self._data_client.get_stock_latest_bar,
                request
            )
            
            if symbol.upper() in bars_data:
                bar = bars_data[symbol.upper()]
                return Bar(
                    symbol=symbol.upper(),
                    timestamp=bar.timestamp,
                    open=Decimal(str(bar.open)),
                    high=Decimal(str(bar.high)),
                    low=Decimal(str(bar.low)),
                    close=Decimal(str(bar.close)),
                    volume=bar.volume,
                    vwap=Decimal(str(bar.vwap)) if bar.vwap else None,
                    trade_count=bar.trade_count,
                )
            return None
            
        except Exception as e:
            raise MarketDataError(f"Failed to get latest bar for {symbol}: {e}") from e
    
    async def get_latest_quote(self, symbol: str) -> Optional[Quote]:
        """Get the latest quote for a symbol."""
        if not self._data_client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            request = self._StockLatestQuoteRequest(
                symbol_or_symbols=symbol.upper()
            )
            
            quotes_data = await self._execute_with_retry(
                self._data_client.get_stock_latest_quote,
                request
            )
            
            if symbol.upper() in quotes_data:
                quote = quotes_data[symbol.upper()]
                return Quote(
                    symbol=symbol.upper(),
                    timestamp=quote.timestamp,
                    bid=Decimal(str(quote.bid_price)),
                    bid_size=quote.bid_size,
                    ask=Decimal(str(quote.ask_price)),
                    ask_size=quote.ask_size,
                )
            return None
            
        except Exception as e:
            raise MarketDataError(f"Failed to get latest quote for {symbol}: {e}") from e
    
    async def get_latest_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        """Get latest quotes for multiple symbols."""
        if not self._data_client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            symbols_upper = [s.upper() for s in symbols]
            request = self._StockLatestQuoteRequest(
                symbol_or_symbols=symbols_upper
            )
            
            quotes_data = await self._execute_with_retry(
                self._data_client.get_stock_latest_quote,
                request
            )
            
            result = {}
            for symbol, quote in quotes_data.items():
                result[symbol] = Quote(
                    symbol=symbol,
                    timestamp=quote.timestamp,
                    bid=Decimal(str(quote.bid_price)),
                    bid_size=quote.bid_size,
                    ask=Decimal(str(quote.ask_price)),
                    ask_size=quote.ask_size,
                )
            
            return result
            
        except Exception as e:
            raise MarketDataError(f"Failed to get quotes: {e}") from e
    
    # Utility Methods
    async def is_market_open(self) -> bool:
        """Check if the market is currently open."""
        if not self._client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            clock = await self._execute_with_retry(self._client.get_clock)
            return clock.is_open
        except Exception as e:
            raise BrokerError(f"Failed to check market status: {e}") from e
    
    async def get_clock(self) -> dict[str, Any]:
        """Get market clock information."""
        if not self._client:
            raise ConnectionError("Not connected to Alpaca")
            
        try:
            clock = await self._execute_with_retry(self._client.get_clock)
            return {
                "is_open": clock.is_open,
                "timestamp": clock.timestamp.isoformat() if clock.timestamp else None,
                "next_open": clock.next_open.isoformat() if clock.next_open else None,
                "next_close": clock.next_close.isoformat() if clock.next_close else None,
            }
        except Exception as e:
            raise BrokerError(f"Failed to get clock: {e}") from e
    
    # Helper Methods
    def _convert_position(self, pos) -> Position:
        """Convert Alpaca position to our Position type."""
        return Position(
            symbol=pos.symbol,
            quantity=Decimal(str(pos.qty)),
            avg_entry_price=Decimal(str(pos.avg_entry_price)),
            market_value=Decimal(str(pos.market_value)),
            unrealized_pnl=Decimal(str(pos.unrealized_pl)),
            unrealized_pnl_pct=Decimal(str(pos.unrealized_plpc)) * 100,
            current_price=Decimal(str(pos.current_price)),
            cost_basis=Decimal(str(pos.cost_basis)),
            side=pos.side.value if hasattr(pos.side, 'value') else str(pos.side),
            asset_class=pos.asset_class.value if hasattr(pos.asset_class, 'value') else str(pos.asset_class),
            exchange=pos.exchange or "",
        )
    
    def _convert_order(self, order) -> Order:
        """Convert Alpaca order to our Order type."""
        return Order(
            id=str(order.id),
            client_order_id=order.client_order_id or "",
            symbol=order.symbol,
            side=OrderSide.BUY if str(order.side).lower() == "buy" else OrderSide.SELL,
            order_type=self._map_order_type(order.type),
            quantity=Decimal(str(order.qty)) if order.qty else Decimal("0"),
            filled_quantity=Decimal(str(order.filled_qty)) if order.filled_qty else Decimal("0"),
            limit_price=Decimal(str(order.limit_price)) if order.limit_price else None,
            stop_price=Decimal(str(order.stop_price)) if order.stop_price else None,
            status=self._map_order_status(order.status),
            time_in_force=self._map_tif_from_alpaca(order.time_in_force),
            submitted_at=order.submitted_at,
            filled_at=order.filled_at,
            filled_avg_price=Decimal(str(order.filled_avg_price)) if order.filled_avg_price else None,
        )
    
    def _map_order_status(self, status) -> OrderStatus:
        """Map Alpaca order status to our OrderStatus."""
        status_str = str(status).lower()
        mapping = {
            "pending_new": OrderStatus.PENDING,
            "new": OrderStatus.SUBMITTED,
            "accepted": OrderStatus.SUBMITTED,
            "partially_filled": OrderStatus.PARTIAL,
            "filled": OrderStatus.FILLED,
            "done_for_day": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "cancelled": OrderStatus.CANCELLED,
            "expired": OrderStatus.EXPIRED,
            "rejected": OrderStatus.REJECTED,
            "pending_cancel": OrderStatus.PENDING,
            "pending_replace": OrderStatus.PENDING,
        }
        return mapping.get(status_str, OrderStatus.PENDING)
    
    def _map_order_type(self, order_type) -> OrderType:
        """Map Alpaca order type to our OrderType."""
        type_str = str(order_type).lower()
        mapping = {
            "market": OrderType.MARKET,
            "limit": OrderType.LIMIT,
            "stop": OrderType.STOP,
            "stop_limit": OrderType.STOP_LIMIT,
            "trailing_stop": OrderType.TRAILING_STOP,
        }
        return mapping.get(type_str, OrderType.MARKET)
    
    def _map_time_in_force(self, tif: TimeInForce):
        """Map our TimeInForce to Alpaca's."""
        mapping = {
            TimeInForce.DAY: self._AlpacaTimeInForce.DAY,
            TimeInForce.GTC: self._AlpacaTimeInForce.GTC,
            TimeInForce.IOC: self._AlpacaTimeInForce.IOC,
            TimeInForce.FOK: self._AlpacaTimeInForce.FOK,
            TimeInForce.OPG: self._AlpacaTimeInForce.OPG,
            TimeInForce.CLS: self._AlpacaTimeInForce.CLS,
        }
        return mapping.get(tif, self._AlpacaTimeInForce.DAY)
    
    def _map_tif_from_alpaca(self, alpaca_tif) -> TimeInForce:
        """Map Alpaca's TimeInForce to ours."""
        tif_str = str(alpaca_tif).lower()
        mapping = {
            "day": TimeInForce.DAY,
            "gtc": TimeInForce.GTC,
            "ioc": TimeInForce.IOC,
            "fok": TimeInForce.FOK,
            "opg": TimeInForce.OPG,
            "cls": TimeInForce.CLS,
        }
        return mapping.get(tif_str, TimeInForce.DAY)
    
    def _parse_timeframe(self, timeframe: str):
        """Parse timeframe string to Alpaca TimeFrame."""
        timeframe = timeframe.lower()
        
        # Common mappings
        if timeframe in ("1min", "1m"):
            return self._TimeFrame.Minute
        elif timeframe in ("5min", "5m"):
            return self._TimeFrame(5, self._TimeFrameUnit.Minute)
        elif timeframe in ("15min", "15m"):
            return self._TimeFrame(15, self._TimeFrameUnit.Minute)
        elif timeframe in ("30min", "30m"):
            return self._TimeFrame(30, self._TimeFrameUnit.Minute)
        elif timeframe in ("1hour", "1h", "60min"):
            return self._TimeFrame.Hour
        elif timeframe in ("4hour", "4h"):
            return self._TimeFrame(4, self._TimeFrameUnit.Hour)
        elif timeframe in ("1day", "1d", "day"):
            return self._TimeFrame.Day
        elif timeframe in ("1week", "1w", "week"):
            return self._TimeFrame.Week
        elif timeframe in ("1month", "1mo", "month"):
            return self._TimeFrame.Month
        else:
            # Default to day
            return self._TimeFrame.Day
