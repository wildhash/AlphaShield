import pandas as pd
import numpy as np
from typing import Dict

def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def trend_signals(prices: pd.DataFrame) -> Dict[str, float]:
    """
    Multi-timeframe EMA trend strength in [-1, 1], scaled by 10 then clipped.
    """
    out: Dict[str, float] = {}
    for symbol in prices.columns:
        s = prices[symbol].dropna()
        if s.empty:
            out[symbol] = 0.0
            continue
        e20, e60, e200 = ema(s, 20).iloc[-1], ema(s, 60).iloc[-1], ema(s, 200).iloc[-1]
        px = s.iloc[-1]
        short = (px - e20) / (e20 + 1e-12)
        med   = (e20 - e60) / (e60 + 1e-12)
        long  = (e60 - e200) / (e200 + 1e-12)
        score = 0.5 * short + 0.3 * med + 0.2 * long
        out[symbol] = float(np.clip(10.0 * score, -1.0, 1.0))
    return out
