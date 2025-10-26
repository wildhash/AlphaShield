from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    total_return: float
    cagr: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    avg_monthly_return: float


class Backtester:
    """Historical simulation of trading strategy."""

    def _calculate_cagr(self, portfolio_values: pd.Series) -> float:
        if portfolio_values.empty:
            return 0.0
        start_value = float(portfolio_values.iloc[0])
        end_value = float(portfolio_values.iloc[-1])
        num_days = len(portfolio_values)
        years = num_days / 252.0
        if start_value <= 0 or years <= 0:
            return 0.0
        return (end_value / start_value) ** (1 / years) - 1.0

    def _calculate_max_drawdown(self, portfolio_values: pd.Series) -> float:
        if portfolio_values.empty:
            return 0.0
        running_max = portfolio_values.cummax()
        drawdowns = (running_max - portfolio_values) / running_max.replace(0, np.nan)
        return float(drawdowns.max(skipna=True))

    def run_backtest(
        self,
        strategy,
        prices: pd.DataFrame,
        initial_capital: float = 100000.0,
    ) -> Dict:
        portfolio_value = initial_capital
        portfolio_values = []
        positions: Dict[str, float] = {t: 0.0 for t in prices.columns}

        last_month = None
        for date, row in prices.iterrows():
            # Rebalance monthly on first business day
            if last_month != date.month:
                signals = strategy.generate_signals(prices.loc[:date])
                target_weights = strategy.optimize(signals)

                # Convert weights to shares using today's close
                total_value = portfolio_value + sum(positions[t] * row[t] for t in positions)
                for t in positions:
                    target_value = target_weights.get(t, 0.0) * total_value
                    current_value = positions[t] * row[t]
                    delta_value = target_value - current_value
                    delta_shares = delta_value / max(row[t], 1e-6)
                    positions[t] += delta_shares
                last_month = date.month

            # Mark-to-market
            portfolio_value = sum(positions[t] * row[t] for t in positions)
            portfolio_values.append(portfolio_value)

        series = pd.Series(portfolio_values, index=prices.index)
        returns = series.pct_change().dropna()
        sharpe = 0.0
        if returns.std() > 0:
            sharpe = float(returns.mean() / returns.std() * np.sqrt(252))
        win_rate = float((returns > 0).sum() / len(returns)) if len(returns) > 0 else 0.0
        avg_monthly = float(returns.resample("M").sum().mean()) if len(returns) > 0 else 0.0

        result = {
            "total_return": float(series.iloc[-1] / series.iloc[0] - 1.0) if len(series) > 1 else 0.0,
            "cagr": float(self._calculate_cagr(series)),
            "sharpe_ratio": sharpe,
            "max_drawdown": float(self._calculate_max_drawdown(series)),
            "win_rate": win_rate,
            "avg_monthly_return": avg_monthly,
        }
        return result
