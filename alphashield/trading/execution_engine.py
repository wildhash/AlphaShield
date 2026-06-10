from __future__ import annotations

import logging

import numpy as np

from alphashield.trading.broker_adapters import BrokerAdapter, OrderSide, OrderType

logger = logging.getLogger(__name__)


class SlippageModel:
    """Estimate transaction costs and slippage based on order size and volume."""

    def estimate(self, ticker: str, quantity: float) -> float:
        avg_daily_volume = self._get_avg_volume(ticker)
        if avg_daily_volume <= 0:
            return 0.005  # 50 bps default
        impact_ratio = float(quantity) / float(avg_daily_volume)
        base_slippage = 0.001  # 10 bps
        slippage = base_slippage * np.sqrt(max(impact_ratio * 100.0, 0.0))
        return float(min(slippage, 0.01))  # Cap at 100 bps

    def _get_avg_volume(self, ticker: str) -> float:
        # Placeholder: to be connected to data provider
        return 1_000_000.0


class ExecutionEngine:
    """Handle order routing and execution with a broker API.

    Supports live trading via Alpaca or paper trading simulation.
    """

    def __init__(self, broker: BrokerAdapter, data_provider=None) -> None:
        """Initialize execution engine.

        Args:
            broker: Broker adapter for order execution.
            data_provider: Optional data provider for prices and volume.
        """
        self.broker = broker
        self.data_provider = data_provider
        self.slippage_model = SlippageModel()

        logger.info(f"Initialized execution engine with broker: {type(broker).__name__}")

    def execute_rebalance(
        self,
        current_positions: dict[str, float] | None = None,  # {ticker: quantity}
        target_weights: dict[str, float] | None = None,  # {ticker: weight}
        total_value: float | None = None,
    ) -> dict[str, dict]:
        """Execute portfolio rebalancing.

        Args:
            current_positions: Current positions {ticker: quantity}.
                If None, will fetch from broker.
            target_weights: Target portfolio weights {ticker: weight}.
            total_value: Total portfolio value. If None, will fetch from broker.

        Returns:
            Dictionary of order confirmations {ticker: order}.
        """
        # Fetch current positions if not provided
        if current_positions is None:
            positions = self.broker.get_positions()
            current_positions = {pos.ticker: pos.quantity for pos in positions}

        # Fetch total value if not provided
        if total_value is None:
            account = self.broker.get_account()
            total_value = account.portfolio_value

        if target_weights is None:
            raise ValueError("target_weights required for rebalancing")

        trades = self._calculate_trades(current_positions, target_weights, total_value)
        confirmations: dict[str, dict] = {}

        logger.info(f"Executing rebalance: {len(trades)} trades, portfolio value ${total_value:,.2f}")

        # Sells first (to free up cash)
        for ticker, quantity in trades.items():
            if quantity < 0:
                try:
                    estimated_slippage = self.slippage_model.estimate(ticker, abs(quantity))
                    limit_price = self._get_conservative_limit_price(ticker, "sell", estimated_slippage)
                    order = self.broker.submit_order(
                        ticker=ticker,
                        qty=int(abs(quantity)),
                        side=OrderSide.SELL,
                        type=OrderType.LIMIT,
                        limit_price=limit_price,
                    )
                    confirmations[ticker] = {
                        "order_id": order.id,
                        "status": order.status.value,
                        "quantity": abs(quantity),
                        "side": "sell",
                        "limit_price": limit_price,
                    }
                    logger.info(f"Sell order: {ticker} qty={abs(quantity)} @ ${limit_price:.2f}")
                except Exception as e:
                    logger.error(f"Failed to submit sell order for {ticker}: {e}")
                    confirmations[ticker] = {"error": str(e), "side": "sell"}

        # Buys after (using freed cash)
        for ticker, quantity in trades.items():
            if quantity > 0:
                try:
                    estimated_slippage = self.slippage_model.estimate(ticker, quantity)
                    limit_price = self._get_conservative_limit_price(ticker, "buy", estimated_slippage)
                    order = self.broker.submit_order(
                        ticker=ticker,
                        qty=int(quantity),
                        side=OrderSide.BUY,
                        type=OrderType.LIMIT,
                        limit_price=limit_price,
                    )
                    confirmations[ticker] = {
                        "order_id": order.id,
                        "status": order.status.value,
                        "quantity": quantity,
                        "side": "buy",
                        "limit_price": limit_price,
                    }
                    logger.info(f"Buy order: {ticker} qty={quantity} @ ${limit_price:.2f}")
                except Exception as e:
                    logger.error(f"Failed to submit buy order for {ticker}: {e}")
                    confirmations[ticker] = {"error": str(e), "side": "buy"}

        return confirmations

    def _calculate_trades(
        self,
        current_positions: dict[str, float],
        target_weights: dict[str, float],
        total_value: float,
    ) -> dict[str, int]:
        trades: dict[str, int] = {}
        tickers = set(current_positions.keys()) | set(target_weights.keys())
        for ticker in tickers:
            current_qty = float(current_positions.get(ticker, 0.0))
            price = self._get_price(ticker)
            current_value = current_qty * price
            target_value = float(target_weights.get(ticker, 0.0)) * float(total_value)
            delta_value = target_value - current_value
            delta_shares = delta_value / max(price, 1e-6)
            if abs(delta_shares) > 1.0:
                trades[ticker] = int(round(delta_shares))
        return trades

    def _get_conservative_limit_price(self, ticker: str, side: str, slippage: float) -> float:
        price = self._get_price(ticker)
        if side == "buy":
            return price * (1.0 + slippage)
        else:
            return price * (1.0 - slippage)

    def _get_price(self, ticker: str) -> float:
        """Get current price for ticker.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            Current price.
        """
        # Try to get from broker quote
        try:
            quote = self.broker.get_quote(ticker)
            return quote.get("last", 100.0)
        except Exception:
            # Fallback to data provider if available
            if self.data_provider and hasattr(self.data_provider, "get_price"):
                try:
                    return self.data_provider.get_price(ticker)
                except Exception:
                    pass

            # Default fallback
            logger.warning(f"Could not get price for {ticker}, using default $100")
            return 100.0

    def get_order_status(self, order_id: str) -> dict:
        """Get status of an order.

        Args:
            order_id: Order ID to check.

        Returns:
            Order status dictionary.
        """
        try:
            order = self.broker.get_order(order_id)
            return {
                "order_id": order.id,
                "ticker": order.ticker,
                "status": order.status.value,
                "filled_quantity": order.filled_quantity,
                "filled_avg_price": order.filled_avg_price,
            }
        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {e}")
            return {"error": str(e)}

    def monitor_orders(self, order_ids: list[str], timeout_seconds: int = 60) -> dict[str, dict]:
        """Monitor orders until filled or timeout.

        Args:
            order_ids: List of order IDs to monitor.
            timeout_seconds: Maximum time to wait.

        Returns:
            Dictionary of order statuses {order_id: status}.
        """
        import time

        start_time = time.time()
        statuses = {}

        while time.time() - start_time < timeout_seconds:
            all_done = True

            for order_id in order_ids:
                if order_id in statuses:
                    continue

                status = self.get_order_status(order_id)
                order_status = status.get("status", "unknown")

                if order_status in ["filled", "cancelled", "rejected", "expired"]:
                    statuses[order_id] = status
                else:
                    all_done = False

            if all_done:
                break

            time.sleep(1)  # Poll every second

        # Get final status for any remaining orders
        for order_id in order_ids:
            if order_id not in statuses:
                statuses[order_id] = self.get_order_status(order_id)

        return statuses
