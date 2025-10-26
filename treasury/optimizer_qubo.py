"""QUBO formulation for quantum portfolio optimization."""
from typing import Optional, List, Tuple
import numpy as np
import os


def build_qubo(
    mu: np.ndarray,
    Sigma: np.ndarray,
    prev_level_idx: Optional[np.ndarray] = None,
    levels: int = 10
) -> Tuple[dict, float]:
    """Build QUBO formulation for portfolio optimization.
    
    Converts the mean-variance optimization problem into a QUBO
    (Quadratic Unconstrained Binary Optimization) that can be solved
    on quantum annealer.
    
    Args:
        mu: Expected returns vector (n_assets,)
        Sigma: Covariance matrix (n_assets, n_assets)
        prev_level_idx: Previous weight levels for turnover constraint
        levels: Number of discretization levels for weights
        
    Returns:
        Tuple of (qubo_dict, penalty_scale)
        qubo_dict: Dictionary mapping (var1, var2) -> coefficient
        penalty_scale: Penalty multiplier for constraints
    """
    n_assets = len(mu)
    
    # QUBO dictionary: maps (i, j) -> coefficient
    Q = {}
    
    # Discretize weights into binary variables
    # Each asset gets 'levels' binary variables
    # weight_i = sum(b_ij * 2^j) / 2^levels for j in [0, levels)
    
    # Risk aversion parameter
    lambda_risk = 1.0
    
    # Penalty for constraint violations
    penalty = 10.0
    
    # Build QUBO terms
    for i in range(n_assets):
        for j in range(levels):
            var_idx = i * levels + j
            
            # Linear terms from expected returns
            # Maximize returns -> minimize negative returns
            weight_value = (2 ** j) / (2 ** levels)
            Q[(var_idx, var_idx)] = Q.get((var_idx, var_idx), 0) - mu[i] * weight_value
            
            # Add risk terms (quadratic)
            for k in range(n_assets):
                for l in range(levels):
                    var_idx2 = k * levels + l
                    weight_value2 = (2 ** l) / (2 ** levels)
                    
                    risk_term = lambda_risk * Sigma[i, k] * weight_value * weight_value2
                    
                    if var_idx <= var_idx2:
                        Q[(var_idx, var_idx2)] = Q.get((var_idx, var_idx2), 0) + risk_term
    
    # Add constraint: sum of weights = 1
    # Penalty term: penalty * (sum(weights) - 1)^2
    for i in range(n_assets):
        for j in range(levels):
            var_idx = i * levels + j
            weight_value = (2 ** j) / (2 ** levels)
            
            # Linear part of (sum - 1)^2
            Q[(var_idx, var_idx)] = Q.get((var_idx, var_idx), 0) + penalty * (2 * weight_value - 2 * weight_value)
            
            # Quadratic part
            for k in range(n_assets):
                for l in range(levels):
                    var_idx2 = k * levels + l
                    weight_value2 = (2 ** l) / (2 ** levels)
                    
                    if var_idx <= var_idx2:
                        Q[(var_idx, var_idx2)] = Q.get((var_idx, var_idx2), 0) + penalty * 2 * weight_value * weight_value2
    
    return Q, penalty


def solve_qubo(
    Q: dict,
    penalty: float,
    num_reads: int = 1000,
    api_token: Optional[str] = None
) -> Optional[np.ndarray]:
    """Solve QUBO using quantum annealer or classical solver.
    
    Args:
        Q: QUBO dictionary
        penalty: Penalty scale
        num_reads: Number of annealer reads
        api_token: D-Wave API token (optional)
        
    Returns:
        Weight vector if successful, None otherwise
    """
    # Check if quantum is enabled
    quantum_enabled = os.getenv('QUANTUM', 'false').lower() == 'true'
    
    if not quantum_enabled:
        # Return None to trigger fallback to classical QP
        return None
    
    try:
        # Try to use D-Wave quantum annealer
        import dimod
        from dwave.system import DWaveSampler, EmbeddingComposite
        
        # Create BQM (Binary Quadratic Model)
        bqm = dimod.BinaryQuadraticModel.from_qubo(Q)
        
        if api_token:
            # Use actual quantum hardware
            sampler = EmbeddingComposite(DWaveSampler(token=api_token))
        else:
            # Use simulated annealer
            sampler = dimod.SimulatedAnnealingSampler()
        
        # Solve
        sampleset = sampler.sample(bqm, num_reads=num_reads)
        
        # Get best solution
        best_sample = sampleset.first.sample
        
        # Decode binary variables to weights
        weights = decode_solution(best_sample)
        
        return weights
    
    except ImportError:
        # D-Wave not available, return None to trigger fallback
        return None
    except Exception:
        # Any other error, return None to trigger fallback
        return None


def decode_solution(binary_solution: dict, levels: int = 10, n_assets: int = 4) -> np.ndarray:
    """Decode binary solution to portfolio weights.
    
    Args:
        binary_solution: Dictionary mapping variable index to binary value
        levels: Number of discretization levels
        n_assets: Number of assets
        
    Returns:
        Portfolio weights vector
    """
    weights = np.zeros(n_assets)
    
    for i in range(n_assets):
        for j in range(levels):
            var_idx = i * levels + j
            if var_idx in binary_solution and binary_solution[var_idx] == 1:
                weights[i] += (2 ** j) / (2 ** levels)
    
    # Normalize to sum to 1
    weight_sum = weights.sum()
    if weight_sum > 0:
        weights = weights / weight_sum
    else:
        # If all zeros, return equal weights
        weights = np.ones(n_assets) / n_assets
    
    return weights
