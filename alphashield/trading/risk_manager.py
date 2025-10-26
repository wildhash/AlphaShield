from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np


@dataclass
class EmergencyDecision:
    action: str
    instructions: str


class RiskManager:
    """
    Real-time risk monitoring and position sizing with coverage ratio protocols.
    """

    def __init__(self, max_drawdown: float = 0.15) -> None:
        self.max_drawdown = max_drawdown
        self.peak_value: float | None = None

    def calculate_coverage_ratio(self, portfolio_value: float, outstanding_payments: float) -> float:
        if outstanding_payments <= 0:
            return float("inf")
        return float(portfolio_value) / float(outstanding_payments)

    def position_sizing_kelly(
        self, win_rate: float, avg_win: float, avg_loss: float, current_cr: float
    ) -> float:
        if avg_loss == 0:
            return 0.0
        b = avg_win / avg_loss
        kelly_fraction = (win_rate * b - (1 - win_rate)) / b
        kelly_fraction = float(np.clip(kelly_fraction, 0.0, 0.25))
        if current_cr < 1.5:
            cr_adjustment = max(0.0, (current_cr - 1.2) / 0.3)
            kelly_fraction *= cr_adjustment
        return kelly_fraction

    def check_stop_loss(self, current_value: float, entry_value: float, stop_loss_pct: float = 0.10) -> bool:
        if entry_value <= 0:
            return False
        loss = (entry_value - current_value) / entry_value
        return bool(loss > stop_loss_pct)

    def calculate_var(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        if returns.size == 0:
            return 0.0
        return float(np.percentile(returns, (1 - confidence) * 100))

    def calculate_cvar(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        if returns.size == 0:
            return 0.0
        var = self.calculate_var(returns, confidence)
        tail = returns[returns <= var]
        if tail.size == 0:
            return var
        return float(tail.mean())

    def emergency_mode_check(self, coverage_ratio: float, portfolio_drawdown: float) -> EmergencyDecision:
        if coverage_ratio < 1.2 or portfolio_drawdown > self.max_drawdown:
            return EmergencyDecision(
                action="emergency",
                instructions="Move 80% to cash/bonds immediately. Halt new loans.",
            )
        elif coverage_ratio < 1.3:
            return EmergencyDecision(
                action="defensive",
                instructions="Reduce equity exposure by 30%. Increase bonds.",
            )
        else:
            return EmergencyDecision(action="normal", instructions="Proceed with standard rebalancing.")
