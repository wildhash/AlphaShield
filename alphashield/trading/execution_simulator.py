from __future__ import annotations

from typing import Dict, Tuple
import pandas as pd
import numpy as np


def simulate_execution(
    current_weights: pd.Series,
    target_weights: pd.Series,
    prices: pd.Series,
    adv: pd.Series | None = None,
    spread_bps: dict[str, float] | None = None,
    commission_per_trade: float = 0.0,
    adv_limit: float = 0.10,
    portfolio_value: float = 0.0,
) -> dict:
    """
    Simulates execution of trades to move from current to target weights while accounting for spread slippage, per-trade commissions, and optional ADV-based trade caps.
    
    Parameters:
        current_weights (pd.Series): Current portfolio weights aligned by asset index.
        target_weights (pd.Series): Desired portfolio weights; assets not in current_weights are treated as zero.
        prices (pd.Series): Asset prices by asset key; assets with missing or non-positive prices are skipped.
        adv (pd.Series | None): Average daily volume per asset used to cap trade notional when provided.
        spread_bps (dict[str, float] | None): Per-asset spread in basis points; defaults to 1.0 bps for missing entries.
        commission_per_trade (float): Flat commission charged once for each asset with non-zero executed notional.
        adv_limit (float): Fraction of ADV used as a cap for the absolute trade notional (e.g., 0.10 = 10% of ADV).
        portfolio_value (float): Starting total portfolio notional value used to compute desired trade notionals.
    
    Returns:
        dict: {
            "trades": dict of asset -> executed notional (signed, positive means buy notional, negative means sell),
            "total_cost": float total of slippage plus commissions deducted from portfolio value,
            "final_weights": pd.Series of resulting weights clipped to [0,1] and renormalized to sum to 1 if non-zero,
            "final_value": float portfolio value after subtracting total slippage and commissions
        }
    """
    idx = target_weights.index
    cw = current_weights.reindex(idx).fillna(0.0)
    tw = target_weights.reindex(idx).fillna(0.0)
    delta_w = tw - cw

    if spread_bps is None:
        spread_bps = {t: 1.0 for t in idx}

    traded_value = {}
    total_cost = 0.0
    new_weights = cw.copy()
    total_value = float(portfolio_value)

    for t in idx:
        desired_notional = float(delta_w[t]) * total_value
        if desired_notional == 0.0:
            continue
        price = float(prices.get(t, np.nan))
        if not np.isfinite(price) or price <= 0:
            continue
        max_trade = abs(desired_notional)
        if adv is not None and t in adv.index:
            max_trade = min(max_trade, float(adv[t]) * adv_limit)
        executed = np.sign(desired_notional) * max_trade
        # apply slippage cost
        hsp = float(spread_bps.get(t, 1.0)) * 1e-4 / 2.0
        slippage = abs(executed) * hsp
        commission = commission_per_trade if abs(executed) > 0 else 0.0
        total_cost += slippage + commission

        traded_value[t] = executed
        # update weight approximation
        total_value_after = total_value - slippage - commission
        new_notional = float(cw[t]) * total_value_after + executed
        total_value = total_value_after
        new_weights[t] = new_notional / max(total_value, 1e-9)

    final_weights = new_weights.clip(0.0, 1.0)
    # renormalize to sum to 1
    if final_weights.sum() > 0:
        final_weights = final_weights / final_weights.sum()

    return {
        "trades": traded_value,
        "total_cost": float(total_cost),
        "final_weights": final_weights,
        "final_value": float(total_value),
    }