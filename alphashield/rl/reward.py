"""Reward shaping and normalization for AlphaShield RL.

Implements the composite reward function:
R = G * Q * (alpha*W + beta*C + gamma*F + delta*S - (lambda1*D + lambda2*A + lambda3*T))

Where:
- G: Compliance/Ethics gate (0 if violations, else 1)
- Q: Confidence calibration multiplier [0.8, 1.2]
- W: Wealth delta (normalized 0-1)
- C: Coverage ratio (normalized 0-1)
- F: Fairness score (0-1)
- S: User satisfaction (0-1)
- D: Drawdown penalty (0-1)
- A: Anomaly penalty (0-1)
- T: Tax risk penalty (0-1)
"""
from typing import Dict, Any, Optional
import numpy as np


def compute_reward(metrics: Dict[str, Any], config: Dict[str, float], 
                  min_fairness_threshold: float = 0.50) -> float:
    """Compute shaped reward from metrics.
    
    Parameters
    ----------
    metrics : dict
        Dictionary containing:
        - wealth_delta: float, normalized 0-1
        - coverage_ratio: float, raw coverage ratio
        - fairness: float, 0-1 score
        - satisfaction: float, 0-1 score
        - drawdown: float, 0-1 penalty
        - anomaly: float, 0-1 penalty
        - tax_risk: float, 0-1 penalty
        - calibration: float, typically ~1.0, range [0.8, 1.2]
        - compliance_ok: bool, True if compliant
    config : dict
        Reward weights:
        - alpha: wealth weight
        - beta: coverage weight
        - gamma: fairness weight
        - delta: satisfaction weight
        - lambda1: drawdown penalty weight
        - lambda2: anomaly penalty weight
        - lambda3: tax risk penalty weight
    min_fairness_threshold : float
        Minimum fairness score to avoid gate zeroing (default 0.50)
    
    Returns
    -------
    float
        Shaped reward value
    """
    # Extract metrics with defaults
    W = float(metrics.get('wealth_delta', 0.0))
    coverage_raw = float(metrics.get('coverage_ratio', 1.0))
    F = float(metrics.get('fairness', 1.0))
    S = float(metrics.get('satisfaction', 0.5))
    D = float(metrics.get('drawdown', 0.0))
    A = float(metrics.get('anomaly', 0.0))
    T = float(metrics.get('tax_risk', 0.0))
    Q = float(metrics.get('calibration', 1.0))
    compliance_ok = bool(metrics.get('compliance_ok', True))
    
    # Normalize coverage ratio: C' = min(1, max(0, (C - 1.2) / 0.6))
    # This maps 1.2 -> 0, 1.8 -> 1, with linear scaling
    C = min(1.0, max(0.0, (coverage_raw - 1.2) / 0.6))
    
    # Clamp calibration to [0.8, 1.2]
    Q = min(1.2, max(0.8, Q))
    
    # Extract weights from config
    alpha = config.get('alpha', 0.40)
    beta = config.get('beta', 0.15)
    gamma = config.get('gamma', 0.15)
    delta = config.get('delta', 0.10)
    lambda1 = config.get('lambda1', 0.10)
    lambda2 = config.get('lambda2', 0.05)
    lambda3 = config.get('lambda3', 0.05)
    
    # Compliance/Ethics gate: zero reward if violations
    G = 0.0 if (not compliance_ok or F < min_fairness_threshold) else 1.0
    
    # Compute shaped reward
    reward_core = (
        alpha * W + 
        beta * C + 
        gamma * F + 
        delta * S - 
        (lambda1 * D + lambda2 * A + lambda3 * T)
    )
    
    reward = G * Q * reward_core
    
    return reward


def normalize_wealth_delta(wealth_change: float, baseline: float = 0.0, 
                          window_min: float = -0.05, window_max: float = 0.15) -> float:
    """Normalize wealth delta to [0, 1] using min-max scaling.
    
    Parameters
    ----------
    wealth_change : float
        Raw wealth change (e.g., percentage change)
    baseline : float
        Baseline for comparison (default 0.0)
    window_min : float
        Minimum expected wealth change (default -5%)
    window_max : float
        Maximum expected wealth change (default 15%)
    
    Returns
    -------
    float
        Normalized wealth delta in [0, 1]
    """
    relative_change = wealth_change - baseline
    normalized = (relative_change - window_min) / (window_max - window_min)
    return float(np.clip(normalized, 0.0, 1.0))


def normalize_drawdown(drawdown_pct: float, max_drawdown: float = 0.20) -> float:
    """Normalize drawdown penalty to [0, 1].
    
    Parameters
    ----------
    drawdown_pct : float
        Peak-to-trough drawdown as percentage (e.g., 0.10 for 10%)
    max_drawdown : float
        Maximum expected drawdown (default 20%)
    
    Returns
    -------
    float
        Normalized drawdown penalty in [0, 1]
    """
    penalty = drawdown_pct / max_drawdown
    return float(np.clip(penalty, 0.0, 1.0))


class RewardConfig:
    """Configuration for reward computation."""
    
    def __init__(self, 
                 alpha: float = 0.40,
                 beta: float = 0.15,
                 gamma: float = 0.15,
                 delta: float = 0.10,
                 lambda1: float = 0.10,
                 lambda2: float = 0.05,
                 lambda3: float = 0.05,
                 min_fairness_threshold: float = 0.50):
        """Initialize reward configuration.
        
        Parameters
        ----------
        alpha : float
            Wealth weight (default 0.40)
        beta : float
            Coverage/affordability weight (default 0.15)
        gamma : float
            Fairness weight (default 0.15)
        delta : float
            Satisfaction weight (default 0.10)
        lambda1 : float
            Drawdown penalty weight (default 0.10)
        lambda2 : float
            Anomaly penalty weight (default 0.05)
        lambda3 : float
            Tax risk penalty weight (default 0.05)
        min_fairness_threshold : float
            Minimum fairness to avoid gate zeroing (default 0.50)
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.lambda1 = lambda1
        self.lambda2 = lambda2
        self.lambda3 = lambda3
        self.min_fairness_threshold = min_fairness_threshold
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for compute_reward."""
        return {
            'alpha': self.alpha,
            'beta': self.beta,
            'gamma': self.gamma,
            'delta': self.delta,
            'lambda1': self.lambda1,
            'lambda2': self.lambda2,
            'lambda3': self.lambda3,
        }
