"""RL policy for treasury optimization."""
from typing import Optional
import numpy as np
import os


class TreasuryPolicy:
    """Stub policy for treasury optimization.
    
    Returns zeros by default (no RL adjustment).
    When USE_RL is enabled, this can be replaced with a trained policy.
    """
    
    def __init__(self):
        """Initialize policy."""
        self.use_rl = os.getenv('USE_RL', 'false').lower() == 'true'
    
    def select_action(self, state: np.ndarray) -> np.ndarray:
        """Select action based on current state.
        
        Args:
            state: Current state vector
            
        Returns:
            Action vector (zeros by default)
        """
        if not self.use_rl:
            # Return zeros - no RL adjustment
            return np.zeros(4)  # 4 assets
        
        # Stub implementation: return small random adjustments
        # In production, this would load a trained policy
        return np.random.randn(4) * 0.01
    
    def load_weights(self, path: str) -> None:
        """Load policy weights from file.
        
        Args:
            path: Path to policy weights file
        """
        # Stub for loading trained policy
        pass
    
    def save_weights(self, path: str) -> None:
        """Save policy weights to file.
        
        Args:
            path: Path to save policy weights
        """
        # Stub for saving trained policy
        pass
