import pandas as pd
from tests.trading.fixtures.synthetic_prices import make_universe_csv
from alphashield.trading.orchestrator import TradingOrchestrator
import yaml


def test_full_pipeline_step(tmp_path):
    cfg = {
        "signals": {"momentum_window": 252, "trend_window": 200, "meanrev_window": 20, "weights": {"momentum": 0.5, "trend": 0.3, "meanrev": 0.2}},
        "optimizer": {"method": "closed_form", "covariance": "ledoit_wolf", "risk_aversion": 1.0, "max_position": 0.5, "max_turnover": 0.3},
        "coverage": {"target_ratio": 1.3, "emergency_ratio": 1.2, "exp_return_assumption": 0.10},
        "execution": {"spread_bps": {"VTI":1, "BND":2, "VTIP":3}, "commission_per_trade": 0, "adv_limit": 0.10},
    }
    orch = TradingOrchestrator(cfg)
    csv_path = make_universe_csv(str(tmp_path / "sample.csv"))
    prices = pd.read_csv(csv_path, index_col="date", parse_dates=True)
    date = prices.index[260]
    window = prices.loc[:date]
    res = orch.step(date, window, {"principal":100000,"rate":0.08,"term_months":36}, portfolio_value=60000, loan_id="demo")
    assert set(["target_weights","execution_result","coverage_ratio","risk_metrics","rationale"]).issubset(res.keys())
    assert isinstance(res["rationale"], list) and len(res["rationale"]) >= 1
