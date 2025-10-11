# tests/rl/test_bandit_update.py
import math
import random
import numpy as np

# ---- Helper: Simulated linear environment with noise -------------------------
class LinearNoisyEnv:
    """
    K-armed contextual bandit with linear rewards:
        r = x^T theta_a + epsilon
    where each action a has its own hidden parameter vector theta_a.
    Context x is sampled ~ N(0, I) then normalized.
    Rewards are squashed into [0,1] for stability.
    """
    def __init__(self, n_actions: int, d: int, noise_std: float = 0.05, seed: int = 7):
        self.n_actions = n_actions
        self.d = d
        self.noise_std = noise_std
        self.rng = np.random.default_rng(seed)
        # Hidden true weights per action
        thetas = self.rng.normal(0, 1, size=(n_actions, d))
        # Normalize each to unit norm so dot products stay ~[-1,1]
        self.thetas = thetas / np.linalg.norm(thetas, axis=1, keepdims=True)

    def sample_context(self) -> np.ndarray:
        x = self.rng.normal(0, 1, size=(self.d,))
        # Normalize context too
        norm = np.linalg.norm(x)
        if norm > 0:
            x = x / norm
        return x.astype(np.float64)

    def reward(self, action: int, x: np.ndarray) -> float:
        mean = float(np.dot(self.thetas[action], x))
        noisy = mean + self.rng.normal(0, self.noise_std)
        # squash to [0,1]
        return 0.5 * (noisy + 1.0)

    def best_action(self, x: np.ndarray) -> int:
        scores = self.thetas @ x
        return int(np.argmax(scores))


# ---- Minimal import path for LinUCB (Copilot will fill the implementation) ---
from alphashield.rl.bandit import LinUCB  # type: ignore


# ---- Tests -------------------------------------------------------------------

def test_linucb_beats_random_policy():
    """
    LinUCB should accumulate higher reward than a random policy in a linear/noisy bandit.
    """
    rng = np.random.default_rng(42)
    n_actions, d = 4, 12
    env = LinearNoisyEnv(n_actions, d, noise_std=0.05, seed=123)

    # LinUCB with modest exploration
    linucb = LinUCB(n_actions=n_actions, d=d, alpha=0.4)

    T = 2000
    cum_linucb = 0.0
    cum_random = 0.0

    for t in range(T):
        x = env.sample_context()

        # LinUCB choose/update
        a = linucb.suggest_action(x)
        r = env.reward(a, x)
        linucb.update(x, a, r)
        cum_linucb += r

        # Random baseline on identical context (for fairness)
        a_rand = rng.integers(0, n_actions)
        r_rand = env.reward(int(a_rand), x)
        cum_random += r_rand

    # LinUCB should beat random by a healthy margin
    improvement = (cum_linucb - cum_random) / max(1.0, cum_random)
    assert improvement > 0.05, f"Expected >5% improvement, got {improvement:.3%}"


def test_linucb_converges_toward_best_action_short_horizon():
    """
    Over a shorter horizon, we don't require perfect convergence, but we do expect
    LinUCB to pick the oracle-best action more often than random guessing.
    """
    n_actions, d = 3, 8
    env = LinearNoisyEnv(n_actions, d, noise_std=0.08, seed=99)
    linucb = LinUCB(n_actions=n_actions, d=d, alpha=0.6)

    T = 600
    best_hits = 0
    for t in range(T):
        x = env.sample_context()
        a = linucb.suggest_action(x)
        r = env.reward(a, x)
        linucb.update(x, a, r)
        if a == env.best_action(x):
            best_hits += 1

    # Random chance would be ~1/n_actions; require a decent lift
    random_rate = 1.0 / n_actions
    hit_rate = best_hits / T
    assert hit_rate > random_rate + 0.15, f"Hit rate {hit_rate:.3f} not sufficiently above random {random_rate:.3f}"


def test_linucb_is_numerically_stable_with_zero_contexts():
    """
    Guard against numerical issues when context is near-zero.
    """
    n_actions, d = 2, 5
    linucb = LinUCB(n_actions=n_actions, d=d, alpha=0.5)

    x = np.zeros(d, dtype=np.float64)
    # Should still return a valid action and handle update() without NaNs
    a = linucb.suggest_action(x)
    r = 0.5
    linucb.update(x, a, r)

    # No exceptions; parameters should remain finite
    # (Implementation should expose a method to inspect A,b if desired; here we just sanity-call again)
    a2 = linucb.suggest_action(x)
    assert a in range(n_actions) and a2 in range(n_actions)
