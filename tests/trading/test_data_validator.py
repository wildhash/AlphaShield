import pandas as pd
import numpy as np
from alphashield.trading.data_validator import validate_prices, detect_outliers, check_liquidity


def test_validate_prices_flags_issues():
    # Create data with gaps >5, a negative price, and a split-like jump
    idx = pd.bdate_range("2020-01-01", periods=120)
    # introduce large gap by removing 10 business days in the middle
    idx_with_gap = idx.delete(slice(50, 60))
    prices = pd.DataFrame({"VTI": 100 + np.cumsum(np.random.default_rng(0).normal(0, 0.5, size=len(idx_with_gap)))}, index=idx_with_gap)
    prices["BND"] = 80.0
    prices.iloc[10, 0] = -5.0  # negative
    # add split-like move
    prices.iloc[20, 0] = prices.iloc[19, 0] * 1.8

    ok, errs = validate_prices(prices, required_history=200, strict=False)
    assert not ok
    assert {"gap_gt_5_bd","non_positive_price","possible_split_or_corporate_action","insufficient_history"}.issubset(set(errs))


def test_detect_outliers_methods():
    s = pd.Series([0,0,0,0,0,5,0,0,0,0], index=pd.RangeIndex(10))
    iqr = detect_outliers(s, method="iqr")
    zsc = detect_outliers(s, method="zscore")
    assert iqr.sum() >= 1
    assert zsc.sum() >= 1


def test_check_liquidity_adv_threshold():
    """
    Verify that check_liquidity returns False when average daily dollar volume is below the specified ADV threshold and True when it is above.
    
    Creates a 30-business-day price series at $10 and two volume scenarios: low volume (1,000) which should fail the adv_threshold_usd=5_000_000 check, and high volume (100,000) which should pass.
    """
    idx = pd.bdate_range("2020-01-01", periods=30)
    price = pd.Series(10.0, index=idx)
    volume_low = pd.Series(1_000, index=idx)
    assert not check_liquidity(volume_low, price, adv_threshold_usd=5_000_000)
    volume_high = pd.Series(100_000, index=idx)
    assert check_liquidity(volume_high, price, adv_threshold_usd=5_000_000)