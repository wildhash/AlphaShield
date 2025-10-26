import numpy as np
import pandas as pd


def gbm_prices(start_price: float, mu: float, sigma: float, days: int, seed: int = 7) -> pd.Series:
    rng = np.random.default_rng(seed)
    dt = 1 / 252
    shocks = rng.normal((mu - 0.5 * sigma**2) * dt, sigma * np.sqrt(dt), size=days)
    px = start_price * np.exp(np.cumsum(shocks))
    idx = pd.bdate_range("2018-01-01", periods=days)
    return pd.Series(px, index=idx)


def make_universe_csv(path: str = "tests/trading/fixtures/sample_data.csv"):
    vti = gbm_prices(200, 0.10, 0.18, 252 * 5, seed=1)
    bnd = gbm_prices(80, 0.04, 0.06, 252 * 5, seed=2)
    vtip = gbm_prices(50, 0.015, 0.02, 252 * 5, seed=3)
    df = pd.concat([vti, bnd, vtip], axis=1)
    df.columns = ["VTI", "BND", "VTIP"]
    df.to_csv(path, index_label="date")
    return path
