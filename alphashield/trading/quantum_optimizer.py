from __future__ import annotations

from typing import Optional

import numpy as np

try:  # Optional quantum dependencies
    import dimod  # type: ignore
    from dwave.system import DWaveSampler, EmbeddingComposite  # type: ignore
except Exception:  # pragma: no cover
    dimod = None  # type: ignore
    DWaveSampler = None  # type: ignore
    EmbeddingComposite = None  # type: ignore


class QuantumPortfolioOptimizer:
    """Quantum portfolio optimization using a QUBO formulation."""

    def __init__(self, api_token: Optional[str] = None) -> None:
        self.available = dimod is not None and DWaveSampler is not None and EmbeddingComposite is not None
        self._sampler = None
        if self.available and api_token:
            try:
                self._sampler = EmbeddingComposite(DWaveSampler(token=api_token))
            except Exception:
                # If sampler initialization fails, mark as unavailable
                self.available = False
                self._sampler = None

    def optimize_portfolio(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        risk_aversion: float = 1.0,
        num_bins: int = 10,
        num_reads: int = 1000,
    ) -> np.ndarray:
        """
        Optimize portfolio weights via QUBO. If quantum backend is unavailable,
        return a simple heuristic allocation proportional to expected returns.
        """
        n_assets = expected_returns.shape[0]

        if not self.available or self._sampler is None or dimod is None:
            # Heuristic fallback: softmax over expected returns
            logits = expected_returns - expected_returns.max()
            exp = np.exp(logits)
            w = exp / exp.sum()
            return w

        Q = self._build_qubo_matrix(expected_returns, covariance_matrix, risk_aversion, num_bins)
        bqm = dimod.BinaryQuadraticModel.from_qubo(Q)
        sampleset = self._sampler.sample(bqm, num_reads=num_reads)
        best_sample = sampleset.first.sample
        weights = self._decode_solution(best_sample, n_assets, num_bins)
        return weights

    def _build_qubo_matrix(
        self,
        mu: np.ndarray,
        Sigma: np.ndarray,
        lambda_risk: float,
        num_bins: int,
    ):
        n = len(mu)
        Q: dict[tuple[str, str], float] = {}
        # Quadratic terms
        for i in range(n):
            for j in range(n):
                for bi in range(num_bins):
                    for bj in range(num_bins):
                        vi = f"x_{i}_{bi}"
                        vj = f"x_{j}_{bj}"
                        risk_term = lambda_risk * float(Sigma[i, j]) * (bi * bj) / (num_bins**2)
                        return_term = 0.0
                        if i == j and bi == bj:
                            return_term = -float(mu[i]) * (bi / num_bins)
                        key = (vi, vj) if vi <= vj else (vj, vi)
                        Q[key] = Q.get(key, 0.0) + risk_term + return_term

        # Investment constraint penalty: (sum w - 1)^2
        penalty = 10.0
        for i in range(n):
            for bi in range(num_bins):
                vi = f"x_{i}_{bi}"
                key = (vi, vi)
                Q[key] = Q.get(key, 0.0) + penalty * (bi / num_bins) ** 2
                for j in range(i, n):
                    for bj in range(num_bins):
                        vj = f"x_{j}_{bj}"
                        if vi == vj:
                            continue
                        key2 = (vi, vj) if vi <= vj else (vj, vi)
                        Q[key2] = Q.get(key2, 0.0) + 2.0 * penalty * (bi * bj) / (num_bins**2)
        return Q

    def _decode_solution(self, sample: dict[str, int], n_assets: int, num_bins: int) -> np.ndarray:
        weights = np.zeros(n_assets)
        for i in range(n_assets):
            for b in range(num_bins):
                var = f"x_{i}_{b}"
                if int(sample.get(var, 0)) == 1:
                    weights[i] += b / num_bins
        s = weights.sum()
        if s <= 0:
            return np.ones(n_assets) / n_assets
        return weights / s


class HybridOptimizer:
    """Hybrid optimization: quantum for coarse allocation, classical for refinement."""

    def __init__(self, quantum_optimizer, classical_optimizer) -> None:
        self.quantum = quantum_optimizer
        self.classical = classical_optimizer

    def optimize(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        constraints: dict,
        initial_guess: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        quantum_weights = self.quantum.optimize_portfolio(
            expected_returns, covariance_matrix, num_bins=10
        )
        final_weights = self.classical.optimize(
            expected_returns,
            covariance_matrix,
            initial_weights=initial_guess if initial_guess is not None else quantum_weights,
            constraints=constraints,
        )
        return final_weights
