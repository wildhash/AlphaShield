from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import cvxpy as cp

try:
    from sklearn.covariance import LedoitWolf
except Exception:  # pragma: no cover - optional dependency
    LedoitWolf = None  # type: ignore


class ClassicalPortfolioOptimizer:
    """
    Markowitz mean-variance optimization with practical constraints and covariance shrinkage.
    """

    def optimize(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        initial_weights: Optional[np.ndarray] = None,
        constraints: Optional[Dict] = None,
    ) -> np.ndarray:
        if constraints is None:
            constraints = {}
        n_assets = int(expected_returns.shape[0])
        w = cp.Variable(n_assets)

        Sigma = self._shrink_covariance(covariance_matrix)

        risk_aversion = float(constraints.get("risk_aversion", 1.0))
        portfolio_return = expected_returns @ w
        portfolio_risk = cp.quad_form(w, Sigma)
        objective = cp.Maximize(portfolio_return - risk_aversion * portfolio_risk)

        cons = [
            cp.sum(w) == 1.0,
            w >= 0.0,
        ]

        max_weight = float(constraints.get("max_weight", 0.20))
        cons.append(w <= max_weight)

        sector_limits = constraints.get("sector_limits")
        if sector_limits:
            for _sector, (asset_indices, max_exposure) in sector_limits.items():
                sector_weight = cp.sum(cp.hstack([w[i] for i in asset_indices]))
                cons.append(sector_weight <= float(max_exposure))

        if initial_weights is not None:
            max_turnover = float(constraints.get("max_turnover", 0.30))
            turnover = cp.norm1(w - initial_weights)
            cons.append(turnover <= max_turnover)

        problem = cp.Problem(objective, cons)
        try:
            problem.solve(solver=cp.ECOS, warm_start=True)
        except Exception:
            problem.solve(warm_start=True)

        if problem.status not in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE}:
            raise ValueError(f"Optimization failed: {problem.status}")

        weights = np.asarray(w.value, dtype=float)
        # Post-process for numerical stability
        weights = np.where(weights < 0, 0.0, weights)
        total = float(weights.sum())
        if total <= 0:
            # Fallback to equal weight
            weights = np.ones(n_assets) / n_assets
        else:
            weights = weights / total
        return weights

    def _shrink_covariance(self, Sigma: np.ndarray) -> np.ndarray:
        """
        Ledoit-Wolf shrinkage for stable covariance. If sklearn is unavailable,
        fall back to diagonal loading.
        """
        # If we have return series covariance matrix, ensure symmetry/PSD tweaks
        Sigma = np.asarray(Sigma, dtype=float)
        Sigma = (Sigma + Sigma.T) / 2.0

        if LedoitWolf is not None:
            try:
                # LedoitWolf expects samples; hack: reconstruct pseudo-samples via eigendecomposition
                # More robust: shrink towards diagonal via heuristic when samples not available
                lw = LedoitWolf(assume_centered=True)
                # Create pseudo-samples by sampling from multivariate normal with Sigma
                # Keep it small to avoid heavy compute
                n_assets = Sigma.shape[0]
                n_samples = max(200, 5 * n_assets)
                rng = np.random.default_rng(42)
                try:
                    pseudo = rng.multivariate_normal(np.zeros(n_assets), Sigma + np.eye(n_assets) * 1e-6, size=n_samples)
                except np.linalg.LinAlgError:
                    pseudo = rng.standard_normal(size=(n_samples, n_assets))
                lw.fit(pseudo)
                return lw.covariance_
            except Exception:
                pass

        # Fallback: simple diagonal shrinkage
        diag = np.diag(np.diag(Sigma))
        alpha = 0.1
        shrunk = (1 - alpha) * Sigma + alpha * diag
        # Ensure PSD by adding small jitter
        shrunk += np.eye(Sigma.shape[0]) * 1e-6
        return shrunk
