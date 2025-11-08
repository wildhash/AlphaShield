from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any

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


from .data_validator import validate_prices
from .coverage_monitor import monthly_payment, coverage_ratio as compute_cr, is_coverage_ok
from .portfolio_optimizer import PortfolioOptimizer, OptimizerConfig
from .signal_generator import momentum_signal, trend_sma200_signal, mean_reversion_signal, combine_signals
from .execution_simulator import simulate_execution
from alphashield.utils.metrics import time_block


class Backtester:
    """Monthly backtester implementing the AlphaShield flow."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def _cagr(self, series: pd.Series) -> float:
        if series.empty:
            return 0.0
        years = len(series) / 252.0
        if years <= 0 or series.iloc[0] <= 0:
            return 0.0
        return float((series.iloc[-1] / series.iloc[0]) ** (1 / years) - 1.0)

    def _volatility(self, returns: pd.Series) -> float:
        if returns.std(ddof=0) == 0:
            return 0.0
        return float(returns.std(ddof=0) * np.sqrt(252))

    def _sharpe(self, returns: pd.Series) -> float:
        std = returns.std(ddof=0)
        if std == 0:
            return 0.0
        return float(returns.mean() / std * np.sqrt(252))

    def _max_dd(self, series: pd.Series) -> float:
        if series.empty:
            return 0.0
        roll_max = series.cummax()
        dd = (roll_max - series) / roll_max.replace(0, np.nan)
        return float(dd.max(skipna=True))

    def run(
        self,
        prices: pd.DataFrame,
        loan_params: Dict[str, Any],
        rebalance_freq: str = "M",
        initial_capital: float = 100000.0,
    ) -> Dict[str, Any]:
        # 1) Validate once
        ok, errs = validate_prices(prices, required_history=252, strict=False)
        if not ok:
            # continue but note errors
            pass

        # 2) Precompute
        returns = prices.pct_change().dropna()

        sig_cfg = self.config.get("signals", {})
        mom_w = int(sig_cfg.get("momentum_window", 252))
        tr_w = int(sig_cfg.get("trend_window", 200))
        mr_w = int(sig_cfg.get("meanrev_window", 20))
        wts = sig_cfg.get("weights", {"momentum": 0.5, "trend": 0.3, "meanrev": 0.2})

        opt_cfg = self.config.get("optimizer", {})
        opt = PortfolioOptimizer(
            OptimizerConfig(
                method=opt_cfg.get("method", "closed_form"),
                covariance=opt_cfg.get("covariance", "ledoit_wolf"),
                ewma_lambda=float(opt_cfg.get("ewma_lambda", 0.94)),
                risk_aversion=float(opt_cfg.get("risk_aversion", 1.0)),
                max_position=float(opt_cfg.get("max_position", 0.5)),
                min_return=float(opt_cfg.get("min_return", 0.0)),
            )
        )

        exec_cfg = self.config.get("execution", {})
        spread_bps = exec_cfg.get("spread_bps", {})
        commission = float(exec_cfg.get("commission_per_trade", 0.0))
        adv_limit = float(exec_cfg.get("adv_limit", 0.10))

        cov_cfg = self.config.get("coverage", {})
        exp_ret = float(cov_cfg.get("exp_return_assumption", 0.10))
        target_ratio = float(cov_cfg.get("target_ratio", 1.3))
        emergency_ratio = float(cov_cfg.get("emergency_ratio", 1.2))

        # 3) Setup loop
        portfolio_value = float(initial_capital)
        current_weights = pd.Series(0.0, index=prices.columns)
        nav_series: List[float] = []
        dates = prices.resample(rebalance_freq).last().index

        mpay = monthly_payment(
            float(loan_params.get("principal", 100000.0)),
            float(loan_params.get("rate", 0.08)),
            int(loan_params.get("term_months", 36)),
        )
        coverage_ok_count = 0
        total_steps = 0
        total_turnover = 0.0

        for dt in dates:
            if dt not in prices.index:
                continue
            window = prices.loc[:dt]
            if window.shape[0] < 252:
                # hold weights
                nav_series.append(portfolio_value)
                continue

            # Signals in [0,1]
            with time_block("signals"):
                mom = momentum_signal(window, window_6m=mom_w//2, window_12m=mom_w)
                tr = trend_sma200_signal(window, window=tr_w)
                mr = mean_reversion_signal(window, window=mr_w)
                combined = combine_signals({"momentum": mom, "trend": tr, "meanrev": mr}, wts)

            # Expected returns proxy: map [0,1] -> [-0.05, +0.15] annualized
            mu = (combined - 0.5) * 0.20

            # Optimize
            with time_block("optimize"):
                w, _info = opt.optimize(mu, returns.loc[:dt])

            # Risk/coverage guard simplified: enforce coverage target -> if fail, tilt defensive
            cr = compute_cr(portfolio_value, mpay, exp_ret)
            cov_ok = cr >= emergency_ratio
            if not cov_ok:
                from alphashield.utils.metrics import coverage_breach_inc
                try:
                    coverage_breach_inc()
                except Exception:
                    pass
                # shift 20% from equities to bonds
                if "VTI" in w.index and "BND" in w.index:
                    shift = min(0.2, w.get("VTI", 0.0))
                    w["VTI"] = max(0.0, w.get("VTI", 0.0) - shift)
                    w["BND"] = min(1.0, w.get("BND", 0.0) + shift)
                w = w / max(w.sum(), 1e-9)

            # Execution simulation: no ADV data, so unlimited except adv_limit ignored
            prices_row = prices.loc[dt]
            with time_block("execution"):
                exec_res = simulate_execution(
                    current_weights=current_weights,
                    target_weights=w,
                    prices=prices_row,
                    adv=None,
                    spread_bps=spread_bps,
                    commission_per_trade=commission,
                    adv_limit=adv_limit,
                    portfolio_value=portfolio_value,
                )
            new_weights = exec_res["final_weights"].reindex(prices.columns).fillna(0.0)
            turnover = float(abs(new_weights - current_weights).sum())
            total_turnover += turnover
            current_weights = new_weights

            # Mark to market to end of month using same day close (simplified)
            portfolio_value = float((current_weights * prices_row).sum())
            nav_series.append(portfolio_value)

            total_steps += 1
            if is_coverage_ok(cr, target_ratio, emergency_ratio):
                coverage_ok_count += 1

        nav = pd.Series(nav_series, index=dates[: len(nav_series)])
        rets = nav.pct_change().dropna()
        metrics = {
            "cagr": self._cagr(nav),
            "volatility": self._volatility(rets) if not rets.empty else 0.0,
            "sharpe": self._sharpe(rets) if not rets.empty else 0.0,
            "max_drawdown": self._max_dd(nav),
            "turnover": float(total_turnover / max(total_steps, 1)),
            "coverage_adherence_pct": float(coverage_ok_count / max(total_steps, 1)),
        }

        return {
            "nav": nav,
            "metrics": metrics,
        }
