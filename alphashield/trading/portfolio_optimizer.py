from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd
try:
    from sklearn.covariance import LedoitWolf  # type: ignore
except Exception:
    LedoitWolf = None  # type: ignore

from alphashield.utils.errors import OptimizationError


@dataclass
class OptimizerConfig:
    method: str = "closed_form"           # or "cvxpy"
    covariance: str = "ledoit_wolf"       # or "ewma"
    ewma_lambda: float = 0.94
    risk_aversion: float = 1.0
    max_position: float = 0.5
    min_return: float = 0.0


def _project_to_simplex_box(w: np.ndarray, max_pos: float) -> np.ndarray:
    """
    Project a weight vector onto the probability simplex with per-asset upper bounds.
    
    Parameters:
        w (np.ndarray): 1-D array of asset weights (can be any real values).
        max_pos (float): Maximum allowed weight for any single asset (0 < max_pos <= 1).
    
    Returns:
        np.ndarray: A 1-D array of the same length as `w` where each element is between 0 and `max_pos`
        and the elements sum to 1. If all weights clip to zero, returns an equal-weight vector with
        each element equal to min(1/n, max_pos).
    """
    w = np.clip(w, 0.0, max_pos)
    s = w.sum()
    if s <= 0:
        # fallback: equal weight within box
        n = w.shape[0]
        return np.full(n, min(1.0 / n, max_pos))
    return w / s


def _estimate_covariance(returns: pd.DataFrame, method: str, ewma_lambda: float) -> np.ndarray:
    """
    Estimate the assets' covariance matrix from historical returns using the selected method.
    
    Parameters:
        returns (pd.DataFrame): Historical asset returns with rows as observations (time) and columns as assets.
        method (str): Covariance estimation method — either "ledoit_wolf" or "ewma".
        ewma_lambda (float): Decay factor used when method is "ewma" (ignored for other methods).
    
    Returns:
        np.ndarray: Estimated covariance matrix (shape: n_assets x n_assets).
    
    Notes:
        - If fewer than two observations are present, returns a diagonal covariance matrix using per-asset variances (with small-value safeguards).
        - For "ledoit_wolf", falls back to the sample covariance if the LedoitWolf estimator is unavailable.
        - For "ewma", computes an exponentially weighted covariance using the provided decay factor.
        - Raises ValueError if an unknown method string is passed.
    """
    x = returns.dropna()
    if x.shape[0] < 2:
        # tiny sample; diagonal proxy
        v = x.var().fillna(1e-4).to_numpy(dtype=float)
        return np.diag(np.maximum(v, 1e-6))
    if method == "ledoit_wolf":
        if LedoitWolf is None:
            # fallback to sample covariance
            return x.cov().to_numpy(dtype=float)
        lw = LedoitWolf().fit(x.to_numpy(dtype=float))
        return lw.covariance_
    elif method == "ewma":
        lam = float(ewma_lambda)
        demeaned = x - x.mean()
        cov = np.zeros((x.shape[1], x.shape[1]))
        weight = 1.0
        total = 0.0
        for i in range(len(demeaned) - 1, -1, -1):
            v = demeaned.iloc[i].to_numpy(dtype=float).reshape(-1, 1)
            cov += weight * (v @ v.T)
            total += weight
            weight *= lam
        cov = cov / max(total, 1e-12)
        return cov
    else:
        raise ValueError("unknown covariance method")


class PortfolioOptimizer:
    def __init__(self, cfg: OptimizerConfig):
        """
        Initialize the optimizer with the given configuration.
        
        Parameters:
            cfg (OptimizerConfig): Configuration object specifying method, covariance estimation,
                EWMA lambda, risk aversion, per-asset bounds, and minimum target return.
        """
        self.cfg = cfg

    def optimize(
        self,
        mu: pd.Series,
        returns: pd.DataFrame,
        current_weights: pd.Series | None = None,
    ) -> Tuple[pd.Series, dict]:
        """
        Compute mean–variance optimal portfolio weights under nonnegative, sum-to-one, and per-asset maximum constraints.
        
        If no return history is available, returns an equal-weight allocation constrained by the configured max position. If the configured minimum portfolio return is positive and the optimized portfolio fails to meet it, returns a predefined "risk_off" allocation and an explanatory status.
        
        Parameters:
            current_weights (pd.Series | None): Optional current portfolio weights; accepted for API compatibility and not used by this optimizer.
        
        Returns:
            tuple: A pair (weights, info) where `weights` is a pandas Series of asset weights that sum to 1 and `info` is a dict containing a `status` key (e.g., `"ok"`, `"no_returns"`, `"fallback_risk_off"`) and, when applicable, a `reason`.
        """
        tickers = list(mu.index)
        x = returns[tickers].dropna()
        if x.empty:
            # no returns; equal weight within box
            n = len(tickers)
            w = np.full(n, min(1.0 / n, self.cfg.max_position))
            w = w / w.sum()
            return pd.Series(w, index=tickers), {"status": "no_returns"}

        mu_vec = mu.to_numpy(dtype=float)
        cov = _estimate_covariance(x, self.cfg.covariance, self.cfg.ewma_lambda)
        # regularize Σ
        try:
            # ensure positive definite-ish
            cov = cov + 1e-6 * np.eye(cov.shape[0])
            inv = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            cov = cov + 1e-4 * np.eye(cov.shape[0])
            try:
                inv = np.linalg.inv(cov)
            except np.linalg.LinAlgError as e:
                raise OptimizationError(f"covariance inversion failed: {e}")

        lam = float(self.cfg.risk_aversion)
        raw = (inv @ mu_vec) / max(lam, 1e-9)
        w = _project_to_simplex_box(raw, self.cfg.max_position)
        w_series = pd.Series(w, index=tickers)

        min_ret = float(self.cfg.min_return)
        if min_ret > 0.0 and float(np.dot(w, mu_vec)) < min_ret:
            # fallback to risk_off template distribution over available tickers
            risk_off = {"VTI": 0.10, "BND": 0.70, "VTIP": 0.20}
            alloc = np.array([risk_off.get(t, 0.0) for t in tickers])
            if alloc.sum() <= 0:
                alloc = np.ones(len(tickers)) / len(tickers)
            w_series = pd.Series(alloc / alloc.sum(), index=tickers)
            return w_series, {"status": "fallback_risk_off", "reason": "min_return_not_met"}

        return w_series, {"status": "ok"}