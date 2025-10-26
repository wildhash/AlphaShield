from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd

from alphashield.utils.errors import DataValidationError


def _is_business_day_index(index: pd.Index) -> bool:
    """
    Determine whether the given pandas index represents business-day data.
    
    Returns `True` if `index` is a DatetimeIndex or PeriodIndex with a business frequency code ('B' or 'C'), or if all dates in the index fall on weekdays (Monday–Friday); returns `False` otherwise.
    
    Returns:
        bool: `True` if the index represents business days, `False` otherwise.
    """
    if not isinstance(index, (pd.DatetimeIndex, pd.PeriodIndex)):
        return False
    # Consider business day index if frequency is business day or dates are weekdays
    if getattr(index, "freqstr", None) in {"B", "C"}:
        return True
    return bool(pd.Index(index).to_series().dt.dayofweek.le(4).all())


def validate_prices(
    df: pd.DataFrame,
    required_history: int = 252,
    strict: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Validate an OHLC/close price DataFrame against business-day, continuity, positivity, volatility, and history-length rules.
    
    Parameters:
        df (pd.DataFrame): Price data indexed by dates (OHLC or close columns).
        required_history (int): Minimum number of rows required in `df`. Default is 252.
        strict (bool): If True, raise DataValidationError when any validation fails; otherwise return error codes.
    
    Returns:
        tuple: (ok, errors) where `ok` is `True` if all validations pass, `False` otherwise; `errors` is a list of error code strings describing detected issues.
    
    Raises:
        DataValidationError: If `strict` is True and one or more validations fail.
    """
    errors: List[str] = []

    if df is None or df.empty:
        errors.append("empty_prices")
        if strict:
            raise DataValidationError("Price DataFrame is empty")
        return False, errors

    if not _is_business_day_index(df.index):
        errors.append("non_business_day_index")

    # Check history length
    if len(df.index) < required_history:
        errors.append("insufficient_history")

    # Identify gaps: reindex to full business day range and count consecutive NaNs
    full_index = pd.bdate_range(df.index.min(), df.index.max())
    reindexed = df.reindex(full_index)
    # Forward fill small gaps to avoid cascading NaNs
    ffilled = reindexed.ffill()
    # Any stretch of NaNs longer than 5 indicates a gap
    is_nan = reindexed.isna().all(axis=1)
    if is_nan.any():
        # compute longest consecutive run
        groups = (is_nan != is_nan.shift()).cumsum()
        max_run = int(is_nan.groupby(groups).transform("sum").where(is_nan).max() or 0)
        if max_run > 5:
            errors.append("gap_gt_5_bd")
    # Non-positive prices
    if (df <= 0).any().any():
        errors.append("non_positive_price")

    # Large daily moves (possible split)
    returns = df.pct_change().replace([np.inf, -np.inf], np.nan)
    if (returns.abs() > 0.5).any().any():
        errors.append("possible_split_or_corporate_action")

    ok = len(errors) == 0
    if strict and not ok:
        raise DataValidationError(
            f"Validation failed: {', '.join(errors)}"
        )
    return ok, errors


def detect_outliers(returns: pd.Series, method: str = "iqr") -> pd.Series:
    """
    Identify outliers in a series of returns using IQR or z-score methods.
    
    Parameters:
        returns (pd.Series): Series of numeric returns; NaN values are ignored for calculations but preserved in the returned index alignment.
        method (str): Outlier detection method: "iqr" to flag values outside Q1 - 1.5*IQR and Q3 + 1.5*IQR, or "zscore" to flag values with absolute z-score greater than 3. Default is "iqr".
    
    Returns:
        pd.Series: Boolean mask aligned to the input index where `True` indicates an outlier and `False` otherwise. Empty input yields an empty boolean Series.
    
    Raises:
        ValueError: If `method` is not "iqr" or "zscore".
    """
    x = pd.Series(returns).dropna()
    if x.empty:
        return pd.Series([], dtype=bool)
    if method == "iqr":
        q1, q3 = x.quantile(0.25), x.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (x < lower) | (x > upper)
        return mask.reindex(returns.index, fill_value=False)
    elif method == "zscore":
        mu, sigma = x.mean(), x.std(ddof=0)
        if sigma == 0:
            mask = pd.Series(False, index=x.index)
        else:
            z = (x - mu) / sigma
            mask = z.abs() > 3.0
        return mask.reindex(returns.index, fill_value=False)
    else:
        raise ValueError("method must be 'iqr' or 'zscore'")


def check_liquidity(
    volume: pd.Series,
    price: pd.Series,
    adv_threshold_usd: float = 5_000_000,
) -> bool:
    """
    Determine whether the average daily dollar volume (ADV) meets or exceeds a USD threshold.
    
    Parameters:
        volume (pd.Series): Daily traded volume (units) indexed by date or reindexable to `price.index`.
        price (pd.Series): Daily price series indexed by date; used to compute dollar volume per day.
        adv_threshold_usd (float): Minimum average daily dollar volume in USD required to pass.
    
    Returns:
        bool: `True` if the mean of (volume * price) is greater than or equal to `adv_threshold_usd`, `False` otherwise.
    """
    v = pd.Series(volume).astype(float).reindex(price.index).fillna(0.0)
    p = pd.Series(price).astype(float)
    adv_usd = float((v * p).mean())
    return adv_usd >= adv_threshold_usd