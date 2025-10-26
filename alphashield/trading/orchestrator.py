from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from alphashield.utils.logging_config import get_logger
from alphashield.utils.metrics import time_block, decisions_inc
from alphashield.trading.coverage_monitor import monthly_payment, coverage_ratio as compute_cr, is_coverage_ok
from alphashield.trading.portfolio_optimizer import PortfolioOptimizer, OptimizerConfig
from alphashield.trading.signal_generator import momentum_signal, trend_sma200_signal, mean_reversion_signal, combine_signals
from alphashield.trading.execution_simulator import simulate_execution


class TradingOrchestrator:
    """
    One-step decision orchestrator for AlphaShield.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the TradingOrchestrator with the provided configuration, set up logging, and construct the portfolio optimizer.
        
        Parameters:
            config (Dict[str, Any]): Configuration dictionary used to configure the orchestrator. Expected keys include an optional "optimizer" mapping that may contain:
                - method: optimization method (default "closed_form")
                - covariance: covariance estimator (default "ledoit_wolf")
                - ewma_lambda: EWMA lambda as a float (default 0.94)
                - risk_aversion: risk aversion coefficient as a float (default 1.0)
                - max_position: maximum position size as a float (default 0.5)
                - min_return: minimum expected return as a float (default 0.0)
        
        Attributes set:
            config: The provided configuration dictionary.
            logger: Logger named "alphashield.trading".
            optimizer: PortfolioOptimizer instance configured from `config["optimizer"]` or sensible defaults.
            current_weights: Initialized to None and used to track the latest executed portfolio weights.
        """
        self.config = config
        self.logger = get_logger("alphashield.trading")
        opt_cfg = self.config.get("optimizer", {})
        self.optimizer = PortfolioOptimizer(
            OptimizerConfig(
                method=opt_cfg.get("method", "closed_form"),
                covariance=opt_cfg.get("covariance", "ledoit_wolf"),
                ewma_lambda=float(opt_cfg.get("ewma_lambda", 0.94)),
                risk_aversion=float(opt_cfg.get("risk_aversion", 1.0)),
                max_position=float(opt_cfg.get("max_position", 0.5)),
                min_return=float(opt_cfg.get("min_return", 0.0)),
            )
        )
        self.current_weights: Optional[pd.Series] = None

    def step(
        self,
        date: pd.Timestamp,
        prices_window: pd.DataFrame,
        loan_params: Dict[str, Any],
        portfolio_value: float,
        loan_id: str = "demo",
    ) -> Dict[str, Any]:
        # Signals
        """
        Run a single trading decision step: compute signals, optimize portfolio weights, simulate execution, and assess coverage and risk.
        
        Parameters:
            date (pd.Timestamp): Evaluation timestamp for the decision.
            prices_window (pd.DataFrame): Historical price matrix with assets as columns and time increasing by row; used for signal calculation and execution pricing.
            loan_params (Dict[str, Any]): Loan details required for coverage calculations (expects keys like "principal", "rate", "term_months").
            portfolio_value (float): Current total portfolio market value used for sizing and execution.
            loan_id (str): Identifier for the loan/context used in logging.
        
        Returns:
            Dict[str, Any]: A dictionary with the following keys:
                - "target_weights" (pd.Series): Optimizer-produced target portfolio weights indexed by asset.
                - "execution_result" (Dict[str, Any]): Full result from simulate_execution (includes "final_weights", "final_value", "total_cost", etc.).
                - "coverage_ratio" (float): Coverage ratio computed from portfolio_value, loan payment, and expected return assumption.
                - "risk_metrics" (Dict[str, float]): Risk metrics including "realized_vol" (annualized) and "turnover".
                - "rationale" (List[str]): Short textual reasons for the decision (template name, realized volatility, coverage ratio).
                - "final_value" (float): Portfolio value after simulated execution (falls back to input portfolio_value if execution result missing).
        """
        sig_cfg = self.config.get("signals", {})
        mom_w = int(sig_cfg.get("momentum_window", 252))
        tr_w = int(sig_cfg.get("trend_window", 200))
        mr_w = int(sig_cfg.get("meanrev_window", 20))
        weights_cfg = sig_cfg.get("weights", {"momentum": 0.5, "trend": 0.3, "meanrev": 0.2})

        with time_block("signals"):
            mom = momentum_signal(prices_window, window_6m=mom_w // 2, window_12m=mom_w)
            tr = trend_sma200_signal(prices_window, window=tr_w)
            mr = mean_reversion_signal(prices_window, window=mr_w)
            combined = combine_signals({"momentum": mom, "trend": tr, "meanrev": mr}, weights_cfg)

        mu = (combined - 0.5) * 0.20
        returns = prices_window.pct_change().dropna()

        # Template selection heuristic: defensive if realized vol high
        realized_vol = float(returns.std().mean() * np.sqrt(252)) if not returns.empty else 0.0
        template_name = "risk_off" if realized_vol > 0.20 else "balanced"

        with time_block("optimize"):
            target_weights, _ = self.optimizer.optimize(mu, returns)

        # Coverage
        cov_cfg = self.config.get("coverage", {})
        exp_ret = float(cov_cfg.get("exp_return_assumption", 0.10))
        target_ratio = float(cov_cfg.get("target_ratio", 1.3))
        emergency_ratio = float(cov_cfg.get("emergency_ratio", 1.2))
        mpay = monthly_payment(float(loan_params.get("principal", 100000.0)), float(loan_params.get("rate", 0.08)), int(loan_params.get("term_months", 36)))
        cr = compute_cr(portfolio_value, mpay, exp_ret)
        coverage_ok = is_coverage_ok(cr, target_ratio, emergency_ratio)

        # Execution
        exec_cfg = self.config.get("execution", {})
        spread_bps = exec_cfg.get("spread_bps", {})
        commission = float(exec_cfg.get("commission_per_trade", 0.0))
        adv_limit = float(exec_cfg.get("adv_limit", 0.10))
        prices_row = prices_window.iloc[-1]
        current_weights = self.current_weights or pd.Series(0.0, index=prices_window.columns)

        with time_block("execution"):
            execution = simulate_execution(
                current_weights=current_weights,
                target_weights=target_weights,
                prices=prices_row,
                adv=None,
                spread_bps=spread_bps,
                commission_per_trade=commission,
                adv_limit=adv_limit,
                portfolio_value=float(portfolio_value),
            )
        self.current_weights = execution["final_weights"].reindex(prices_window.columns).fillna(0.0)
        final_value = float(execution["final_value"]) if isinstance(execution.get("final_value"), (float, int)) else float(portfolio_value)

        risk_metrics = {
            "realized_vol": realized_vol,
            "turnover": float(abs(self.current_weights - current_weights).sum()),
        }

        rationale: List[str] = []
        rationale.append(f"template={template_name}")
        rationale.append(f"realized_vol={realized_vol:.2f}")
        rationale.append(f"coverage_ratio={cr:.2f}")

        log = {
            "event": "trading_decision",
            "date": str(date),
            "loan_id": loan_id,
            "coverage_ratio": float(cr),
            "template": template_name,
            "weights": {k: float(v) for k, v in target_weights.to_dict().items()},
            "costs": float(execution.get("total_cost", 0.0)),
            "metrics": risk_metrics,
        }
        try:
            self.logger.info(json.dumps(log))
            decisions_inc(template_name)
        except Exception:
            pass

        return {
            "target_weights": target_weights,
            "execution_result": execution,
            "coverage_ratio": float(cr),
            "risk_metrics": risk_metrics,
            "rationale": rationale,
            "final_value": final_value,
        }