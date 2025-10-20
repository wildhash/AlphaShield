"""
Tests for quantum portfolio optimization functionality.
"""
import unittest
import numpy as np
import pandas as pd
from trading_core.portfolio.optimizer_qp import (
    create_detailed_qubo_formulation,
    _create_variable_mapping,
    _decode_quantum_solution,
    _validate_quantum_solution,
    optimize_with_fallback,
    OptimizationMetrics,
    PerformanceTracker
)


class TestQUBOFormulation(unittest.TestCase):
    """Test QUBO formulation for quantum optimization"""
    
    def test_qubo_formulation_basic(self):
        """Test basic QUBO formulation"""
        n_assets = 3
        expected_returns = np.array([0.1, 0.15, 0.08])
        covariance_matrix = np.array([
            [0.01, 0.002, 0.001],
            [0.002, 0.015, 0.003],
            [0.001, 0.003, 0.012]
        ])
        
        qubo = create_detailed_qubo_formulation(
            expected_returns, covariance_matrix, n_discrete_levels=5
        )
        
        # Check structure
        self.assertEqual(qubo['n_assets'], n_assets)
        self.assertEqual(qubo['n_levels'], 5)
        self.assertEqual(qubo['total_variables'], n_assets * 5)
        self.assertEqual(qubo['Q_matrix'].shape, (15, 15))
        self.assertEqual(len(qubo['weight_levels']), 5)
        self.assertEqual(len(qubo['variable_mapping']), 15)
    
    def test_qubo_weight_levels(self):
        """Test that weight levels are correctly generated"""
        expected_returns = np.array([0.1, 0.15])
        covariance_matrix = np.array([[0.01, 0.002], [0.002, 0.015]])
        
        qubo = create_detailed_qubo_formulation(
            expected_returns, covariance_matrix, n_discrete_levels=10
        )
        
        weight_levels = qubo['weight_levels']
        self.assertEqual(len(weight_levels), 10)
        self.assertAlmostEqual(weight_levels[0], 0.0)
        self.assertAlmostEqual(weight_levels[-1], 0.5)
    
    def test_variable_mapping(self):
        """Test variable mapping creation"""
        mapping = _create_variable_mapping(n_assets=3, n_levels=4)
        
        # Check total number of variables
        self.assertEqual(len(mapping), 12)
        
        # Check first and last mappings
        self.assertEqual(mapping[0], (0, 0))
        self.assertEqual(mapping[3], (0, 3))
        self.assertEqual(mapping[4], (1, 0))
        self.assertEqual(mapping[11], (2, 3))


class TestQuantumSolutionDecoding(unittest.TestCase):
    """Test quantum solution decoding and validation"""
    
    def test_decode_quantum_solution(self):
        """Test decoding of binary quantum solution"""
        n_assets = 3
        n_levels = 5
        weight_levels = np.linspace(0, 0.5, n_levels)
        
        # Create mapping
        mapping = _create_variable_mapping(n_assets, n_levels)
        
        # Create a binary solution: asset 0 gets level 2, asset 1 gets level 3, asset 2 gets level 1
        binary_solution = {2: 1, 8: 1, 11: 1}  # Indices for those selections
        
        weights = _decode_quantum_solution(
            binary_solution, mapping, n_assets, n_levels, weight_levels
        )
        
        # Verify weights are normalized
        self.assertAlmostEqual(weights.sum(), 1.0, places=5)
        self.assertEqual(len(weights), n_assets)
    
    def test_validate_quantum_solution_valid(self):
        """Test validation of valid quantum solution"""
        weights = np.array([0.3, 0.4, 0.3])
        self.assertTrue(_validate_quantum_solution(weights))
    
    def test_validate_quantum_solution_invalid_sum(self):
        """Test validation fails when weights don't sum to 1"""
        weights = np.array([0.3, 0.4, 0.2])  # Sums to 0.9
        self.assertFalse(_validate_quantum_solution(weights))
    
    def test_validate_quantum_solution_negative(self):
        """Test validation fails with negative weights"""
        weights = np.array([0.5, 0.6, -0.1])
        self.assertFalse(_validate_quantum_solution(weights))
    
    def test_validate_quantum_solution_exceeds_limit(self):
        """Test validation fails when weight exceeds limit"""
        weights = np.array([0.6, 0.3, 0.1])
        self.assertFalse(_validate_quantum_solution(weights))


class TestOptimizeWithFallback(unittest.TestCase):
    """Test optimization with fallback mechanism"""
    
    def test_fallback_to_classical(self):
        """Test that fallback to classical works when quantum unavailable"""
        expected_returns = np.array([0.1, 0.15, 0.08])
        covariance_matrix = np.array([
            [0.01, 0.002, 0.001],
            [0.002, 0.015, 0.003],
            [0.001, 0.003, 0.012]
        ])
        current_weights = np.array([0.33, 0.33, 0.34])
        
        # Test with quantum_available=False
        weights, method = optimize_with_fallback(
            expected_returns,
            covariance_matrix,
            current_weights,
            risk_aversion=1.0,
            quantum_available=False
        )
        
        # Should fallback to classical
        self.assertIn(method, ["classical_cvxpy", "equal_weights_fallback"])
        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(weights.sum(), 1.0, places=5)
    
    def test_equal_weights_fallback(self):
        """Test that system can handle edge cases gracefully"""
        # Create valid inputs for optimization
        expected_returns = np.array([0.1, 0.15, 0.08])
        covariance_matrix = np.array([
            [0.01, 0.002, 0.001],
            [0.002, 0.015, 0.003],
            [0.001, 0.003, 0.012]
        ])
        current_weights = np.array([0.33, 0.33, 0.34])
        
        weights, method = optimize_with_fallback(
            expected_returns,
            covariance_matrix,
            current_weights,
            risk_aversion=1.0,
            quantum_available=False
        )
        
        # Should have valid weights
        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(weights.sum(), 1.0, places=5)
        # Method should be classical since quantum is not available
        self.assertIn(method, ["classical_cvxpy", "equal_weights_fallback"])


class TestOptimizationMetrics(unittest.TestCase):
    """Test optimization metrics tracking"""
    
    def test_optimization_metrics_creation(self):
        """Test OptimizationMetrics dataclass creation"""
        metrics = OptimizationMetrics(
            method="quantum_dwave",
            solve_time_seconds=0.5,
            final_portfolio_value=10500.0,
            sharpe_ratio=1.5,
            max_drawdown=-0.15,
            constraint_violations=0
        )
        
        self.assertEqual(metrics.method, "quantum_dwave")
        self.assertEqual(metrics.solve_time_seconds, 0.5)
        self.assertEqual(metrics.final_portfolio_value, 10500.0)


class TestPerformanceTracker(unittest.TestCase):
    """Test performance tracking functionality"""
    
    def test_performance_tracker_initialization(self):
        """Test PerformanceTracker initialization"""
        tracker = PerformanceTracker()
        self.assertEqual(len(tracker.metrics_history), 0)
    
    def test_log_optimization(self):
        """Test logging optimization metrics"""
        tracker = PerformanceTracker()
        
        # Create sample returns
        returns = pd.Series([0.01, -0.005, 0.015, 0.02, -0.01] * 50)
        
        tracker.log_optimization(
            method="classical_cvxpy",
            solve_time=0.1,
            portfolio_value=10500.0,
            returns=returns
        )
        
        self.assertEqual(len(tracker.metrics_history), 1)
        self.assertEqual(tracker.metrics_history[0].method, "classical_cvxpy")
    
    def test_get_method_comparison(self):
        """Test method comparison generation"""
        tracker = PerformanceTracker()
        
        # Add some metrics
        returns1 = pd.Series([0.01, -0.005, 0.015] * 30)
        returns2 = pd.Series([0.008, -0.003, 0.012] * 30)
        
        tracker.log_optimization("classical_cvxpy", 0.1, 10500.0, returns1)
        tracker.log_optimization("quantum_dwave", 0.5, 10600.0, returns2)
        tracker.log_optimization("classical_cvxpy", 0.12, 10520.0, returns1)
        
        comparison = tracker.get_method_comparison()
        
        # Should have 2 methods
        self.assertEqual(len(comparison), 2)
        self.assertIn('classical_cvxpy', comparison.index)
        self.assertIn('quantum_dwave', comparison.index)
    
    def test_calculate_max_drawdown(self):
        """Test max drawdown calculation"""
        tracker = PerformanceTracker()
        
        # Create returns with known drawdown
        returns = pd.Series([0.1, -0.2, 0.05, -0.1, 0.15])
        
        max_dd = tracker._calculate_max_drawdown(returns)
        
        # Drawdown should be negative
        self.assertLess(max_dd, 0)


if __name__ == '__main__':
    unittest.main()
