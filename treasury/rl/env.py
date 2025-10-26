"""Gym-like RL environment for treasury optimization."""
from typing import Dict, Any, Tuple, Optional
import numpy as np


class TreasuryEnv:
    """Gym-like environment for treasury portfolio optimization with RL.
    
    State: portfolio weights, market conditions, coverage ratio
    Action: adjustment to portfolio weights
    Reward: based on coverage ratio, returns, and constraint satisfaction
    """
    
    def __init__(
        self,
        n_assets: int = 4,
        min_coverage: float = 1.30,
        max_weight: float = 0.40,
        min_cash: float = 0.05
    ):
        """Initialize treasury environment.
        
        Args:
            n_assets: Number of assets in portfolio
            min_coverage: Minimum coverage ratio constraint
            max_weight: Maximum weight per asset
            min_cash: Minimum cash allocation
        """
        self.n_assets = n_assets
        self.min_coverage = min_coverage
        self.max_weight = max_weight
        self.min_cash = min_cash
        
        # State: [weights(n_assets), coverage_ratio, market_volatility]
        self.state_dim = n_assets + 2
        # Action: weight adjustments for each asset
        self.action_dim = n_assets
        
        self.state = None
        self.reset()
    
    def reset(self) -> np.ndarray:
        """Reset environment to initial state.
        
        Returns:
            Initial state
        """
        # Start with equal weights
        initial_weights = np.ones(self.n_assets) / self.n_assets
        coverage_ratio = 1.35
        market_volatility = 0.15
        
        self.state = np.concatenate([
            initial_weights,
            [coverage_ratio, market_volatility]
        ])
        
        return self.state
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """Execute one step in the environment.
        
        Args:
            action: Weight adjustments (bounded and clipped)
            
        Returns:
            Tuple of (next_state, reward, done, info)
        """
        # Extract current state
        current_weights = self.state[:self.n_assets]
        coverage_ratio = self.state[self.n_assets]
        market_volatility = self.state[self.n_assets + 1]
        
        # Apply shielded action (clip to constraints)
        action = self._shield_action(action, current_weights)
        
        # Apply action to get new weights
        new_weights = current_weights + action
        new_weights = self._normalize_weights(new_weights)
        
        # Simulate portfolio return (simplified)
        expected_returns = np.array([0.05, 0.08, 0.10, 0.12])  # bonds, index, div, growth
        portfolio_return = np.dot(new_weights, expected_returns)
        
        # Simulate new coverage ratio
        new_coverage = coverage_ratio * (1 + portfolio_return * 0.1)
        
        # Calculate reward
        reward = self._calculate_reward(
            new_weights,
            new_coverage,
            portfolio_return
        )
        
        # Check if coverage ratio constraint is violated
        done = bool(new_coverage < self.min_coverage)
        
        # Update state
        self.state = np.concatenate([
            new_weights,
            [new_coverage, market_volatility]
        ])
        
        info = {
            'coverage_ratio': new_coverage,
            'portfolio_return': portfolio_return,
            'constraint_violated': done,
        }
        
        return self.state, reward, done, info
    
    def _shield_action(self, action: np.ndarray, current_weights: np.ndarray) -> np.ndarray:
        """Shield action to ensure constraints are satisfied.
        
        Clips actions that would violate:
        - Sum of weights = 1
        - Individual weights in [0, max_weight]
        - Minimum cash allocation
        
        Args:
            action: Proposed weight adjustments
            current_weights: Current portfolio weights
            
        Returns:
            Shielded action that satisfies constraints
        """
        # Clip action magnitude
        action = np.clip(action, -0.1, 0.1)
        
        # Predict new weights
        new_weights = current_weights + action
        
        # Ensure non-negative
        new_weights = np.maximum(new_weights, 0.0)
        
        # Ensure max weight constraint
        new_weights = np.minimum(new_weights, self.max_weight)
        
        # Ensure min cash (assuming first asset is cash/bonds)
        if new_weights[0] < self.min_cash:
            new_weights[0] = self.min_cash
        
        # Normalize to sum to 1
        new_weights = self._normalize_weights(new_weights)
        
        # Return the actual adjustment needed
        return new_weights - current_weights
    
    def _normalize_weights(self, weights: np.ndarray) -> np.ndarray:
        """Normalize weights to sum to 1.
        
        Args:
            weights: Portfolio weights
            
        Returns:
            Normalized weights
        """
        weight_sum = weights.sum()
        if weight_sum > 0:
            return weights / weight_sum
        return np.ones(self.n_assets) / self.n_assets
    
    def _calculate_reward(
        self,
        weights: np.ndarray,
        coverage_ratio: float,
        portfolio_return: float
    ) -> float:
        """Calculate reward for the current state.
        
        Reward components:
        - Portfolio return (positive)
        - Coverage ratio above minimum (bonus)
        - Constraint violations (penalty)
        
        Args:
            weights: Portfolio weights
            coverage_ratio: Current coverage ratio
            portfolio_return: Portfolio return
            
        Returns:
            Reward value
        """
        reward = 0.0
        
        # Reward for portfolio return
        reward += portfolio_return * 10.0
        
        # Bonus for coverage ratio above minimum
        if coverage_ratio >= self.min_coverage:
            reward += (coverage_ratio - self.min_coverage) * 5.0
        else:
            # Heavy penalty for violating coverage ratio
            reward -= (self.min_coverage - coverage_ratio) * 20.0
        
        # Penalty for extreme concentrations
        max_single_weight = weights.max()
        if max_single_weight > self.max_weight:
            reward -= (max_single_weight - self.max_weight) * 10.0
        
        return reward
