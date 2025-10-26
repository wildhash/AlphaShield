"""Tests for treasury QUBO optimizer."""
import unittest
import numpy as np
import os
from treasury.optimizer_qubo import build_qubo, solve_qubo, decode_solution


class TestQUBOBuilder(unittest.TestCase):
    """Test QUBO formulation."""
    
    def test_build_qubo(self):
        """Test building QUBO from portfolio parameters."""
        mu = np.array([0.05, 0.08, 0.10, 0.12])
        Sigma = np.array([
            [0.01, 0.005, 0.003, 0.002],
            [0.005, 0.02, 0.006, 0.004],
            [0.003, 0.006, 0.03, 0.008],
            [0.002, 0.004, 0.008, 0.04]
        ])
        
        Q, penalty = build_qubo(mu, Sigma, levels=5)
        
        # Q should be a dict
        self.assertIsInstance(Q, dict)
        self.assertGreater(len(Q), 0)
        
        # Penalty should be positive
        self.assertGreater(penalty, 0)
    
    def test_qubo_structure(self):
        """Test QUBO has correct structure."""
        mu = np.array([0.05, 0.08])
        Sigma = np.array([[0.01, 0.005], [0.005, 0.02]])
        
        Q, _ = build_qubo(mu, Sigma, levels=3)
        
        # All keys should be tuples of ints
        for key in Q.keys():
            self.assertIsInstance(key, tuple)
            self.assertEqual(len(key), 2)
            self.assertIsInstance(key[0], int)
            self.assertIsInstance(key[1], int)
            # First element should be <= second element
            self.assertLessEqual(key[0], key[1])


class TestQUBOSolver(unittest.TestCase):
    """Test QUBO solver."""
    
    def test_solve_qubo_disabled(self):
        """Test QUBO solver when quantum is disabled."""
        Q = {(0, 0): 1.0, (0, 1): 0.5, (1, 1): 1.0}
        
        weights = solve_qubo(Q, penalty=10.0)
        
        # Should return None when QUANTUM is disabled
        self.assertIsNone(weights)
    
    def test_solve_qubo_enabled_no_dwave(self):
        """Test QUBO solver when quantum enabled but D-Wave not available."""
        os.environ['QUANTUM'] = 'true'
        
        try:
            Q = {(0, 0): 1.0, (0, 1): 0.5, (1, 1): 1.0}
            weights = solve_qubo(Q, penalty=10.0)
            
            # Should return None due to missing D-Wave
            self.assertIsNone(weights)
        finally:
            os.environ['QUANTUM'] = 'false'


class TestSolutionDecoder(unittest.TestCase):
    """Test solution decoder."""
    
    def test_decode_solution(self):
        """Test decoding binary solution to weights."""
        # Simple solution: asset 0 has bits [0,1] set, asset 1 has bit [0] set
        solution = {
            0: 1, 1: 1, 2: 0, 3: 0, 4: 0,  # Asset 0: levels 0,1
            5: 1, 6: 0, 7: 0, 8: 0, 9: 0,  # Asset 1: level 0
        }
        
        weights = decode_solution(solution, levels=5, n_assets=2)
        
        self.assertEqual(len(weights), 2)
        # Weights should sum to 1
        self.assertAlmostEqual(weights.sum(), 1.0, places=5)
        # All weights should be non-negative
        self.assertTrue(all(w >= 0 for w in weights))
    
    def test_decode_empty_solution(self):
        """Test decoding empty solution returns equal weights."""
        solution = {}
        
        weights = decode_solution(solution, levels=5, n_assets=4)
        
        self.assertEqual(len(weights), 4)
        # Should return equal weights
        np.testing.assert_array_almost_equal(weights, np.ones(4) / 4)
    
    def test_decode_normalizes_weights(self):
        """Test that decoder normalizes weights."""
        # All bits set
        solution = {i: 1 for i in range(20)}  # 4 assets * 5 levels
        
        weights = decode_solution(solution, levels=5, n_assets=4)
        
        # Should still sum to 1
        self.assertAlmostEqual(weights.sum(), 1.0, places=5)


if __name__ == '__main__':
    unittest.main()
