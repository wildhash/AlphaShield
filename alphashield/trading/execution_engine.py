from __future__ import annotations

from typing import Dict

import numpy as np


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
    """Handle order routing and execution with a broker API."""

    def __init__(self, broker_api) -> None:
        self.broker = broker_api
        self.slippage_model = SlippageModel()

    def execute_rebalance(
        self,
        current_positions: Dict[str, float],  # {ticker: quantity}
        target_weights: Dict[str, float],  # {ticker: weight}
        total_value: float,
    ) -> Dict[str, dict]:
        trades = self._calculate_trades(current_positions, target_weights, total_value)
        confirmations: Dict[str, dict] = {}

        # Sells first
        for ticker, quantity in trades.items():
            if quantity < 0:
                estimated_slippage = self.slippage_model.estimate(ticker, abs(quantity))
                limit_price = self._get_conservative_limit_price(ticker, "sell", estimated_slippage)
                confirmation = self.broker.submit_order(
                    ticker=ticker,
                    qty=int(abs(quantity)),
                    side="sell",
                    type="limit",
                    limit_price=limit_price,
                )
                confirmations[ticker] = confirmation

        # Buys after
        for ticker, quantity in trades.items():
            if quantity > 0:
                estimated_slippage = self.slippage_model.estimate(ticker, quantity)
                limit_price = self._get_conservative_limit_price(ticker, "buy", estimated_slippage)
                confirmation = self.broker.submit_order(
                    ticker=ticker,
                    qty=int(quantity),
                    side="buy",
                    type="limit",
                    limit_price=limit_price,
                )
                confirmations[ticker] = confirmation

        return confirmations

    def _calculate_trades(
        self,
        current_positions: Dict[str, float],
        target_weights: Dict[str, float],
        total_value: float,
    ) -> Dict[str, int]:
        trades: Dict[str, int] = {}
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
        # Placeholder for data provider integration
        return 100.0
