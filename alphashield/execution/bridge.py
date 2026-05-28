"""Orchestration bridge between AlphaShield agents and Lumibot.

``run_agent_backtest`` is the single entry-point exposed as a Google AI
Studio / Gemini function-calling tool.  Given a set of target assets, a
dollar allocation, and a date range, it instantiates
``AlphaShieldYieldStrategy``, drives a Lumibot backtest via Yahoo Finance
historical data, and returns the key risk/return metrics that the agent
needs to decide whether the collateral pool will generate enough yield to
reduce the borrower's loan rate.

Usage from agent code::

    from alphashield.execution.bridge import run_agent_backtest

    result = run_agent_backtest(
        target_assets=["SPY", "GLD", "BTC-USD"],
        allocation_amount=12_000.0,
        start_date="2020-01-01",
        end_date="2023-12-31",
    )
    sharpe = result["sharpe_ratio"]
    cagr   = result["cagr"]

The function is intentionally dependency-light from the AlphaShield side:
it only imports from ``lumibot`` and the local ``strategies`` module, so
it can be tested in isolation without a live database.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from lumibot.backtesting import YahooDataBacktesting

from alphashield.execution.strategies import AlphaShieldYieldStrategy


def run_agent_backtest(
    target_assets: list[str],
    allocation_amount: float,
    start_date: str,
    end_date: str,
    risk_tolerance: str = "balanced",
) -> dict[str, Any]:
    """Run a Lumibot backtest and return performance metrics.

    This function is designed to be registered as a Gemini function-calling
    tool.  The agent calls it after computing the 40 % collateral pool from
    a loan request, receives the backtest metrics, and uses them to decide
    whether the strategy is viable and what rate reduction to offer the
    borrower.

    Args:
        target_assets: Ticker symbols for the collateral pool, e.g.
            ``["SPY", "GLD", "BTC-USD"]``.
        allocation_amount: Dollar amount to deploy — typically 40 % of the
            loan principal.
        start_date: Backtest start in ``YYYY-MM-DD`` format.
        end_date: Backtest end in ``YYYY-MM-DD`` format.
        risk_tolerance: Strategy aggressiveness — ``"conservative"``,
            ``"balanced"`` (default), or ``"aggressive"``.

    Returns:
        Dictionary with performance metrics::

            {
                "cagr": float,          # Compound annual growth rate (0–1)
                "sharpe_ratio": float,  # Annualised Sharpe ratio
                "max_drawdown": float,  # Maximum peak-to-trough drawdown (0–1)
                "total_return": float,  # Cumulative return over the period (0–1)
                "backtest_raw": ...     # Full lumibot result object (optional)
            }

    Raises:
        ValueError: If ``start_date`` or ``end_date`` cannot be parsed.
    """
    try:
        dt_start = datetime.strptime(start_date, "%Y-%m-%d")
        dt_end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            f"Dates must be in YYYY-MM-DD format. Got start={start_date!r}, end={end_date!r}."
        ) from exc

    strategy_params: dict[str, Any] = {
        "assets": target_assets,
        "allocation": allocation_amount,
        "risk_tolerance": risk_tolerance,
    }

    backtest_result = AlphaShieldYieldStrategy.run_backtest(
        YahooDataBacktesting,
        dt_start,
        dt_end,
        parameters=strategy_params,
        save_stats_file=False,
        show_plot=False,
        show_tearsheet=False,
        show_indicators=False,
    )

    return _extract_metrics(backtest_result)


def _extract_metrics(backtest_result: Any) -> dict[str, Any]:
    """Normalise the lumibot backtest result into a flat metrics dict.

    Lumibot returns a tuple ``(stats_df, indicators)`` from
    ``run_backtest``.  This helper extracts the values the agent cares
    about and provides safe defaults when a metric is unavailable.

    Args:
        backtest_result: Raw return value from ``Strategy.run_backtest``.

    Returns:
        Flat dict with ``cagr``, ``sharpe_ratio``, ``max_drawdown``, and
        ``total_return``.
    """
    metrics: dict[str, Any] = {
        "cagr": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown": 0.0,
        "total_return": 0.0,
    }

    if backtest_result is None:
        return metrics

    # Lumibot run_backtest returns (stats_df, indicators) as of v3.x
    stats = None
    if isinstance(backtest_result, tuple) and len(backtest_result) >= 1:
        stats = backtest_result[0]
    else:
        stats = backtest_result

    if stats is None:
        return metrics

    # stats is a pandas DataFrame with a single row (index = strategy name)
    try:
        import pandas as pd  # noqa: PLC0415

        if isinstance(stats, pd.DataFrame) and not stats.empty:
            row = stats.iloc[0]
            metrics["cagr"] = float(row.get("CAGR", 0.0) or 0.0)
            metrics["sharpe_ratio"] = float(row.get("Sharpe", 0.0) or 0.0)
            metrics["max_drawdown"] = float(row.get("Max Drawdown", 0.0) or 0.0)
            metrics["total_return"] = float(row.get("Total Return", 0.0) or 0.0)
    except Exception:  # noqa: BLE001
        # If stats layout changes in a future lumibot release, return safe defaults
        pass

    return metrics
