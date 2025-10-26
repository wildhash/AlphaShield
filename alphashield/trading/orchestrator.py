from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd

from .signal_generator import SignalAggregator
from .quantum_optimizer import QuantumPortfolioOptimizer
from .classical_optimizer import ClassicalPortfolioOptimizer
from .risk_manager import RiskManager
from .execution_engine import ExecutionEngine
from .portfolio_tracker import PortfolioTracker
from .data_provider import DataProvider
from .models.constraints import default_constraints

# Optional RL wiring (behind config flags)
try:
    from alphashield.rl.trainer import RLTrainer
    from alphashield.rl.reward import normalize_wealth_delta
except Exception:  # pragma: no cover - RL optional
    RLTrainer = None  # type: ignore
    def normalize_wealth_delta(x: float, baseline: float = 0.0, window_min: float = -0.05, window_max: float = 0.15) -> float:  # type: ignore
        return 0.0


class AutonomousTradingOrchestrator:
    """Fully autonomous trading system coordinating signals, optimization, and execution."""

    def __init__(self, config: Dict):
        self.signal_generator = SignalAggregator()
        self.quantum_optimizer = QuantumPortfolioOptimizer(config.get("dwave_token"))
        self.classical_optimizer = ClassicalPortfolioOptimizer()
        self.risk_manager = RiskManager()
        self.execution_engine = ExecutionEngine(config.get("broker_api"))
        self.portfolio_tracker = PortfolioTracker()
        self.data_provider = DataProvider()

        # State
        self.current_positions: Dict[str, float] = {}
        self.coverage_ratio: Optional[float] = None
        self.outstanding_payments: float = 0.0
        self._universe = config.get("universe", ["SPY", "QQQ", "EFA", "EEM", "TLT", "IEF", "LQD", "GLD", "AGG", "SHY"])

        # RL config and trainer (optional)
        self._rl_cfg: Dict = config.get("rl", {}) if isinstance(config, dict) else {}
        self._rl_enabled: bool = bool(self._rl_cfg.get("enabled", False)) and RLTrainer is not None
        self._rl_agent_name: str = str(self._rl_cfg.get("agent_name", "AlphaTrading"))
        self._prev_portfolio_value: Optional[float] = None
        self._rl_trainer: Optional[RLTrainer] = None
        if self._rl_enabled:
            # Initialize minimal trainer; db integration optional
            self._rl_trainer = RLTrainer(db_client=None, mock_mode=bool(self._rl_cfg.get("mock_mode", False)))  # type: ignore[arg-type]

    def run_daily_cycle(self, start: str = "2020-01-01", end: str = "2025-01-01") -> None:
        # Step 1: Risk check
        portfolio_value = self.portfolio_tracker.get_total_value()
        self.coverage_ratio = self.risk_manager.calculate_coverage_ratio(portfolio_value, self.outstanding_payments)

        emergency = self.risk_manager.emergency_mode_check(self.coverage_ratio, self.portfolio_tracker.get_drawdown())
        if emergency.action == "emergency":
            self._activate_emergency_mode()
            return

        # Step 2-3: Market regime and signals
        regime = self._detect_regime()
        market_data = self._fetch_market_data(self._universe, start, end)
        signals = self.signal_generator.aggregate_signals(market_data.prices, market_data.vix, regime=regime)

        # Step 4: Estimate returns and covariance
        expected_returns = self._forecast_returns(signals, market_data)
        covariance = self._estimate_covariance(market_data.returns)

        # Step 5: Optimize (optionally influenced by RL bandit)
        constraints = self._get_constraints(regime)

        rl_action: Optional[int] = None
        if self._rl_enabled and self._rl_trainer is not None:
            # Build recent metrics for reward shaping
            recent_metrics = {
                "wealth_delta": normalize_wealth_delta(
                    0.0 if self._prev_portfolio_value in (None, 0.0) else (portfolio_value - self._prev_portfolio_value) / max(self._prev_portfolio_value, 1e-9)
                ),
                "coverage_ratio": float(self.coverage_ratio) if self.coverage_ratio is not None else 1.0,
                "drawdown": float(self.portfolio_tracker.get_drawdown()),
                "anomaly": 0.0,
                "tax_risk": 0.0,
                "satisfaction": 0.5,
                "calibration": 1.0,
            }
            decision_input = {"regime": regime, "universe_size": len(self._universe)}
            # Provide compliant and fair output placeholders for gating
            agent_output = {"fairness": 0.9, "compliant": True}
            rl_info = self._rl_trainer.train_step(
                agent_name=self._rl_agent_name,
                user_id="portfolio",
                decision_input=decision_input,
                agent_output=agent_output,
                recent_metrics=recent_metrics,
                memory_hits=None,
            )
            rl_action = int(rl_info.get("action", 1))
            # Adjust constraints based on RL action mapping
            constraints = self._apply_rl_action_to_constraints(rl_action, constraints)

        if self.should_use_quantum():
            weights = self.quantum_optimizer.optimize_portfolio(expected_returns, covariance)
        else:
            weights = self.classical_optimizer.optimize(
                expected_returns,
                covariance,
                initial_weights=self._get_current_weights(expected_returns),
                constraints=constraints,
            )

        target_weights = {t: float(w) for t, w in zip(market_data.prices.columns, weights)}

        # Step 6: Execute trades
        trades = self.execution_engine.execute_rebalance(self.current_positions, target_weights, portfolio_value)

        # Step 7: Log
        self._log_decision(
            regime=regime,
            signals=signals,
            target_weights=target_weights,
            trades=trades,
            coverage_ratio=self.coverage_ratio,
            rl_action=rl_action,
            rl_enabled=self._rl_enabled,
        )

        # Update previous value for next cycle
        self._prev_portfolio_value = float(self.portfolio_tracker.get_total_value())

    def _activate_emergency_mode(self) -> None:
        target_weights = {"AGG": 0.50, "SHY": 0.30, "Cash": 0.20}
        self.execution_engine.execute_rebalance(
            self.current_positions, target_weights, self.portfolio_tracker.get_total_value()
        )
        self._send_alert(f"Coverage ratio dropped to {self.coverage_ratio:.2f}. Emergency mode active.")

    def should_use_quantum(self) -> bool:
        return self.portfolio_tracker.get_total_value() > 1_000_000 and len(self.current_positions) > 50

    def _detect_regime(self) -> str:
        # Placeholder heuristic: balanced
        return "balanced"

    def _fetch_market_data(self, universe: list[str], start: str, end: str):
        return self.data_provider.get_market_data(universe, start, end)

    def _forecast_returns(self, signals: pd.Series, market_data) -> np.ndarray:
        # Map signals to short-horizon expected returns via scaling factor
        scale = 0.10  # target annualized expectation scaling
        mu = signals.fillna(0.0).to_numpy(dtype=float) * scale
        return mu

    def _estimate_covariance(self, returns: pd.DataFrame) -> np.ndarray:
        return returns.cov().to_numpy(dtype=float)

    def _get_current_weights(self, expected_returns: np.ndarray) -> np.ndarray:
        # If no positions, return equal weight as initial guess
        n = expected_returns.shape[0]
        weights = np.ones(n) / n
        return weights

    def _get_constraints(self, regime: str) -> Dict:
        cons = default_constraints()
        if regime == "high_vol":
            cons["max_weight"] = 0.15
            cons["risk_aversion"] = 2.0
        elif regime == "low_vol":
            cons["max_weight"] = 0.25
            cons["risk_aversion"] = 0.8
        return cons

    def _apply_rl_action_to_constraints(self, action: int, constraints: Dict) -> Dict:
        """Map RL discrete action to portfolio constraints adjustments.

        Actions (AlphaTrading default):
          0: conservative_allocation -> higher risk_aversion, lower max_weight
          1: balanced_allocation    -> no change
          2: growth_allocation      -> lower risk_aversion, slightly higher max_weight
          3: rebalance_defensive    -> reduce max_weight moderately
          4: rebalance_aggressive   -> increase max_weight moderately
        """
        cons = dict(constraints) if constraints is not None else {}
        if action == 0:  # conservative
            cons["risk_aversion"] = float(cons.get("risk_aversion", 1.0)) * 1.5
            cons["max_weight"] = min(0.15, float(cons.get("max_weight", 0.20)))
        elif action == 2:  # growth
            cons["risk_aversion"] = max(0.5, float(cons.get("risk_aversion", 1.0)) * 0.7)
            cons["max_weight"] = min(0.35, float(cons.get("max_weight", 0.20)) + 0.05)
        elif action == 3:  # defensive rebalance
            cons["max_weight"] = min(0.18, float(cons.get("max_weight", 0.20)))
        elif action == 4:  # aggressive rebalance
            cons["max_weight"] = min(0.30, float(cons.get("max_weight", 0.20)) + 0.05)
        # action == 1 balanced: leave as-is
        return cons

    def _send_alert(self, message: str) -> None:
        print(f"ALERT: {message}")

    def _log_decision(self, **kwargs) -> None:
        print({k: (v if isinstance(v, (str, float)) else "...") for k, v in kwargs.items()})
