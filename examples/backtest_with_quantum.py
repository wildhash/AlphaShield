"""
Example demonstrating integration of quantum optimization with backtest engine.

This shows how to extend BacktestEngine to use quantum optimization.
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from collections import Counter
from trading_core.signals.trend import trend_signals
from trading_core.signals.meanrev import meanrev_signals
from trading_core.portfolio.optimizer_qp import optimize_with_fallback, setup_quantum_environment
from trading_core.risk.guardrails import RiskLimits, enforce_caps, check_risk_limits
from finance.coverage import LoanTerms, coverage_ratio


class QuantumBacktestEngine:
    """
    Enhanced BacktestEngine with quantum optimization support.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        loan_terms: LoanTerms,
        initial_nav: float = 5000.0,
        max_position_size: float = 0.25,
        risk: RiskLimits = RiskLimits(),
        fee_bps: float = 1.0,
        spread_bps: float = 5.0,
        turnover_budget: float = 0.20,
        use_quantum: bool = False
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
        
        # Quantum optimization settings
        self.use_quantum = use_quantum
        self.quantum_available = False
        if use_quantum:
            self.quantum_available = setup_quantum_environment()

        self.nav_history: List[float] = []
        self.cr_history: List[float] = []
        self.optimization_methods: List[str] = []

    def _combine_signals(self, prices: pd.DataFrame) -> Dict[str, float]:
        tr = trend_signals(prices)
        mr = meanrev_signals(prices)
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
        mu = 0.5 * scaled.clip(-3, 3).values / np.sqrt(252)
        return mu.astype(float)

    def _cov(self, prices: pd.DataFrame) -> np.ndarray:
        rets = prices.pct_change().dropna()
        return (rets.cov().values * 252.0).astype(float)

    def step(self, t: int) -> Dict:
        """Run one rebalance at index t (use trailing window)."""
        if t < 252:
            self.nav_history.append(self.nav)
            self.cr_history.append(np.nan)
            self.optimization_methods.append("warmup")
            return {"status": "warmup"}

        window = self.data.iloc[: t + 1]
        prices = window[self.symbols]
        signals = self._combine_signals(prices)
        mu = self._forecasts(prices, signals)
        Sigma = self._cov(prices)

        # Use quantum optimization with fallback
        w_target, method = optimize_with_fallback(
            expected_returns=mu,
            covariance_matrix=Sigma,
            current_weights=self.w,
            risk_aversion=1.0,
            quantum_available=self.quantum_available
        )
        
        # Track which method was used
        self.optimization_methods.append(method)
        
        w_target = enforce_caps(w_target, self.risk)

        # Compute portfolio expected monthly return from target weights
        port_exp_ann = float(np.dot(w_target, mu))
        cr = coverage_ratio(port_exp_ann, invested_amount=self.nav, terms=self.loan_terms)

        # Simple cash buffer from limits
        cash_ratio = max(self.risk.min_cash, 1.0 - w_target.sum())
        is_ok, violations = check_risk_limits(cash_ratio, w_target, cr, self.risk)
        mode = "optimized"
        if not is_ok:
            mode = "defensive"
            w_target = 0.30 * (np.ones_like(w_target) / max(len(w_target), 1))
            cash_ratio = max(self.risk.min_cash, 1.0 - w_target.sum())

        # Rebalance costs
        turnover = np.abs(w_target - self.w).sum()
        trading_cost = self.nav * turnover * (self.fee + self.spread)

        # Next-day PnL
        day_ret_vec = self.data[self.symbols].pct_change().iloc[t].values.astype(float)
        port_ret = float(np.dot(self.w, day_ret_vec))
        self.nav = self.nav * (1.0 + port_ret) - trading_cost

        # Apply rebalance
        self.w = w_target.copy()

        self.nav_history.append(self.nav)
        self.cr_history.append(cr)

        return {
            "mode": mode,
            "method": method,
            "turnover": float(turnover),
            "trading_cost": float(trading_cost),
            "cr": float(cr),
            "nav": float(self.nav),
            "violations": violations if not is_ok else []
        }

    def run(self) -> Dict:
        """
        Run the backtest simulation.
        
        Returns:
            Dict with keys:
                - final_nav (float): Final net asset value
                - nav_series (List[float]): NAV history over time
                - cr_series (List[float]): Coverage ratio history
                - logs (List[Dict]): Detailed logs for each step
                - method_counts (Dict[str, int]): Count of optimization methods used
        """
        logs = []
        for t in range(len(self.data)):
            logs.append(self.step(t))
        
        # Count optimization methods used
        method_counts = Counter(self.optimization_methods)
        
        return {
            "final_nav": float(self.nav),
            "nav_series": self.nav_history,
            "cr_series": self.cr_history,
            "logs": logs,
            "method_counts": dict(method_counts)
        }


def main():
    """Demo: run backtest with and without quantum optimization"""
    print("=" * 70)
    print("Quantum Backtest Engine Demo")
    print("=" * 70)
    
    # Create sample price data
    print("\n1. Creating sample price data...")
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', periods=500, freq='D')
    
    # Generate correlated price series
    n_assets = 4
    returns = np.random.randn(500, n_assets) * 0.01 + 0.0005
    prices_data = {}
    for i, symbol in enumerate(['AAPL', 'GOOGL', 'MSFT', 'AMZN']):
        price_series = 100 * (1 + returns[:, i]).cumprod()
        prices_data[symbol] = price_series
    
    prices = pd.DataFrame(prices_data, index=dates)
    print(f"   Created {len(prices)} days of price data for {n_assets} assets")
    
    # Setup loan terms
    terms = LoanTerms(principal=10000, annual_rate=0.08, months=36)
    
    # Run backtest with classical optimization
    print("\n2. Running backtest with classical optimization...")
    bt_classical = QuantumBacktestEngine(
        data=prices,
        loan_terms=terms,
        initial_nav=5000.0,
        use_quantum=False
    )
    result_classical = bt_classical.run()
    
    print(f"   Final NAV: ${result_classical['final_nav']:.2f}")
    print(f"   Method counts: {result_classical['method_counts']}")
    
    # Run backtest with quantum optimization (will fallback to classical if unavailable)
    print("\n3. Running backtest with quantum optimization enabled...")
    bt_quantum = QuantumBacktestEngine(
        data=prices,
        loan_terms=terms,
        initial_nav=5000.0,
        use_quantum=True
    )
    result_quantum = bt_quantum.run()
    
    print(f"   Final NAV: ${result_quantum['final_nav']:.2f}")
    print(f"   Method counts: {result_quantum['method_counts']}")
    
    # Compare results
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    
    print(f"\nClassical Final NAV: ${result_classical['final_nav']:.2f}")
    print(f"Quantum Final NAV:   ${result_quantum['final_nav']:.2f}")
    
    pnl_diff = result_quantum['final_nav'] - result_classical['final_nav']
    print(f"\nDifference: ${pnl_diff:.2f}")
    
    if bt_quantum.quantum_available:
        print("\n✅ Quantum optimization was available and used")
    else:
        print("\nℹ️  Quantum optimization not available, both used classical")
        print("   To enable quantum:")
        print("   - pip install dwave-ocean-sdk")
        print("   - Set DWAVE_API_TOKEN environment variable")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
