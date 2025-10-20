# Quantum Portfolio Optimization

AlphaShield now includes quantum computing capabilities for portfolio optimization using D-Wave's quantum annealing technology.

## Overview

The quantum optimization system converts the continuous portfolio optimization problem into a Quadratic Unconstrained Binary Optimization (QUBO) problem that can be solved on D-Wave quantum computers.

### Key Features

1. **QUBO Formulation**: Converts mean-variance portfolio optimization to binary quantum problem
2. **D-Wave Integration**: Real quantum computing via D-Wave Ocean SDK
3. **Automatic Fallback**: Gracefully falls back to classical optimization if quantum unavailable
4. **Performance Tracking**: Compare quantum vs classical optimization performance

## Installation

### Basic (Classical Only)

```bash
pip install numpy pandas cvxpy scipy
```

### With Quantum Support

```bash
pip install numpy pandas cvxpy scipy dwave-ocean-sdk
```

### D-Wave API Setup

1. Sign up for free quantum access at [cloud.dwavesys.com](https://cloud.dwavesys.com)
2. Get your API token from the dashboard
3. Set environment variable:

```bash
export DWAVE_API_TOKEN="your_token_here"
```

## Usage

### Basic Optimization with Fallback

```python
import numpy as np
from trading_core.portfolio.optimizer_qp import (
    optimize_with_fallback,
    setup_quantum_environment
)

# Setup quantum (checks if D-Wave is available)
quantum_available = setup_quantum_environment()

# Define portfolio parameters
expected_returns = np.array([0.12, 0.10, 0.15, 0.08])
covariance_matrix = np.array([
    [0.04, 0.01, 0.02, 0.00],
    [0.01, 0.03, 0.01, 0.00],
    [0.02, 0.01, 0.05, 0.01],
    [0.00, 0.00, 0.01, 0.02]
])
current_weights = np.array([0.25, 0.25, 0.25, 0.25])

# Optimize with automatic fallback
weights, method = optimize_with_fallback(
    expected_returns,
    covariance_matrix,
    current_weights,
    risk_aversion=1.0,
    quantum_available=quantum_available
)

print(f"Optimization method: {method}")
print(f"Portfolio weights: {weights}")
```

### QUBO Formulation Only

If you want to just create the QUBO formulation for analysis:

```python
from trading_core.portfolio.optimizer_qp import create_detailed_qubo_formulation

qubo = create_detailed_qubo_formulation(
    expected_returns,
    covariance_matrix,
    n_discrete_levels=10  # Number of weight levels per asset
)

print(f"QUBO matrix shape: {qubo['Q_matrix'].shape}")
print(f"Total variables: {qubo['total_variables']}")
print(f"Weight levels: {qubo['weight_levels']}")
```

### Performance Tracking

Track and compare optimization methods:

```python
import pandas as pd
from trading_core.portfolio.optimizer_qp import PerformanceTracker

tracker = PerformanceTracker()

# After each optimization
returns = pd.Series([0.01, -0.005, 0.015, 0.02, -0.01] * 50)

tracker.log_optimization(
    method="quantum_dwave",
    solve_time=0.5,
    portfolio_value=10500.0,
    returns=returns
)

# Get comparison
comparison = tracker.get_method_comparison()
print(comparison)
```

### Integration with Backtest Engine

Update the backtest engine to use quantum optimization:

```python
from backtest.engine import BacktestEngine
from trading_core.portfolio.optimizer_qp import optimize_with_fallback, setup_quantum_environment

# In your backtest setup
quantum_available = setup_quantum_environment()

# Then in the optimization step, replace:
# w_target = optimize_classical(...)

# With:
w_target, method = optimize_with_fallback(
    expected_returns=mu,
    covariance_matrix=Sigma,
    current_weights=self.w,
    risk_aversion=1.0,
    quantum_available=quantum_available
)
```

## How It Works

### QUBO Formulation

The continuous portfolio optimization problem:

```
maximize: μ'w - (λ/2)w'Σw
subject to: Σw_i = 1, 0 ≤ w_i ≤ 0.5
```

Is converted to a binary problem where:
- Each asset gets `n_discrete_levels` binary variables (default 10)
- Variable `x[i][j] = 1` if asset `i` gets weight level `j`
- Weight levels: 0%, 5.6%, 11.1%, ..., 50%

The QUBO matrix includes:
1. **Return terms**: Maximize expected returns (negated for minimization)
2. **Risk terms**: Minimize portfolio variance
3. **Constraint penalties**: Large penalties for constraint violations
   - One-hot constraint: Each asset must have exactly one weight level
   - Sum-to-one: Portfolio weights must sum to 1

### D-Wave Quantum Annealing

1. QUBO matrix is converted to sparse dictionary format
2. Problem is submitted to D-Wave quantum computer
3. Quantum annealing runs 1000 times to find best solution
4. Binary solution is decoded back to portfolio weights
5. Solution is validated against constraints

### Fallback Chain

1. **Try Quantum**: If `quantum_available=True` and D-Wave SDK installed
2. **Fall back to Classical**: If quantum fails or unavailable, use CVXPY
3. **Equal Weights**: If classical fails, use equal weight portfolio

## Performance Considerations

### Quantum Advantages
- Can handle non-convex constraints
- Potentially faster for large portfolios (>100 assets)
- Explores solution space more thoroughly

### Quantum Limitations
- Discretization of weights (10 levels by default)
- Currently limited to ~170 binary variables (embedding constraints)
- Higher latency (network + quantum processing time)

### Recommendations
- **Small portfolios (<10 assets)**: Classical is typically faster
- **Medium portfolios (10-50 assets)**: Quantum can be competitive
- **Large portfolios (>50 assets)**: Quantum may have advantages

## Troubleshooting

### Import Error: D-Wave Ocean SDK

```
ImportError: No module named 'dwave'
```

**Solution**: Install D-Wave Ocean SDK:
```bash
pip install dwave-ocean-sdk
```

### Connection Error

```
Error: Unable to connect to D-Wave
```

**Solutions**:
1. Check API token is set: `echo $DWAVE_API_TOKEN`
2. Verify internet connection
3. Check D-Wave system status at [cloud.dwavesys.com](https://cloud.dwavesys.com)

### Validation Failed

```
WARNING: Quantum solution validation failed, falling back to classical
```

This is normal and means the quantum solution didn't meet constraints. The system automatically falls back to classical optimization.

## Example Output

```
INFO: Attempting quantum portfolio optimization...
INFO: Submitting portfolio optimization to D-Wave quantum computer...
INFO: Connected to D-Wave Advantage_system4.1 quantum processor
INFO: Available qubits: 5627
INFO: Quantum optimization completed. Best energy: -0.0245
INFO: Quantum solution validated successfully
INFO: ✅ Quantum optimization successful
Optimization method: quantum_dwave
Portfolio weights: [0.31 0.23 0.28 0.18]
```

## References

- [D-Wave Ocean Documentation](https://docs.ocean.dwavesys.com/)
- [QUBO Formulation Guide](https://docs.dwavesys.com/docs/latest/c_handbook_3.html)
- [Portfolio Optimization with Quantum Computing](https://arxiv.org/abs/2007.00017)

## Support

For issues or questions:
1. Check D-Wave status: [cloud.dwavesys.com](https://cloud.dwavesys.com)
2. Review D-Wave documentation
3. File an issue on the AlphaShield GitHub repository
