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
    Simple execution simulator with spread slippage and ADV caps.
    - Limit trade notional to adv_limit * ADV
    - Slippage: half-spread per trade leg
    - Commission: flat per name traded (if any trade occurs)
    Returns dict with trades, total_cost, final_weights, final_value
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
