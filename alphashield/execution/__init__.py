"""Lumibot execution bridge for AlphaShield.

Provides the orchestration layer that translates agent decisions into
lumibot backtesting and live-trading parameters.
"""

from alphashield.execution.bridge import run_agent_backtest
from alphashield.execution.strategies import AlphaShieldYieldStrategy

__all__ = ["run_agent_backtest", "AlphaShieldYieldStrategy"]
