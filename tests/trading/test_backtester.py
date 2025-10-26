import pandas as pd
import numpy as np
from tests.trading.fixtures.synthetic_prices import make_universe_csv
from alphashield.trading.backtester import Backtester


def test_backtester_metrics_shape_and_ranges(tmp_path):
    csv_path = make_universe_csv(str(tmp_path / "sample.csv"))
    prices = pd.read_csv(csv_path, index_col="date", parse_dates=True)
    # Minimal config for Backtester run
    cfg = {
        "backtesting": {
            "rebalance_freq": "M",
            "initial_capital": 60000,
            "loan_params": {"principal": 100000, "rate": 0.08, "term_months": 36},
        },
        "signals": {"momentum_window": 252, "trend_window": 200, "meanrev_window": 20, "weights": {"momentum": 0.5, "trend": 0.3, "meanrev": 0.2}},
        "optimizer": {"method": "closed_form", "covariance": "ledoit_wolf", "risk_aversion": 1.0, "max_position": 0.5, "max_turnover": 0.3},
        "coverage": {"target_ratio": 1.3, "emergency_ratio": 1.2, "exp_return_assumption": 0.10},
        "risk": {"max_drawdown": 0.15, "var_confidence": 0.95},
        "execution": {"spread_bps": {"VTI":1, "BND":2, "VTIP":3}, "commission_per_trade": 0, "adv_limit": 0.10},
    }
    bt = Backtester(cfg)
    res = bt.run(prices, cfg["backtesting"]["loan_params"], cfg["backtesting"]["rebalance_freq"], cfg["backtesting"]["initial_capital"]) 
    metrics = res["metrics"]
    for k in ["cagr","volatility","sharpe","max_drawdown","coverage_adherence_pct","turnover"]:
        assert k in metrics
        assert isinstance(metrics[k], float)
    assert 0.0 <= metrics["max_drawdown"] <= 1.0
