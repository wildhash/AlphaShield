import numpy as np
import pandas as pd
from typing import Dict, List, Callable
from trading_core.signals.trend import trend_signals
from trading_core.signals.meanrev import meanrev_signals
from trading_core.portfolio.optimizer_qp import optimize_classical
from trading_core.risk.guardrails import RiskLimits, enforce_caps, check_risk_limits
from finance.coverage import LoanTerms, coverage_ratio

class BacktestEngine:
    """
    Minimal event-driven backtest:
    - Daily bars
    - Simple slippage/fee model
    - CR-aware portfolio selection
    """

    def __init__(
        self,
        data: pd.DataFrame,                   # price DF with columns = symbols
        loan_terms: LoanTerms,
        initial_nav: float = 5000.0,
        max_position_size: float = 0.25,
        risk: RiskLimits = RiskLimits(),
        fee_bps: float = 1.0,                 # 1bp per trade
        spread_bps: float = 5.0,              # 5bp half-spread impact
        turnover_budget: float = 0.20
    ):
        self.data = data.dropna(how="all")
        self.symbols: List[str] = list(self.data.columns)
        self.loan_terms = loan_terms
        self.nav = initial_nav
        self.w = np.zeros(len(self.symbols))
        self.max_position_size = max_position_size
        self.risk = risk
        self.fee = fee_bps / 1e4
        self.spread = spread_bps / 1e4
        self.turnover_budget = turnover_budget

        self.nav_history: List[float] = []
        self.cr_history: List[float] = []

    def _combine_signals(self, prices: pd.DataFrame) -> Dict[str, float]:
        tr = trend_signals(prices)
        mr = meanrev_signals(prices)
        # Simple vol-aware mix: more mean-rev in high vol
        rets = prices.pct_change().dropna()
        recent_vol = rets.rolling(20).std().iloc[-1].mean()
        long_vol = rets.rolling(252).std().mean().mean()
        w_tr, w_mr = (0.7, 0.3) if recent_vol <= long_vol else (0.4, 0.6)
        return {s: w_tr * tr.get(s, 0.0) + w_mr * mr.get(s, 0.0) for s in self.symbols}

    def _forecasts(self, prices: pd.DataFrame, signals: Dict[str, float]) -> np.ndarray:
        rets = prices.pct_change().dropna()
        ann_vol = (rets.std() * np.sqrt(252)).replace(0, np.nan)
        z = pd.Series(signals).reindex(self.symbols).fillna(0.0)
        scaled = (z / ann_vol).replace([np.inf, -np.inf], 0.0).fillna(0.0)
        # Clamp and convert to annualized expected return (conservative)
        mu = 0.5 * scaled.clip(-3, 3).values / np.sqrt(252)
        return mu.astype(float)

    def _cov(self, prices: pd.DataFrame) -> np.ndarray:
        rets = prices.pct_change().dropna()
        return (rets.cov().values * 252.0).astype(float)

    def step(self, t: int) -> Dict:
        """Run one rebalance at index t (use trailing window)."""
        if t < 252:  # need a year for stats
            self.nav_history.append(self.nav)
            self.cr_history.append(np.nan)
            return {"status": "warmup"}

        window = self.data.iloc[: t + 1]
        prices = window[self.symbols]
        signals = self._combine_signals(prices)
        mu = self._forecasts(prices, signals)
        Sigma = self._cov(prices)

        # Optimize target weights
        w_target = optimize_classical(
            expected_returns=mu,
            covariance_matrix=Sigma,
            current_weights=self.w,
            max_position_size=self.max_position_size,
            risk_aversion=1.0,
            turnover_budget=self.turnover_budget
        )
        w_target = enforce_caps(w_target, self.risk)

        # Compute portfolio expected monthly return from target weights
        port_exp_ann = float(np.dot(w_target, mu))
        cr = coverage_ratio(port_exp_ann, invested_amount=self.nav, terms=self.loan_terms)

        # Simple cash buffer from limits
        cash_ratio = max(self.risk.min_cash, 1.0 - w_target.sum())
        is_ok, violations = check_risk_limits(cash_ratio, w_target, cr, self.risk)
        mode = "optimized"
        if not is_ok:
            # Emergency: scale down risk
            mode = "defensive"
            w_target = 0.30 * (np.ones_like(w_target) / max(len(w_target), 1))
            cash_ratio = max(self.risk.min_cash, 1.0 - w_target.sum())

        # Rebalance costs (slippage + fees) on dollar turnover
        turnover = np.abs(w_target - self.w).sum()
        trading_cost = self.nav * turnover * (self.fee + self.spread)

        # Next-day PnL using simple close-to-close returns
        day_ret_vec = self.data[self.symbols].pct_change().iloc[t].values.astype(float)
        port_ret = float(np.dot(self.w, day_ret_vec))
        self.nav = self.nav * (1.0 + port_ret) - trading_cost

        # Apply rebalance after performance attribution for day t
        self.w = w_target.copy()

        self.nav_history.append(self.nav)
        self.cr_history.append(cr)

        return {
            "mode": mode,
            "turnover": float(turnover),
            "trading_cost": float(trading_cost),
            "cr": float(cr),
            "nav": float(self.nav),
            "violations": violations if not is_ok else []
        }

    def run(self) -> Dict:
        logs = []
        for t in range(len(self.data)):
            logs.append(self.step(t))
        return {
            "final_nav": float(self.nav),
            "nav_series": self.nav_history,
            "cr_series": self.cr_history,
            "logs": logs
        }
