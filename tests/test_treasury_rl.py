"""Tests for treasury RL environment and policy."""
import unittest
import numpy as np
import os
from treasury.rl.env import TreasuryEnv
from treasury.rl.policy import TreasuryPolicy


class TestTreasuryEnv(unittest.TestCase):
    """Test treasury RL environment."""
    
    def test_env_initialization(self):
        """Test environment initialization."""
        env = TreasuryEnv(n_assets=4)
        
        self.assertEqual(env.n_assets, 4)
        self.assertEqual(env.min_coverage, 1.30)
        self.assertEqual(env.state_dim, 6)  # 4 weights + coverage + volatility
        self.assertEqual(env.action_dim, 4)
    
    def test_reset(self):
        """Test environment reset."""
        env = TreasuryEnv()
        state = env.reset()
        
        self.assertEqual(len(state), 6)
        # Check weights sum to 1
        weights = state[:4]
        self.assertAlmostEqual(weights.sum(), 1.0, places=5)
    
    def test_step(self):
        """Test environment step."""
        env = TreasuryEnv()
        state = env.reset()
        
        action = np.array([0.01, -0.01, 0.005, -0.005])
        next_state, reward, done, info = env.step(action)
        
        self.assertEqual(len(next_state), 6)
        self.assertIsInstance(reward, float)
        self.assertIsInstance(done, bool)
        self.assertIn('coverage_ratio', info)
    
    def test_shielded_action(self):
        """Test that actions are shielded to satisfy constraints."""
        env = TreasuryEnv()
        state = env.reset()
        
        # Try extreme action
        extreme_action = np.array([1.0, -1.0, 0.5, -0.5])
        next_state, reward, done, info = env.step(extreme_action)
        
        # Weights should still be valid
        weights = next_state[:4]
        self.assertAlmostEqual(weights.sum(), 1.0, places=5)
        self.assertTrue(all(w >= 0 for w in weights))
        self.assertTrue(all(w <= env.max_weight for w in weights))
    
    def test_coverage_ratio_violation(self):
        """Test that low coverage ratio terminates episode."""
        env = TreasuryEnv()
        state = env.reset()
        
        # Force coverage below minimum
        env.state[4] = 1.20  # Below min_coverage of 1.30
        
        action = np.zeros(4)
        next_state, reward, done, info = env.step(action)
        
        # Should trigger done due to constraint violation
        self.assertTrue(info['constraint_violated'])
    
    def test_reward_calculation(self):
        """Test reward calculation components."""
        env = TreasuryEnv()
        state = env.reset()
        
        # Small positive action
        action = np.array([0.01, 0.01, -0.01, -0.01])
        next_state, reward, done, info = env.step(action)
        
        # Reward should be finite
        self.assertTrue(np.isfinite(reward))


class TestTreasuryPolicy(unittest.TestCase):
    """Test treasury policy."""
    
    def test_policy_initialization(self):
        """Test policy initialization."""
        policy = TreasuryPolicy()
        self.assertFalse(policy.use_rl)
    
    def test_select_action_disabled(self):
        """Test action selection when RL is disabled."""
        policy = TreasuryPolicy()
        state = np.random.randn(6)
        
        action = policy.select_action(state)
        
        # Should return zeros when RL is disabled
        self.assertEqual(len(action), 4)
        np.testing.assert_array_equal(action, np.zeros(4))
    
    def test_select_action_enabled(self):
        """Test action selection when RL is enabled."""
        # Temporarily enable RL
        os.environ['USE_RL'] = 'true'
        
        try:
            policy = TreasuryPolicy()
            self.assertTrue(policy.use_rl)
            
            state = np.random.randn(6)
            action = policy.select_action(state)
            
            # Should return non-zero action
            self.assertEqual(len(action), 4)
            # Action should be small
            self.assertTrue(all(abs(a) < 0.1 for a in action))
        finally:
            # Clean up
            os.environ['USE_RL'] = 'false'


if __name__ == '__main__':
    unittest.main()
