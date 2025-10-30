import pandas as pd
import numpy as np
from tests.trading.fixtures.synthetic_prices import gbm_prices
from alphashield.trading.signal_generator import momentum_signal, trend_sma200_signal, mean_reversion_signal, combine_signals


def test_momentum_and_trend_rank_uptrend_highest():
    # Create an uptrend for VTI, flat for BND, slight down for VTIP
    idx = pd.bdate_range("2020-01-01", periods=252*2)
    vti = pd.Series(np.linspace(100, 160, len(idx)), index=idx)
    bnd = pd.Series(np.linspace(80, 82, len(idx)), index=idx)
    vtip = pd.Series(np.linspace(60, 58, len(idx)), index=idx)
    prices = pd.concat([vti, bnd, vtip], axis=1)
    prices.columns = ["VTI","BND","VTIP"]

    mom = momentum_signal(prices)
    tr = trend_sma200_signal(prices)

    # VTI should be highest
    assert mom["VTI"] >= mom[["BND","VTIP"]].max() - 1e-12
    assert tr["VTI"] >= tr[["BND","VTIP"]].max() - 1e-12


def test_mean_reversion_buy_dips_behavior():
    # Construct a recent dip in VTI relative to 20d mean
    idx = pd.bdate_range("2020-01-01", periods=60)
    base = pd.Series(100 + np.sin(np.linspace(0, 6, len(idx))) * 2, index=idx)
    vti = base.copy()
    vti.iloc[-1] = vti.iloc[-1] - 4.0  # dip
    bnd = base * 0 + 80
    vtip = base * 0 + 60
    prices = pd.concat([vti, bnd, vtip], axis=1)
    prices.columns = ["VTI","BND","VTIP"]

    mr = mean_reversion_signal(prices)
    assert mr["VTI"] > 0.5  # buy the dip produces > neutral


def test_combine_signals_weighting_and_bounds():
    idx = pd.bdate_range("2020-01-01", periods=252)
    prices = pd.DataFrame({"VTI": np.linspace(100, 150, len(idx)), "BND": np.linspace(80, 81, len(idx)), "VTIP": np.linspace(60, 61, len(idx))}, index=idx)
    mom = momentum_signal(prices)
    tr = trend_sma200_signal(prices)
    mr = mean_reversion_signal(prices)
    combo = combine_signals({"momentum": mom, "trend": tr, "meanrev": mr}, weights={"momentum":0.5,"trend":0.3,"meanrev":0.2})
    assert (combo>=0.0).all() and (combo<=1.0).all()
