import cvxpy as cp
import numpy as np
import logging
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass
import pandas as pd

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


def create_detailed_qubo_formulation(expected_returns: np.ndarray,
                                   covariance_matrix: np.ndarray,
                                   n_discrete_levels: int = 10) -> Dict:
    """
    DETAILED QUBO Formulation for Portfolio Optimization
    Converts continuous portfolio problem to binary quantum problem
    """
    n_assets = len(expected_returns)
    
    # Each asset gets n_discrete_levels binary variables
    # Variable x[i][j] = 1 if asset i gets weight level j, 0 otherwise
    total_vars = n_assets * n_discrete_levels
    
    # Weight levels (0%, 5%, 10%, ..., 50% for max_position_size = 0.5)
    weight_levels = np.linspace(0, 0.5, n_discrete_levels)
    
    # Initialize QUBO matrix Q
    Q = np.zeros((total_vars, total_vars))
    
    # OBJECTIVE TERMS
    # 1. Expected return term (we want to MAXIMIZE this, so negate for minimization)
    for i in range(n_assets):
        for j in range(n_discrete_levels):
            var_idx = i * n_discrete_levels + j
            Q[var_idx, var_idx] -= expected_returns[i] * weight_levels[j]
    
    # 2. Risk penalty term (quadratic)
    for i1 in range(n_assets):
        for j1 in range(n_discrete_levels):
            for i2 in range(n_assets):
                for j2 in range(n_discrete_levels):
                    var1_idx = i1 * n_discrete_levels + j1
                    var2_idx = i2 * n_discrete_levels + j2
                    
                    risk_term = covariance_matrix[i1, i2] * weight_levels[j1] * weight_levels[j2]
                    Q[var1_idx, var2_idx] += 0.5 * risk_term  # Risk penalty
    
    # CONSTRAINT PENALTIES (large penalties for constraint violations)
    penalty_weight = 1000.0
    
    # 3. One-hot constraint: exactly one weight level per asset
    for i in range(n_assets):
        for j1 in range(n_discrete_levels):
            for j2 in range(j1 + 1, n_discrete_levels):
                var1_idx = i * n_discrete_levels + j1
                var2_idx = i * n_discrete_levels + j2
                Q[var1_idx, var2_idx] += penalty_weight  # Penalty for both being 1
    
    # 4. Sum-to-one constraint: portfolio weights must sum to 1
    # (sum of weight_levels * binary_vars - 1)^2 = penalty
    for i1 in range(n_assets):
        for j1 in range(n_discrete_levels):
            for i2 in range(n_assets):
                for j2 in range(n_discrete_levels):
                    var1_idx = i1 * n_discrete_levels + j1
                    var2_idx = i2 * n_discrete_levels + j2
                    
                    if var1_idx != var2_idx:
                        Q[var1_idx, var2_idx] += penalty_weight * weight_levels[j1] * weight_levels[j2]
    
    # Linear terms for sum-to-one constraint
    for i in range(n_assets):
        for j in range(n_discrete_levels):
            var_idx = i * n_discrete_levels + j
            Q[var_idx, var_idx] -= 2 * penalty_weight * weight_levels[j]
    
    return {
        'Q_matrix': Q,
        'n_assets': n_assets,
        'n_levels': n_discrete_levels,
        'weight_levels': weight_levels,
        'variable_mapping': _create_variable_mapping(n_assets, n_discrete_levels),
        'total_variables': total_vars
    }


def _create_variable_mapping(n_assets: int, n_levels: int) -> Dict[int, Tuple[int, int]]:
    """
    Create mapping: variable_index -> (asset_index, weight_level_index)
    """
    mapping = {}
    var_idx = 0
    for asset in range(n_assets):
        for level in range(n_levels):
            mapping[var_idx] = (asset, level)
            var_idx += 1
    return mapping


def optimize_quantum_dwave(qubo_formulation: Dict) -> Optional[np.ndarray]:
    """
    ACTUAL D-Wave quantum optimization implementation
    Replace placeholder with real quantum computing
    """
    try:
        # Import D-Wave Ocean SDK
        from dwave.system import DWaveSampler, EmbeddingComposite
        import dwave.inspector
        
        # Get QUBO matrix and parameters
        Q = qubo_formulation['Q_matrix']
        n_assets = qubo_formulation['n_assets']
        n_levels = qubo_formulation['n_levels']
        weight_levels = qubo_formulation['weight_levels']
        variable_mapping = qubo_formulation['variable_mapping']
        
        # Convert numpy matrix to dict format for D-Wave
        Q_dict = {}
        for i in range(Q.shape[0]):
            for j in range(i, Q.shape[1]):  # Upper triangular only
                if Q[i, j] != 0:
                    Q_dict[(i, j)] = Q[i, j]
        
        # Initialize D-Wave sampler
        sampler = EmbeddingComposite(DWaveSampler())
        
        # Set sampling parameters
        num_reads = 1000  # Number of quantum annealing runs
        chain_strength = max(abs(Q.max()), abs(Q.min())) * 2  # Strength of constraint chains
        
        # Submit to quantum computer
        logging.info("Submitting portfolio optimization to D-Wave quantum computer...")
        response = sampler.sample_qubo(
            Q_dict,
            num_reads=num_reads,
            chain_strength=chain_strength,
            annealing_time=20,  # Microseconds of annealing
            label="AlphaShield Portfolio Optimization"
        )
        
        # Get best solution
        best_sample = response.first.sample
        best_energy = response.first.energy
        
        logging.info(f"Quantum optimization completed. Best energy: {best_energy}")
        
        # Convert binary solution back to portfolio weights
        portfolio_weights = _decode_quantum_solution(
            best_sample, variable_mapping, n_assets, n_levels, weight_levels
        )
        
        # Validate solution
        if _validate_quantum_solution(portfolio_weights):
            logging.info("Quantum solution validated successfully")
            return portfolio_weights
        else:
            logging.warning("Quantum solution validation failed, falling back to classical")
            return None
    
    except ImportError:
        logging.warning("D-Wave Ocean SDK not installed. Install with: pip install dwave-ocean-sdk")
        return None
    
    except Exception as e:
        logging.error(f"Quantum optimization failed: {str(e)}")
        return None


def _decode_quantum_solution(binary_solution: Dict[int, int],
                            variable_mapping: Dict[int, Tuple[int, int]],
                            n_assets: int,
                            n_levels: int,
                            weight_levels: np.ndarray) -> np.ndarray:
    """
    Convert binary quantum solution back to portfolio weights
    """
    portfolio_weights = np.zeros(n_assets)
    
    for var_idx, binary_value in binary_solution.items():
        if binary_value == 1:  # This variable is selected
            asset_idx, level_idx = variable_mapping[var_idx]
            portfolio_weights[asset_idx] = weight_levels[level_idx]
    
    # Normalize to ensure weights sum to 1 (handle small quantum errors)
    total_weight = portfolio_weights.sum()
    if total_weight > 0:
        portfolio_weights = portfolio_weights / total_weight
    
    return portfolio_weights


def _validate_quantum_solution(weights: np.ndarray) -> bool:
    """
    Validate that quantum solution meets portfolio constraints
    """
    # Check weights sum to approximately 1
    if abs(weights.sum() - 1.0) > 0.01:
        return False
    
    # Check no negative weights
    if np.any(weights < -0.001):
        return False
    
    # Check position limits
    if np.any(weights > 0.51):  # Allow small tolerance
        return False
    
    return True


def optimize_with_fallback(expected_returns: np.ndarray,
                          covariance_matrix: np.ndarray,
                          current_weights: np.ndarray,
                          risk_aversion: float = 1.0,
                          quantum_available: bool = False) -> Tuple[np.ndarray, str]:
    """
    Try quantum first, fallback to classical with detailed logging
    Returns (weights, method_used)
    """
    method_used = "unknown"
    
    # Try quantum optimization first
    if quantum_available:
        logging.info("Attempting quantum portfolio optimization...")
        
        try:
            # Prepare QUBO formulation
            qubo_formulation = create_detailed_qubo_formulation(
                expected_returns, covariance_matrix
            )
            
            # Try quantum optimization
            quantum_weights = optimize_quantum_dwave(qubo_formulation)
            
            if quantum_weights is not None:
                logging.info("✅ Quantum optimization successful")
                return quantum_weights, "quantum_dwave"
            else:
                logging.warning("⚠️ Quantum optimization failed, trying classical...")
        
        except Exception as e:
            logging.error(f"❌ Quantum optimization error: {str(e)}")
    
    # Fallback to classical optimization
    logging.info("Using classical convex optimization...")
    
    try:
        classical_weights = optimize_classical(
            expected_returns, covariance_matrix, current_weights, risk_aversion=risk_aversion
        )
        
        if classical_weights is not None:
            logging.info("✅ Classical optimization successful")
            return classical_weights, "classical_cvxpy"
        else:
            logging.error("❌ Classical optimization failed")
    
    except Exception as e:
        logging.error(f"❌ Classical optimization error: {str(e)}")
    
    # Last resort: equal weights
    logging.warning("🚨 All optimization methods failed, using equal weights")
    n_assets = len(expected_returns)
    equal_weights = np.ones(n_assets) / n_assets
    return equal_weights, "equal_weights_fallback"


def setup_quantum_environment() -> bool:
    """
    Setup quantum computing environment
    """
    try:
        import dwave
        from dwave.system import DWaveSampler
        
        # Test connection to D-Wave
        sampler = DWaveSampler()
        properties = sampler.properties
        
        logging.info(f"Connected to D-Wave {properties.get('chip_id', 'Unknown')} quantum processor")
        logging.info(f"Available qubits: {len(properties.get('qubits', []))}")
        
        return True
    
    except Exception as e:
        logging.warning(f"Quantum setup failed: {str(e)}")
        logging.info("Running in classical-only mode")
        return False


@dataclass
class OptimizationMetrics:
    """Track performance of different optimization methods"""
    method: str
    solve_time_seconds: float
    final_portfolio_value: float
    sharpe_ratio: float
    max_drawdown: float
    constraint_violations: int


class PerformanceTracker:
    """
    Compare quantum vs classical optimization performance
    """
    
    def __init__(self):
        self.metrics_history: List[OptimizationMetrics] = []
    
    def log_optimization(self, 
                        method: str,
                        solve_time: float,
                        portfolio_value: float,
                        returns: pd.Series):
        """Log optimization performance metrics"""
        
        # Calculate metrics
        sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
        max_dd = self._calculate_max_drawdown(returns)
        
        metrics = OptimizationMetrics(
            method=method,
            solve_time_seconds=solve_time,
            final_portfolio_value=portfolio_value,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            constraint_violations=0  # Would be calculated based on constraints
        )
        
        self.metrics_history.append(metrics)
        
        # Log summary
        logging.info(f"Optimization Method: {method}")
        logging.info(f"Solve Time: {solve_time:.3f}s")
        logging.info(f"Sharpe Ratio: {sharpe:.2f}")
        logging.info(f"Max Drawdown: {max_dd:.2%}")
    
    def get_method_comparison(self) -> pd.DataFrame:
        """Compare performance across optimization methods"""
        if not self.metrics_history:
            return pd.DataFrame()
        
        data = []
        for metric in self.metrics_history:
            data.append({
                'method': metric.method,
                'solve_time': metric.solve_time_seconds,
                'sharpe_ratio': metric.sharpe_ratio,
                'max_drawdown': metric.max_drawdown
            })
        
        df = pd.DataFrame(data)
        return df.groupby('method').agg({
            'solve_time': 'mean',
            'sharpe_ratio': 'mean',
            'max_drawdown': 'mean'
        }).round(3)
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown from returns series"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return float(drawdown.min())
