"""
Demonstration of quantum portfolio optimization with AlphaShield.

This example shows how to:
1. Set up quantum environment
2. Use QUBO formulation
3. Run optimization with fallback
4. Track performance metrics
"""

import numpy as np
import pandas as pd
from trading_core.portfolio.optimizer_qp import (
    optimize_with_fallback,
    setup_quantum_environment,
    create_detailed_qubo_formulation,
    PerformanceTracker,
    optimize_classical
)
import time


def main():
    print("=" * 70)
    print("AlphaShield Quantum Portfolio Optimization Demo")
    print("=" * 70)
    
    # Step 1: Setup quantum environment
    print("\n1. Setting up quantum environment...")
    quantum_available = setup_quantum_environment()
    
    if quantum_available:
        print("   ✅ Quantum computing is AVAILABLE")
        print("   🚀 D-Wave quantum computer connected")
    else:
        print("   ℹ️  Quantum computing is NOT AVAILABLE")
        print("   🔧 Will use classical optimization only")
    
    # Step 2: Define portfolio parameters
    print("\n2. Defining portfolio parameters...")
    
    n_assets = 5
    asset_names = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    
    # Expected annual returns (mock data)
    expected_returns = np.array([0.12, 0.15, 0.10, 0.18, 0.20])
    
    # Covariance matrix (mock data)
    np.random.seed(42)
    random_cov = np.random.randn(n_assets, n_assets) * 0.01
    covariance_matrix = random_cov @ random_cov.T + np.eye(n_assets) * 0.02
    
    # Current portfolio (starting equal weighted)
    current_weights = np.ones(n_assets) / n_assets
    
    print(f"   Number of assets: {n_assets}")
    print(f"   Asset names: {asset_names}")
    print(f"   Expected returns: {expected_returns}")
    print(f"   Current weights: {current_weights}")
    
    # Step 3: Create QUBO formulation (for analysis)
    print("\n3. Creating QUBO formulation...")
    
    qubo = create_detailed_qubo_formulation(
        expected_returns,
        covariance_matrix,
        n_discrete_levels=10
    )
    
    print(f"   QUBO matrix shape: {qubo['Q_matrix'].shape}")
    print(f"   Total variables: {qubo['total_variables']}")
    print(f"   Weight levels: {qubo['weight_levels']}")
    print(f"   Number of weight levels: {qubo['n_levels']}")
    
    # Step 4: Run optimization with fallback
    print("\n4. Running portfolio optimization...")
    
    start_time = time.time()
    
    optimized_weights, method = optimize_with_fallback(
        expected_returns,
        covariance_matrix,
        current_weights,
        risk_aversion=1.0,
        quantum_available=quantum_available
    )
    
    solve_time = time.time() - start_time
    
    print(f"\n   Optimization completed!")
    print(f"   Method used: {method}")
    print(f"   Solve time: {solve_time:.3f} seconds")
    print(f"\n   Optimized portfolio weights:")
    for i, (asset, weight) in enumerate(zip(asset_names, optimized_weights)):
        print(f"      {asset:6s}: {weight:.4f} ({weight*100:.2f}%)")
    
    # Step 5: Compare with classical optimization
    print("\n5. Comparing with classical optimization...")
    
    classical_start = time.time()
    classical_weights = optimize_classical(
        expected_returns,
        covariance_matrix,
        current_weights,
        risk_aversion=1.0
    )
    classical_time = time.time() - classical_start
    
    print(f"   Classical solve time: {classical_time:.3f} seconds")
    print(f"\n   Classical portfolio weights:")
    for i, (asset, weight) in enumerate(zip(asset_names, classical_weights)):
        print(f"      {asset:6s}: {weight:.4f} ({weight*100:.2f}%)")
    
    # Step 6: Calculate portfolio metrics
    print("\n6. Portfolio metrics...")
    
    def calculate_metrics(weights, returns, cov):
        """Calculate portfolio return and risk"""
        portfolio_return = np.dot(weights, returns)
        portfolio_risk = np.sqrt(np.dot(weights, np.dot(cov, weights)))
        sharpe_ratio = portfolio_return / portfolio_risk if portfolio_risk > 0 else 0
        return portfolio_return, portfolio_risk, sharpe_ratio
    
    opt_return, opt_risk, opt_sharpe = calculate_metrics(
        optimized_weights, expected_returns, covariance_matrix
    )
    
    class_return, class_risk, class_sharpe = calculate_metrics(
        classical_weights, expected_returns, covariance_matrix
    )
    
    print(f"\n   {method} optimization:")
    print(f"      Expected return: {opt_return:.4f} ({opt_return*100:.2f}%)")
    print(f"      Portfolio risk:  {opt_risk:.4f}")
    print(f"      Sharpe ratio:    {opt_sharpe:.4f}")
    
    print(f"\n   Classical optimization:")
    print(f"      Expected return: {class_return:.4f} ({class_return*100:.2f}%)")
    print(f"      Portfolio risk:  {class_risk:.4f}")
    print(f"      Sharpe ratio:    {class_sharpe:.4f}")
    
    # Step 7: Performance tracking
    print("\n7. Setting up performance tracking...")
    
    tracker = PerformanceTracker()
    
    # Simulate some returns
    mock_returns = pd.Series(np.random.randn(250) * 0.01 + 0.0005)
    
    tracker.log_optimization(
        method=method,
        solve_time=solve_time,
        portfolio_value=10000 * (1 + opt_return),
        returns=mock_returns
    )
    
    tracker.log_optimization(
        method="classical_cvxpy",
        solve_time=classical_time,
        portfolio_value=10000 * (1 + class_return),
        returns=mock_returns
    )
    
    print("\n   Performance comparison:")
    comparison = tracker.get_method_comparison()
    print(comparison)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if quantum_available and method == "quantum_dwave":
        print("✅ Quantum optimization was successful!")
        print(f"   - Quantum solve time: {solve_time:.3f}s")
        print(f"   - Classical solve time: {classical_time:.3f}s")
        speedup = classical_time / solve_time if solve_time > 0 else 0
        print(f"   - Speedup: {speedup:.2f}x")
    else:
        print("ℹ️  Classical optimization was used")
        print("   To enable quantum optimization:")
        print("   1. Install D-Wave SDK: pip install dwave-ocean-sdk")
        print("   2. Get API token from cloud.dwavesys.com")
        print("   3. Set environment variable: export DWAVE_API_TOKEN='your_token'")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
