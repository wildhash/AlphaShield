# alphashield/rl/bandit.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from typing import Optional, Tuple

Array = np.ndarray


@dataclass
class LinUCBConfig:
    n_actions: int
    d: int                 # feature dimension
    alpha: float = 1.5     # exploration weight
    reg: float = 1e-2      # ridge regularization


class LinUCB:
    """
    Minimal LinUCB implementation.
    Keeps per-action A (dxd) and b (dx1) for linear reward model.
    UCB score: x^T theta_a + alpha * sqrt(x^T A_a^{-1} x)
    """
    def __init__(self, n_actions: int = None, d: int = None, alpha: float = 1.5, 
                 reg: float = 1e-2, cfg: Optional[LinUCBConfig] = None, 
                 rng: Optional[np.random.Generator] = None) -> None:
        """Initialize LinUCB bandit.
        
        Parameters
        ----------
        n_actions: Number of actions (required if cfg not provided)
        d: Feature dimension (required if cfg not provided)
        alpha: Exploration weight
        reg: Ridge regularization parameter
        cfg: LinUCBConfig object (overrides other parameters if provided)
        rng: Random number generator
        """
        if cfg is not None:
            self.cfg = cfg
        else:
            if n_actions is None or d is None:
                raise ValueError("Either cfg or both n_actions and d must be provided")
            self.cfg = LinUCBConfig(n_actions=n_actions, d=d, alpha=alpha, reg=reg)
        
        self.rng = rng or np.random.default_rng()
        d, k = self.cfg.d, self.cfg.n_actions
        self.A: Array = np.stack([np.eye(d) * self.cfg.reg for _ in range(k)])   # (k, d, d)
        self.b: Array = np.zeros((k, d))                                    # (k, d)
        # cached inverses (lazy)
        self._A_inv: Optional[Array] = None

    # ---------- utilities ----------
    def _ensure_inv(self) -> Array:
        if self._A_inv is None:
            # compute inverses for all actions
            self._A_inv = np.linalg.inv(self.A)    # (k, d, d)
        return self._A_inv

    def _invalidate_inv(self) -> None:
        self._A_inv = None

    def _theta(self) -> Array:
        # theta_a = A_a^{-1} b_a
        A_inv = self._ensure_inv()                 # (k, d, d)
        # (k,d,d) @ (k,d,1) -> (k,d)
        return np.einsum("kij,kj->ki", A_inv, self.b)

    # ---------- public API ----------
    def suggest_action(self, x: Array) -> int:
        """
        Parameters
        ----------
        x: shape (d,) feature vector

        Returns
        -------
        int: action index in [0, n_actions)
        """
        x = np.asarray(x).reshape(-1)
        assert x.shape[0] == self.cfg.d, f"expected x dim {self.cfg.d}, got {x.shape[0]}"

        A_inv = self._ensure_inv()                # (k, d, d)
        theta = self._theta()                     # (k, d)
        # mean: (k,)
        mean = np.einsum("kd,d->k", theta, x)
        # uncertainty: sqrt(x^T A_inv x) per action
        var = np.einsum("kij,i,j->k", A_inv, x, x)
        ucb = mean + self.cfg.alpha * np.sqrt(np.maximum(var, 1e-12))
        return int(np.argmax(ucb))

    def update(self, x: Array, action: int, reward: float) -> None:
        """
        Performs the standard LinUCB ridge update:
        A_a <- A_a + x x^T
        b_a <- b_a + r x
        """
        x = np.asarray(x).reshape(-1)
        assert 0 <= action < self.cfg.n_actions
        self.A[action] += np.outer(x, x)
        self.b[action] += reward * x
        self._invalidate_inv()

    # convenience (used by tests)
    def parameters(self, action: int) -> Tuple[Array, Array]:
        """Return (A_a, theta_a) for inspection."""
        theta = self._theta()
        return self.A[action], theta[action]
