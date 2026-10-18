"""Unit tests for alphashield.execution.bridge.

All lumibot I/O is mocked so these tests run without network access or
a real lumibot installation.
"""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from alphashield.execution.bridge import _extract_metrics, run_agent_backtest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_stats_df(
    cagr: float = 0.12,
    sharpe: float = 1.1,
    max_dd: float = -0.08,
    total_return: float = 0.40,
) -> pd.DataFrame:
    """Build a minimal lumibot-style stats DataFrame."""
    return pd.DataFrame(
        {
            "CAGR": [cagr],
            "Sharpe": [sharpe],
            "Max Drawdown": [max_dd],
            "Total Return": [total_return],
        }
    )


# ---------------------------------------------------------------------------
# _extract_metrics
# ---------------------------------------------------------------------------


class TestExtractMetrics:
    def test_none_returns_zeroed_dict(self):
        result = _extract_metrics(None)
        assert result == {
            "cagr": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "total_return": 0.0,
        }

    def test_tuple_result_parsed(self):
        stats = _make_stats_df(cagr=0.15, sharpe=1.3, max_dd=-0.10, total_return=0.50)
        result = _extract_metrics((stats, {}))
        assert pytest.approx(result["cagr"], abs=1e-9) == 0.15
        assert pytest.approx(result["sharpe_ratio"], abs=1e-9) == 1.3
        assert pytest.approx(result["max_drawdown"], abs=1e-9) == -0.10
        assert pytest.approx(result["total_return"], abs=1e-9) == 0.50

    def test_bare_dataframe_result_parsed(self):
        stats = _make_stats_df(cagr=0.08, sharpe=0.9, max_dd=-0.05, total_return=0.25)
        result = _extract_metrics(stats)
        assert pytest.approx(result["cagr"], abs=1e-9) == 0.08

    def test_empty_dataframe_returns_zeroed_dict(self):
        result = _extract_metrics(pd.DataFrame())
        assert result["cagr"] == 0.0

    def test_missing_columns_returns_zeroed_dict(self):
        # DataFrame exists but has unrecognised columns
        stats = pd.DataFrame({"foo": [1], "bar": [2]})
        result = _extract_metrics((stats,))
        assert result == {
            "cagr": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "total_return": 0.0,
        }


# ---------------------------------------------------------------------------
# run_agent_backtest
# ---------------------------------------------------------------------------


class TestRunAgentBacktest:
    """Tests for run_agent_backtest, mocking the lumibot backtest call."""

    @patch("alphashield.execution.bridge.AlphaShieldYieldStrategy.run_backtest")
    def test_returns_metrics_dict(self, mock_run_backtest):
        stats = _make_stats_df(cagr=0.20, sharpe=1.5, max_dd=-0.12, total_return=0.80)
        mock_run_backtest.return_value = (stats, {})

        result = run_agent_backtest(
            target_assets=["SPY", "GLD"],
            allocation_amount=10_000.0,
            start_date="2021-01-01",
            end_date="2022-12-31",
        )

        assert "cagr" in result
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result
        assert "total_return" in result
        assert pytest.approx(result["cagr"], abs=1e-9) == 0.20

    @patch("alphashield.execution.bridge.AlphaShieldYieldStrategy.run_backtest")
    def test_passes_strategy_params(self, mock_run_backtest):
        mock_run_backtest.return_value = (_make_stats_df(), {})

        run_agent_backtest(
            target_assets=["SPY", "BTC-USD"],
            allocation_amount=5_000.0,
            start_date="2022-01-01",
            end_date="2023-01-01",
            risk_tolerance="aggressive",
        )

        # Ensure lumibot run_backtest was invoked at all
        mock_run_backtest.assert_called_once()

    @patch("alphashield.execution.bridge.AlphaShieldYieldStrategy.run_backtest")
    def test_backtesting_class_passed(self, mock_run_backtest):
        """YahooDataBacktesting must be the first positional argument."""
        from lumibot.backtesting import YahooDataBacktesting  # noqa: PLC0415

        mock_run_backtest.return_value = (_make_stats_df(), {})

        run_agent_backtest(
            target_assets=["SPY"],
            allocation_amount=1_000.0,
            start_date="2022-01-01",
            end_date="2022-06-30",
        )

        args, _ = mock_run_backtest.call_args
        assert args[0] is YahooDataBacktesting

    def test_invalid_start_date_raises(self):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            run_agent_backtest(
                target_assets=["SPY"],
                allocation_amount=1_000.0,
                start_date="01-01-2022",  # wrong format
                end_date="2022-12-31",
            )

    def test_invalid_end_date_raises(self):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            run_agent_backtest(
                target_assets=["SPY"],
                allocation_amount=1_000.0,
                start_date="2022-01-01",
                end_date="not-a-date",
            )

    @patch("alphashield.execution.bridge.AlphaShieldYieldStrategy.run_backtest")
    def test_none_backtest_result_returns_safe_defaults(self, mock_run_backtest):
        mock_run_backtest.return_value = None

        result = run_agent_backtest(
            target_assets=["SPY"],
            allocation_amount=1_000.0,
            start_date="2022-01-01",
            end_date="2022-12-31",
        )

        assert result["cagr"] == 0.0
        assert result["sharpe_ratio"] == 0.0
