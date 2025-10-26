from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Literal


class MomentumSignal:
    """
    Exploits intermediate-term persistence in asset returns.

    Logic:
    - Calculate 3-month, 6-month, 12-month returns
    - Rank assets by momentum score
    - Long top 30%, short/avoid bottom 30%
    - Rebalance monthly
    """

    def generate_signal(self, prices: pd.DataFrame) -> pd.Series:
        """
        Compute momentum signal for the latest available date.

        Args:
            prices: DataFrame of prices indexed by date, columns are asset tickers.

        Returns:
            pd.Series of signal strengths in [-1, 1] for each asset (latest row).
        """
        if prices.shape[0] < 252:
            # Require at least ~1 year of data for stable momentum computation
            return pd.Series(0.0, index=prices.columns)

        returns_3m = prices.pct_change(63)
        returns_6m = prices.pct_change(126)
        returns_12m = prices.pct_change(252)

        momentum_score = (
            0.5 * returns_3m + 0.3 * returns_6m + 0.2 * returns_12m
        )

        latest_scores = momentum_score.iloc[-1].replace([np.inf, -np.inf], np.nan).fillna(0.0)

        # Normalize to [-1, 1]
        ranks = latest_scores.rank(pct=True)
        signals = ranks * 2.0 - 1.0
        signals = signals.clip(-1.0, 1.0)
        return signals


class MeanReversionSignal:
    """
    Exploits short-term overreactions.

    Logic:
    - Calculate Z-score vs. 20-day moving average
    - Identify extreme deviations (>2 std devs)
    - Fade extremes (buy oversold, sell overbought)
    - Rebalance weekly
    """

    def generate_signal(self, prices: pd.DataFrame) -> pd.Series:
        """
        Compute mean-reversion signal for the latest available date.

        Args:
            prices: DataFrame of prices indexed by date, columns are asset tickers.

        Returns:
            pd.Series of signal strengths in [-1, 1] for each asset (latest row).
        """
        if prices.shape[0] < 20:
            return pd.Series(0.0, index=prices.columns)

        ma_20 = prices.rolling(20).mean()
        std_20 = prices.rolling(20).std().replace(0.0, np.nan)
        z_score = (prices - ma_20) / std_20

        latest_z = z_score.iloc[-1].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        signals = -latest_z.clip(-2.0, 2.0) / 2.0
        signals = signals.clip(-1.0, 1.0)
        return signals


class TrendFollowingSignal:
    """
    Captures long-term directional moves.

    Logic:
    - Dual moving average crossover (50/200 day)
    - Volatility scaling for trend strength (simplified ADX proxy)
    - Position size scales with trend confidence
    """

    def generate_signal(self, prices: pd.DataFrame) -> pd.Series:
        """
        Compute trend-following signal for the latest available date.

        Args:
            prices: DataFrame of prices indexed by date, columns are asset tickers.

        Returns:
            pd.Series of signal strengths in [-1, 1] for each asset (latest row).
        """
        if prices.shape[0] < 200:
            return pd.Series(0.0, index=prices.columns)

        ma_50 = prices.rolling(50).mean()
        ma_200 = prices.rolling(200).mean()

        crossover = (ma_50.iloc[-1] > ma_200.iloc[-1]).astype(float) * 2.0 - 1.0

        daily_vol = prices.pct_change().rolling(14).std()
        denom = daily_vol.iloc[-1].replace(0.0, np.nan)
        trend_strength = (ma_50.iloc[-1] - ma_200.iloc[-1]).abs() / denom
        trend_strength = trend_strength.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        trend_strength = trend_strength.clip(0.0, 1.0)

        signal = crossover * trend_strength
        signal = signal.clip(-1.0, 1.0)
        return signal


class VolatilitySignal:
    """
    Exploits mean reversion in volatility using VIX-like series.

    Logic:
    - Compare current VIX with its 50-day average
    - Risk-on if vol below average; risk-off if above
    """

    def generate_signal(self, vix_data: pd.Series) -> float:
        """
        Compute risk-on/risk-off signal in [-1, 1].

        Args:
            vix_data: Series of VIX levels indexed by date.

        Returns:
            float in [-1, 1], where -1 is defensive, +1 is aggressive.
        """
        if vix_data.shape[0] < 50:
            return 0.0

        current_vix = float(vix_data.iloc[-1])
        vix_ma = float(vix_data.rolling(50).mean().iloc[-1])
        if vix_ma == 0:
            return 0.0

        signal = (vix_ma - current_vix) / vix_ma
        return float(np.clip(signal, -1.0, 1.0))


Regime = Literal["low_vol", "balanced", "high_vol"]


class SignalAggregator:
    """Combines signals based on market regime and volatility overlay."""

    def __init__(self) -> None:
        self.strategies = {
            "momentum": MomentumSignal(),
            "mean_reversion": MeanReversionSignal(),
            "trend_following": TrendFollowingSignal(),
            "volatility": VolatilitySignal(),
        }

    def aggregate_signals(
        self,
        prices: pd.DataFrame,
        vix: pd.Series,
        regime: Regime = "balanced",
    ) -> pd.Series:
        """
        Combine strategy signals using regime-specific weights and apply a volatility overlay.
        
        Parameters:
            prices (pd.DataFrame): Price history with datetime index and asset columns used to generate component signals.
            vix (pd.Series): VIX-like series passed to the volatility strategy to compute a volatility overlay.
            regime (Regime): One of "low_vol", "balanced", or "high_vol". If an invalid value is provided, "balanced" is used.
        
        Returns:
            pd.Series: Aggregated signal for each asset (indexed by asset name) with values clipped to the range [-1.0, 1.0]. If the volatility strategy's signal is less than -0.5, the aggregated signal is scaled by 0.5 before clipping.
        """
        weights: Dict[str, Dict[str, float]] = {
            "low_vol": {"momentum": 0.6, "trend_following": 0.2, "mean_reversion": 0.2},
            "balanced": {"momentum": 0.4, "trend_following": 0.3, "mean_reversion": 0.3},
            "high_vol": {"momentum": 0.2, "trend_following": 0.2, "mean_reversion": 0.6},
        }
        if regime not in weights:
            regime = "balanced"

        momentum = self.strategies["momentum"].generate_signal(prices)
        mean_rev = self.strategies["mean_reversion"].generate_signal(prices)
        trend = self.strategies["trend_following"].generate_signal(prices)

        components: Dict[str, pd.Series] = {
            "momentum": momentum,
            "mean_reversion": mean_rev,
            "trend_following": trend,
        }

        # Start with zeros for safe addition
        final_signal = pd.Series(0.0, index=prices.columns)
        for strategy_name, weight in weights[regime].items():
            final_signal = final_signal.add(components[strategy_name] * weight, fill_value=0.0)

        vol_signal = self.strategies["volatility"].generate_signal(vix)
        if vol_signal < -0.5:
            final_signal *= 0.5

        return final_signal.clip(-1.0, 1.0)


# === Light-weight API for Phase 1 tests ===
import pandas as _pd
import numpy as _np


def momentum_signal(prices: _pd.DataFrame, window_6m: int = 126, window_12m: int = 252) -> _pd.Series:
    """
    Compute rank-percentile momentum scores from 6- and 12-month returns.
    
    Parameters:
        prices (_pd.DataFrame): Historical price series with rows ordered by time and columns as asset identifiers.
        window_6m (int): Lookback window (in rows) used to compute the 6-month percentage change.
        window_12m (int): Lookback window (in rows) used to compute the 12-month percentage change.
    
    Returns:
        _pd.Series: Rank-percentile scores in the range [0, 1] for each asset, where larger values indicate stronger recent momentum.
        If the input has fewer rows than max(window_6m, window_12m), returns 0.5 for every asset.
    """
    if prices.shape[0] < max(window_6m, window_12m):
        return _pd.Series(0.5, index=prices.columns)
    r6 = prices.pct_change(window_6m).iloc[-1]
    r12 = prices.pct_change(window_12m).iloc[-1]
    score = 0.6 * r6 + 0.4 * r12
    ranks = score.rank(pct=True).fillna(0.5)
    return ranks.clip(0.0, 1.0)


def trend_sma200_signal(prices: _pd.DataFrame, window: int = 200) -> _pd.Series:
    """
    Return a per-asset binary signal indicating whether the latest price is above its simple moving average over the given window.
    
    Parameters:
        prices (_pd.DataFrame): Price history with rows as time-ordered observations and columns as asset identifiers.
        window (int): Lookback period for the simple moving average (default 200).
    
    Returns:
        _pd.Series: Series indexed by asset (columns of `prices`) with values in [0, 1]:
            - `1.0` if the latest price is above the window-period SMA,
            - `0.0` if the latest price is at or below the SMA,
            - `0.5` for all assets if `prices` has fewer than `window` rows.
    """
    if prices.shape[0] < window:
        return _pd.Series(0.5, index=prices.columns)
    sma = prices.rolling(window).mean().iloc[-1]
    last = prices.iloc[-1]
    return (last > sma).astype(float)


def mean_reversion_signal(prices: _pd.DataFrame, window: int = 20) -> _pd.Series:
    """
    Compute a mean-reversion score per asset where higher values indicate the asset is more oversold.
    
    Calculates the inverted z-score of the latest prices versus a rolling mean and standard deviation over `window` periods, then clips the inverted z to the range [-2, 2] and scales it to [0, 1] where 0 corresponds to strongly overbought and 1 corresponds to strongly oversold. If there are fewer than `window` rows in `prices`, returns 0.5 for every asset.
    
    Parameters:
        prices (_pd.DataFrame): Historical price series with rows indexed by time and columns by asset.
        window (int): Lookback window length (in rows) used to compute the rolling mean and standard deviation.
    
    Returns:
        _pd.Series: Per-asset scores in [0, 1], where larger values indicate stronger mean-reversion buy signals.
    """
    if prices.shape[0] < window:
        return _pd.Series(0.5, index=prices.columns)
    ma = prices.rolling(window).mean().iloc[-1]
    std = prices.rolling(window).std().iloc[-1].replace(0.0, _np.nan)
    z = (prices.iloc[-1] - ma) / std
    inv = -z.replace([_np.inf, -_np.inf], _np.nan).fillna(0.0)
    # scale inv z to [0,1] by clipping at +/-2 and mapping [-2,2] -> [0,1]
    clipped = inv.clip(-2.0, 2.0)
    return (clipped + 2.0) / 4.0


def combine_signals(components: dict, weights: dict | None = None) -> _pd.Series:
    """
    Combine multiple normalized component signals into a single weighted signal in the range [0, 1].
    
    Each input Series is reindexed to a common index (taken from the first component), missing values are filled with 0.5, and inputs are clipped to [0, 1]. If weights is None, components receive equal weight; weights provided for missing component keys are treated as zero. The combined value is the weighted sum normalized by the sum of weights and then clipped to [0, 1].
    
    Parameters:
        components (dict): Mapping from component name to pandas Series of signals (values expected in [0, 1]).
        weights (dict | None): Optional mapping from component name to non-negative weight. If None, equal weights are used.
    
    Returns:
        pandas.Series: Combined signal indexed by the common index, with values clipped to [0, 1].
    
    Raises:
        ValueError: If `components` is empty or if the sum of resolved weights is not greater than zero.
    """
    if not components:
        raise ValueError("components must be non-empty")
    idx = next(iter(components.values())).index
    total = _pd.Series(0.0, index=idx)
    if weights is None:
        weights = {k: 1.0 / len(components) for k in components}
    wsum = sum(float(weights.get(k, 0.0)) for k in components)
    if wsum <= 0:
        raise ValueError("sum of weights must be positive")
    for name, series in components.items():
        w = float(weights.get(name, 0.0))
        s = series.reindex(idx).fillna(0.5).clip(0.0, 1.0)
        total = total.add(w * s, fill_value=0.0)
    total = total / wsum
    return total.clip(0.0, 1.0)