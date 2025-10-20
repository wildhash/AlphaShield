import pandas as pd
import numpy as np
from typing import Dict

def meanrev_signals(prices: pd.DataFrame, window: int = 20) -> Dict[str, float]:
    """
    Bollinger-style mean reversion in [-1, 1]: negative near upper band, positive near lower band.
    """
    out: Dict[str, float] = {}
    for symbol in prices.columns:
        s = prices[symbol].dropna()
        if len(s) < window + 1:
            out[symbol] = 0.0
            continue
        sma = s.rolling(window).mean().iloc[-1]
        std = s.rolling(window).std().iloc[-1]
        px = s.iloc[-1]
        if std > 0:
            band_pos = (px - sma) / (2 * std)
            out[symbol] = float(np.clip(-band_pos, -1.0, 1.0))
        else:
            out[symbol] = 0.0
    return out
