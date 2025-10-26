from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd


@dataclass
class MarketData:
    prices: pd.DataFrame
    returns: pd.DataFrame
    vix: pd.Series


class DataProvider:
    """Simple data provider abstraction.

    In production, connect to real-time feeds (e.g., Polygon, IEX, Alpaca).
    For now, provides synthetic or stubbed data.
    """

    def __init__(self) -> None:
        self._rng = np.random.default_rng(123)

    def get_historical_prices(self, tickers: List[str], start: str, end: str) -> pd.DataFrame:
        dates = pd.bdate_range(start=start, end=end, freq="C")
        n = len(dates)
        m = len(tickers)
        # Geometric Brownian Motion synthetic prices
        mu = 0.08 / 252
        sigma = 0.15 / np.sqrt(252)
        shocks = self._rng.normal(mu, sigma, size=(n, m))
        prices = 100 * np.exp(np.cumsum(shocks, axis=0))
        return pd.DataFrame(prices, index=dates, columns=tickers)

    def get_vix_series(self, start: str, end: str) -> pd.Series:
        dates = pd.bdate_range(start=start, end=end, freq="C")
        # Mean-reverting synthetic vol index
        vix = 20 + np.cumsum(self._rng.normal(0, 0.2, size=len(dates)))
        vix = np.clip(vix, 10, 60)
        return pd.Series(vix, index=dates, name="VIX")

    def get_market_data(self, tickers: List[str], start: str, end: str) -> MarketData:
        prices = self.get_historical_prices(tickers, start, end)
        returns = prices.pct_change().dropna()
        vix = self.get_vix_series(start, end).reindex(prices.index).ffill()
        return MarketData(prices=prices, returns=returns, vix=vix)
