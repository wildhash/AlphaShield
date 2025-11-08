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
    w = np.clip(w, 0.0, max_pos)
    s = w.sum()
    if s <= 0:
        # fallback: equal weight within box
        n = w.shape[0]
        return np.full(n, min(1.0 / n, max_pos))
    return w / s


def _estimate_covariance(returns: pd.DataFrame, method: str, ewma_lambda: float) -> np.ndarray:
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
        self.cfg = cfg

    def optimize(
        self,
        mu: pd.Series,
        returns: pd.DataFrame,
        current_weights: pd.Series | None = None,
    ) -> Tuple[pd.Series, dict]:
        """
        Closed-form mean-variance: argmin_w lambda w^T Σ w - w^T μ
        subject to w>=0, sum w = 1, w<=max_pos. Projection handles constraints.
        If target expected return not met, fallback to risk_off.
        Returns weights Series and info dict.
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
