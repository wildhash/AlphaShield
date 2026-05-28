"""Custom Lumibot strategy classes for AlphaShield.

AlphaShieldYieldStrategy implements a volatility-managed, yield-generation
portfolio that mirrors the 40% collateral-pool allocation used when a
self-funding loan is originated.  The strategy accepts dynamic asset
weights and a risk tolerance so that the Gemini agent can parameterise it
at run-time.
"""

from __future__ import annotations

from typing import Any

from lumibot.strategies import Strategy


class AlphaShieldYieldStrategy(Strategy):
    """Volatility-managed yield strategy for the AlphaShield collateral pool.

    Parameters (passed via ``parameters`` dict to ``run_backtest``):
        assets (list[str]): Ticker symbols to trade, e.g. ``["SPY", "GLD", "BTC-USD"]``.
        allocation (float): Dollar amount available to deploy (the 40% pool).
        risk_tolerance (str): ``"conservative"``, ``"balanced"`` (default), or
            ``"aggressive"``.  Controls position-sizing and rebalance frequency.

    The strategy rebalances monthly.  Target weights are derived from the
    equal-risk-contribution (ERC) heuristic scaled by the requested risk
    tolerance, keeping each position below a hard 40% cap.
    """

    # ------------------------------------------------------------------
    # Lumibot lifecycle hooks
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        self.assets: list[str] = self.parameters.get("assets", ["SPY", "GLD"])
        self.allocation: float = float(self.parameters.get("allocation", 10_000.0))
        self.risk_tolerance: str = self.parameters.get("risk_tolerance", "balanced")

        # Rebalance frequencies by risk profile (in trading days)
        self._rebalance_days = {"conservative": 30, "balanced": 21, "aggressive": 10}
        self.sleeptime = f"{self._rebalance_days.get(self.risk_tolerance, 21)}D"

        # Hard cap on any single position
        self._max_weight = {"conservative": 0.30, "balanced": 0.40, "aggressive": 0.50}[
            self.risk_tolerance
        ]

    def on_trading_iteration(self) -> None:
        """Rebalance the collateral pool on each scheduled iteration."""
        prices = self._get_last_prices()
        if not prices:
            return

        weights = self._compute_weights(prices)
        self._rebalance(weights)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_last_prices(self) -> dict[str, float]:
        """Return the most recent close price for each tracked asset."""
        prices: dict[str, float] = {}
        for ticker in self.assets:
            bar = self.get_last_price(ticker)
            if bar is not None:
                prices[ticker] = float(bar)
        return prices

    def _compute_weights(self, prices: dict[str, float]) -> dict[str, float]:
        """Compute equal-risk-contribution target weights.

        Falls back to equal-weight allocation when historical data is
        insufficient for volatility estimation.
        """
        n = len(prices)
        if n == 0:
            return {}

        # Attempt volatility-weighted allocation (inverse-vol = ERC proxy)
        vols: dict[str, float] = {}
        for ticker in prices:
            try:
                bars = self.get_historical_prices(ticker, 30, "day")
                if bars is not None and len(bars.df) >= 10:
                    import numpy as np  # noqa: PLC0415

                    daily_rets = bars.df["close"].pct_change().dropna()
                    vols[ticker] = float(daily_rets.std()) or 1.0
                else:
                    vols[ticker] = 1.0
            except Exception:  # noqa: BLE001
                vols[ticker] = 1.0

        inv_vol = {t: 1.0 / v for t, v in vols.items()}
        total = sum(inv_vol.values())
        weights = {t: min(iv / total, self._max_weight) for t, iv in inv_vol.items()}

        # Re-normalise after capping
        total_w = sum(weights.values())
        if total_w > 0:
            weights = {t: w / total_w for t, w in weights.items()}

        return weights

    def _rebalance(self, weights: dict[str, float]) -> None:
        """Submit orders to align the portfolio with ``weights``."""
        portfolio_value = self.portfolio_value or self.allocation
        for ticker, target_weight in weights.items():
            target_value = portfolio_value * target_weight
            current_position = self.get_position(ticker)
            current_value = (
                current_position.quantity * self.get_last_price(ticker)
                if current_position
                else 0.0
            )
            delta = target_value - current_value

            price = self.get_last_price(ticker)
            if price and price > 0 and abs(delta) > price:
                qty = int(delta / price)
                if qty != 0:
                    order = self.create_order(ticker, abs(qty), "buy" if qty > 0 else "sell")
                    self.submit_order(order)
