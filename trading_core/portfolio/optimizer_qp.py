import cvxpy as cp
import numpy as np
from typing import Optional

def shrink_cov(cov: np.ndarray, shrink: float = 0.2) -> np.ndarray:
    """Simple Ledoit-Wolf-style shrinkage toward diagonal."""
    cov = np.asarray(cov, dtype=float)
    diag = np.diag(np.diag(cov))
    return (1 - shrink) * cov + shrink * diag

def optimize_classical(
    expected_returns: np.ndarray,
    covariance_matrix: np.ndarray,
    current_weights: np.ndarray,
    max_position_size: float = 0.25,
    risk_aversion: float = 1.0,
    turnover_budget: float = 0.20,
    solver: str = "ECOS"
) -> np.ndarray:
    """
    Long-only mean-variance with L1 turnover penalty and hard turnover budget.
    sum(w)=1, 0<=w<=max_position_size, ||w - w_prev||_1 <= turnover_budget
    """
    mu = np.asarray(expected_returns, dtype=float)
    Sigma = shrink_cov(np.asarray(covariance_matrix, dtype=float), shrink=0.2)
    w_prev = np.asarray(current_weights, dtype=float)
    n = mu.shape[0]

    if n == 0:
        return w_prev

    w = cp.Variable(n)
    ret = mu @ w
    risk = cp.quad_form(w, Sigma)
    tc = 0.001 * cp.norm1(w - w_prev)

    obj = cp.Maximize(ret - 0.5 * risk_aversion * risk - tc)
    cons = [
        cp.sum(w) == 1.0,
        w >= 0.0,
        w <= max_position_size,
        cp.norm1(w - w_prev) <= turnover_budget
    ]
    prob = cp.Problem(obj, cons)
    prob.solve(solver=solver, max_iters=20000, abstol=1e-8, reltol=1e-8, feastol=1e-8)

    if prob.status in ("optimal", "optimal_inaccurate") and w.value is not None:
        return np.clip(w.value, 0.0, 1.0)
    return w_prev
