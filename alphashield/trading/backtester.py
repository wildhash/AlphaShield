from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

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

    # Optional RL wiring (behind config flags)
    try:
        from alphashield.rl.trainer import RLTrainer  # type: ignore
        from alphashield.rl.reward import normalize_wealth_delta  # type: ignore
    except Exception:  # pragma: no cover - RL optional
        RLTrainer = None  # type: ignore
        def normalize_wealth_delta(x: float, baseline: float = 0.0, window_min: float = -0.05, window_max: float = 0.15) -> float:  # type: ignore
            return 0.0

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
        rl: Optional[Dict] = None,
    ) -> Dict:
        portfolio_value = initial_capital
        portfolio_values = []
        positions: Dict[str, float] = {t: 0.0 for t in prices.columns}

        # RL setup (optional)
        rl_cfg = rl or {}
        rl_enabled: bool = bool(rl_cfg.get("enabled", False)) and self.RLTrainer is not None  # type: ignore[attr-defined]
        rl_trainer = None
        if rl_enabled:
            # Initialize trainer with mock mode by default for backtests unless provided
            rl_trainer = self.RLTrainer(db_client=None, mock_mode=bool(rl_cfg.get("mock_mode", True)))  # type: ignore[call-arg]
            rl_agent_name = str(rl_cfg.get("agent_name", "AlphaTrading"))
            prev_value: Optional[float] = None

        last_month = None
        for date, row in prices.iterrows():
            # Rebalance monthly on first business day
            if last_month != date.month:
                signals = strategy.generate_signals(prices.loc[:date])
                target_weights = strategy.optimize(signals)

                # RL bandit can adjust target weights by risk profile action
                if rl_enabled and rl_trainer is not None:
                    wealth_delta = 0.0 if prev_value in (None, 0.0) else (portfolio_value - prev_value) / max(prev_value, 1e-9)
                    recent_metrics = {
                        "wealth_delta": self.normalize_wealth_delta(wealth_delta),  # type: ignore[attr-defined]
                        "coverage_ratio": 1.4,  # heuristic; detailed CR not tracked in backtester
                        "drawdown": 0.0,
                        "anomaly": 0.0,
                        "tax_risk": 0.0,
                        "satisfaction": 0.5,
                        "calibration": 1.0,
                    }
                    decision_input = {"date": str(date)}
                    agent_output = {"fairness": 0.9, "compliant": True}
                    rl_info = rl_trainer.train_step(
                        agent_name=rl_agent_name,
                        user_id="backtest",
                        decision_input=decision_input,
                        agent_output=agent_output,
                        recent_metrics=recent_metrics,
                        memory_hits=None,
                    )
                    rl_action = int(rl_info.get("action", 1))
                    target_weights = self._apply_rl_action_to_weights(target_weights, rl_action)

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
            if rl_enabled:
                prev_value = portfolio_value

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

    def _apply_rl_action_to_weights(self, target_weights: Dict[str, float], action: int) -> Dict[str, float]:
        """Clamp and renormalize weights based on RL action profile.

        Mirrors orchestrator's constraint mapping:
          0: conservative -> cap 0.15
          1: balanced    -> cap 0.20
          2: growth      -> cap 0.35
          3: defensive   -> cap 0.18
          4: aggressive  -> cap 0.30
        """
        caps = {0: 0.15, 1: 0.20, 2: 0.35, 3: 0.18, 4: 0.30}
        cap = caps.get(int(action), 0.20)
        # Clip
        clipped = {k: min(max(float(v), 0.0), cap) for k, v in target_weights.items()}
        total = sum(clipped.values())
        if total <= 0:
            # fallback to equal weight
            n = len(clipped)
            return {k: 1.0 / n for k in clipped}
        return {k: v / total for k, v in clipped.items()}
