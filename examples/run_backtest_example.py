import os
import json
import pandas as pd
import yaml

from alphashield.trading.backtester import Backtester
from tests.trading.fixtures.synthetic_prices import make_universe_csv


def main():
    cfg = yaml.safe_load(open("config/trading.yaml")) if os.path.exists("config/trading.yaml") else {
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
    csv_path = make_universe_csv()
    prices = pd.read_csv(csv_path, index_col="date", parse_dates=True)
    bt = Backtester(cfg)
    res = bt.run(prices, cfg["backtesting"]["loan_params"], cfg["backtesting"]["rebalance_freq"], cfg["backtesting"]["initial_capital"]) 
    print("=== AlphaShield Backtest Results ===")
    print(json.dumps(res["metrics"], indent=2))


if __name__ == "__main__":
    main()
