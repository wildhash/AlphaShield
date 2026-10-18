"""Paper trading adapter for testing without real money."""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime

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


class PaperTradingAdapter(BrokerAdapter):
    """Paper trading simulator for testing strategies without real money.

    Simulates order execution with configurable slippage and fills.
    """

    def __init__(
        self,
        initial_cash: float = 100_000.0,
        slippage_bps: float = 10.0,
        fill_probability: float = 1.0,
    ):
        """Initialize paper trading adapter.

        Args:
            initial_cash: Starting cash balance.
            slippage_bps: Slippage in basis points (default 10 bps = 0.1%).
            fill_probability: Probability of order fill (default 1.0 = 100%).
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.slippage_bps = slippage_bps
        self.fill_probability = fill_probability

        self.positions: dict[str, float] = defaultdict(float)  # ticker -> quantity
        self.orders: dict[str, Order] = {}  # order_id -> Order
        self.prices: dict[str, float] = {}  # ticker -> last price

        logger.info(
            f"Initialized paper trading adapter "
            f"(cash=${initial_cash:,.2f}, slippage={slippage_bps}bps)"
        )

    def set_price(self, ticker: str, price: float):
        """Set current price for ticker (for simulation).

        Args:
            ticker: Stock ticker.
            price: Current price.
        """
        self.prices[ticker] = price

    def set_prices(self, prices: dict[str, float]):
        """Set multiple prices at once.

        Args:
            prices: Dictionary of ticker -> price.
        """
        self.prices.update(prices)

    def get_account(self) -> Account:
        """Get account information."""
        # Calculate portfolio value
        portfolio_value = self.cash
        for ticker, qty in self.positions.items():
            price = self.prices.get(ticker, 100.0)
            portfolio_value += qty * price

        return Account(
            id="paper_account",
            cash=self.cash,
            portfolio_value=portfolio_value,
            buying_power=self.cash,
            equity=portfolio_value,
            last_equity=portfolio_value,
            multiplier=1.0,
            currency="USD",
        )

    def get_positions(self) -> list[Position]:
        """Get all current positions."""
        positions = []

        for ticker, qty in self.positions.items():
            if abs(qty) < 0.01:  # Skip near-zero positions
                continue

            price = self.prices.get(ticker, 100.0)
            market_value = qty * price

            # Simplified P&L calculation (would need entry price tracking for real)
            avg_entry = price  # Placeholder
            unrealized_pnl = 0.0
            unrealized_pnl_pct = 0.0

            positions.append(
                Position(
                    ticker=ticker,
                    quantity=qty,
                    avg_entry_price=avg_entry,
                    current_price=price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_pct=unrealized_pnl_pct,
                )
            )

        return positions

    def get_position(self, ticker: str) -> Position | None:
        """Get position for specific ticker."""
        qty = self.positions.get(ticker, 0.0)

        if abs(qty) < 0.01:
            return None

        price = self.prices.get(ticker, 100.0)
        market_value = qty * price

        return Position(
            ticker=ticker,
            quantity=qty,
            avg_entry_price=price,
            current_price=price,
            market_value=market_value,
            unrealized_pnl=0.0,
            unrealized_pnl_pct=0.0,
        )

    def submit_order(
        self,
        ticker: str,
        qty: float,
        side: OrderSide,
        type: OrderType = OrderType.MARKET,
        limit_price: float | None = None,
        stop_price: float | None = None,
        time_in_force: str = "day",
    ) -> Order:
        """Submit an order."""
        order_id = str(uuid.uuid4())

        # Get current price
        price = self.prices.get(ticker, 100.0)

        # Apply slippage
        slippage_factor = self.slippage_bps / 10000.0
        if side == OrderSide.BUY:
            execution_price = price * (1.0 + slippage_factor)
        else:
            execution_price = price * (1.0 - slippage_factor)

        # For limit orders, check if we can fill
        if type == OrderType.LIMIT:
            if limit_price is None:
                return Order(
                    id=order_id,
                    ticker=ticker,
                    quantity=qty,
                    side=side,
                    type=type,
                    status=OrderStatus.REJECTED,
                    error_message="limit_price required for limit orders",
                )

            # Check if limit price allows fill
            if (
                side == OrderSide.BUY
                and execution_price > limit_price
                or side == OrderSide.SELL
                and execution_price < limit_price
            ):
                status = OrderStatus.SUBMITTED  # Would wait for better price
            else:
                status = OrderStatus.FILLED
                execution_price = limit_price
        else:
            # Market order fills immediately
            status = OrderStatus.FILLED

        # Check if we have sufficient funds/shares
        if status == OrderStatus.FILLED:
            if side == OrderSide.BUY:
                cost = qty * execution_price
                if cost > self.cash:
                    return Order(
                        id=order_id,
                        ticker=ticker,
                        quantity=qty,
                        side=side,
                        type=type,
                        status=OrderStatus.REJECTED,
                        error_message=f"Insufficient funds (need ${cost:.2f}, have ${self.cash:.2f})",
                    )

                # Execute buy
                self.cash -= cost
                self.positions[ticker] += qty

            else:  # SELL
                current_position = self.positions.get(ticker, 0.0)
                if qty > current_position:
                    return Order(
                        id=order_id,
                        ticker=ticker,
                        quantity=qty,
                        side=side,
                        type=type,
                        status=OrderStatus.REJECTED,
                        error_message=f"Insufficient shares (need {qty}, have {current_position})",
                    )

                # Execute sell
                proceeds = qty * execution_price
                self.cash += proceeds
                self.positions[ticker] -= qty

        # Create order object
        order = Order(
            id=order_id,
            ticker=ticker,
            quantity=qty,
            side=side,
            type=type,
            status=status,
            limit_price=limit_price,
            stop_price=stop_price,
            filled_quantity=qty if status == OrderStatus.FILLED else 0.0,
            filled_avg_price=execution_price if status == OrderStatus.FILLED else None,
            submitted_at=datetime.utcnow(),
            filled_at=datetime.utcnow() if status == OrderStatus.FILLED else None,
        )

        self.orders[order_id] = order

        logger.info(
            f"Paper order: {side.value} {qty} {ticker} @ ${execution_price:.2f} "
            f"(status={status.value})"
        )

        return order

    def get_order(self, order_id: str) -> Order:
        """Get order status."""
        if order_id not in self.orders:
            raise ValueError(f"Order {order_id} not found")
        return self.orders[order_id]

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if order_id not in self.orders:
            return False

        order = self.orders[order_id]
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            return False

        order.status = OrderStatus.CANCELLED
        logger.info(f"Cancelled paper order {order_id}")
        return True

    def get_orders(self, status: OrderStatus | None = None, limit: int = 100) -> list[Order]:
        """Get orders, optionally filtered by status."""
        orders = list(self.orders.values())

        if status:
            orders = [o for o in orders if o.status == status]

        # Sort by submission time (newest first)
        orders.sort(key=lambda o: o.submitted_at or datetime.min, reverse=True)

        return orders[:limit]

    def get_quote(self, ticker: str) -> dict[str, float]:
        """Get real-time quote for ticker."""
        price = self.prices.get(ticker, 100.0)

        # Simulate bid-ask spread (5 bps)
        spread = price * 0.0005

        return {
            "bid": price - spread / 2,
            "ask": price + spread / 2,
            "bid_size": 100.0,
            "ask_size": 100.0,
            "last": price,
        }

    def close_position(self, ticker: str) -> Order:
        """Close entire position for ticker."""
        qty = self.positions.get(ticker, 0.0)

        if abs(qty) < 0.01:
            raise ValueError(f"No position exists for {ticker}")

        side = OrderSide.SELL if qty > 0 else OrderSide.BUY

        return self.submit_order(
            ticker=ticker,
            qty=abs(qty),
            side=side,
            type=OrderType.MARKET,
        )

    def close_all_positions(self) -> list[Order]:
        """Close all positions."""
        orders = []

        for ticker in list(self.positions.keys()):
            try:
                order = self.close_position(ticker)
                orders.append(order)
            except Exception as e:
                logger.error(f"Failed to close position {ticker}: {e}")

        return orders
