# AlphaShield RL: Self-Optimizing, Ethics-Aligned Learning

## Overview

The AlphaShield RL module adds self-improving capabilities to the multi-agent system through:

- **Per-agent contextual bandits** for fast personalization (learns thresholds, allocations, and action choices for each user)
- **Cross-agent evolutionary search** (CMA-ES-style) over shared hyper-parameters each night
- **Unified reward shaping** that multiplies profitability × ethics × calibration × user satisfaction and penalizes risk/compliance breaches
- **Memory-first training**: experiences/logs in MongoDB; contexts embedded via Voyage for retrieval-augmented learning

## Architecture

### Training Loop

```
[Context Builder] → [Bandit Suggest] → [Agent Action] → [Metrics Collection] → [Reward Computation] → [Bandit Update] → [Replay Buffer]
                                                                                                                              ↓
                                            [Nightly: Evolutionary Search] ← [Sample Experiences] ←────────────────────────┘
                                                         ↓
                                            [New Global Policy/Config]
```

### Flow Diagram

```
┌─────────────────┐
│  User Decision  │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────┐
│            1. Build Context                             │
│  - Agent name, user ID, time features                   │
│  - Decision inputs (amount, rate, term)                 │
│  - Recent metrics (coverage, risk, satisfaction)        │
│  - Memory hits from semantic search                     │
└────────┬────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────┐
│        2. Bandit Suggests Action                        │
│  LinUCB: action = argmax(μ + α√(x^T A^{-1} x))         │
└────────┬────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────┐
│           3. Execute Agent Decision                     │
│  - Agent processes input with suggested action          │
│  - Returns decision output                              │
└────────┬────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────┐
│         4. Collect Metrics & Compute Reward             │
│  R = G·Q·(αW + βC + γF + δS - λ₁D - λ₂A - λ₃T)        │
│  where:                                                 │
│    G = ethics gate (0 if violations, else 1)           │
│    Q = calibration multiplier [0.8, 1.2]               │
│    W = wealth delta, C = coverage ratio                │
│    F = fairness, S = satisfaction                       │
│    D = drawdown, A = anomaly, T = tax risk              │
└────────┬────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────┐
│          5. Update Bandit Parameters                    │
│  A_a ← A_a + xx^T                                       │
│  b_a ← b_a + rx                                         │
└────────┬────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────┐
│          6. Store Experience in Replay                  │
│  MongoDB: {ts, user_id, agent, context, action,         │
│            metrics, reward, policy_version}             │
└─────────────────────────────────────────────────────────┘

         [Nightly Meta-Optimization]
                    ↓
┌─────────────────────────────────────────────────────────┐
│    Evolutionary Search Over Reward Weights              │
│  - Sample experiences from last N days                  │
│  - Evolve population of reward configs                  │
│  - Fitness = avg_reward - volatility - fairness_penalty │
│  - Update global config if improvement found            │
└─────────────────────────────────────────────────────────┘
```

## Reward Function

The reward function is bounded, explainable, and ethics-aligned:

**Formula:**
```
R = G · Q · (αW + βC + γF + δS - (λ₁D + λ₂A + λ₃T))
```

**Components:**
- **G** (Gate): 0 if fairness < 0.50 OR compliance fails, else 1
- **Q** (Calibration): confidence calibration multiplier, clamped to [0.8, 1.2]
- **W** (Wealth): wealth delta normalized to [0, 1]
- **C** (Coverage): coverage ratio normalized: `min(1, max(0, (C - 1.2) / 0.6))`
- **F** (Fairness): fairness score [0, 1]
- **S** (Satisfaction): user satisfaction [0, 1]
- **D** (Drawdown): peak-to-trough penalty [0, 1]
- **A** (Anomaly): spending anomaly penalty [0, 1]
- **T** (Tax Risk): tax risk penalty [0, 1]

**Default Weights** (configurable in `config/rl.yaml`):
```yaml
alpha: 0.40    # wealth
beta: 0.15     # coverage
gamma: 0.15    # fairness
delta: 0.10    # satisfaction
lambda1: 0.10  # drawdown penalty
lambda2: 0.05  # anomaly penalty
lambda3: 0.05  # tax risk penalty
```

**Hard Stops** (G = 0):
- Fairness score < 0.50
- Compliance violation
- APR exceeds cap (agent-specific)
- Contract clause violations

## Components

### 1. Contextual Bandits (`bandit.py`)

**LinUCB Algorithm:**
- Maintains per-action matrices A (d×d) and vectors b (d×1)
- Upper Confidence Bound: `UCB = x^T θ + α√(x^T A^{-1} x)`
- Balances exploration (uncertainty) and exploitation (mean reward)

**Action Spaces per Agent:**
- **Lender**: 9 actions (approve variants, revise, deny, defer)
- **AlphaTrading**: 5 actions (allocation strategies)
- **SpendingGuard**: 4 actions (no alert, soft/strong warning, block)
- **BudgetAnalyzer**: 5 actions (no changes, minor/major adjustments, emergency, savings)
- **TaxOptimizer**: 4 actions (standard, itemized, retirement, aggressive)
- **ContractReview**: 3 actions (approve, revise, reject)

### 2. Context Builder (`context.py`)

**Feature Vector** (13 dimensions):
1. Agent hash (normalized)
2. User hash (anonymized)
3. Hour of day [0, 1]
4. Day of week [0, 1]
5. Log-scaled amount
6. Interest rate / 100
7. Term / 60 months
8. Coverage ratio / 2
9. Risk score [0, 1]
10. Satisfaction [0, 1]
11. Memory hit count / 10
12. Average memory similarity
13. (Reserved for future use)

### 3. Replay Buffer (`replay.py`)

**MongoDB Schema:**
```javascript
{
  ts: ISODate,
  user_id: String,
  agent: String,
  context: [Float],       // 13-dim feature vector
  action: Int,
  metrics: {              // raw metrics
    wealth_delta: Float,
    coverage_ratio: Float,
    fairness: Float,
    // ...
  },
  reward: Float,
  policy_version: Int
}
```

**Operations:**
- `append()`: Store new experience
- `sample()`: Random sampling for training
- `get_recent()`: Latest experiences for user/agent
- `get_statistics()`: Aggregate metrics
- `cleanup_old_experiences()`: Rolling retention (default 90 days)

### 4. Policy Manager (`policy.py`)

**Policy Object:**
```python
@dataclass
class Policy:
    agent: str
    algo: str              # 'LinUCB', 'ThompsonSampling'
    version: int
    created_at: str        # ISO timestamp
    params: dict           # A, b matrices for LinUCB
    metadata: dict         # fitness, performance metrics
```

**Operations:**
- `save_policy()`: Persist to MongoDB
- `load_policy()`: Load by agent + version
- `bump_version()`: Create new version on improvement
- `list_versions()`: Recent versions for rollback

### 5. Evolutionary Search (`evolution.py`)

**(μ, λ) Evolution Strategy:**
1. Initialize population around current config
2. Evaluate fitness for each candidate
3. Select top 30% as elites
4. Generate offspring via crossover + Gaussian mutation
5. Repeat for N generations or until convergence

**Fitness Function:**
```python
fitness = avg_reward - 0.5 * volatility - 2.0 * fairness_penalty
```

**Bounds for Reward Weights:**
```yaml
alpha: [0.2, 0.6]      # wealth
beta: [0.05, 0.25]     # coverage
gamma: [0.05, 0.25]    # fairness
delta: [0.05, 0.20]    # satisfaction
lambda1: [0.05, 0.20]  # drawdown
lambda2: [0.0, 0.10]   # anomaly
lambda3: [0.0, 0.10]   # tax risk
```

### 6. Trainer (`trainer.py`)

**Main Loop:**
```python
def train_step(agent_name, user_id, decision_input, agent_output, recent_metrics):
    # 1. Build context
    context = build_context(...)
    
    # 2. Get bandit and suggest action
    bandit = get_bandit(agent_name)
    action = bandit.suggest_action(context)
    
    # 3. Extract or mock metrics
    metrics = extract_metrics(agent_output, recent_metrics)
    
    # 4. Compute reward
    reward = compute_reward(metrics, reward_config)
    
    # 5. Update bandit
    bandit.update(context, action, reward)
    
    # 6. Store experience
    replay.append(user_id, agent_name, context, action, metrics, reward, policy_version)
    
    return {'action': action, 'reward': reward, 'policy_version': policy_version}
```

**Nightly Meta-Optimization:**
```python
def nightly_meta_optimization():
    # 1. Sample experiences from last N days
    experiences = replay.sample(n=1000, recent_days=30)
    
    # 2. Run evolutionary search
    optimized_config = optimize_reward_weights(replay, base_config)
    
    # 3. Evaluate improvement
    if optimized_fitness > baseline_fitness + epsilon:
        reward_config.update(optimized_config)
        policy_manager.bump_version(...)
```

### 7. Orchestration Hooks (`orchestration/rl_hooks.py`)

**RLOrchestrator:**
- `wrap_agent_decide()`: Wraps agent decision with RL training
- `get_suggested_action()`: Pre-decision RL suggestion
- `run_nightly_optimization()`: Scheduled meta-optimization
- `get_statistics()`: Training metrics

**Usage:**
```python
rl = RLOrchestrator(db_client, mock_mode=False)

# Wrap agent decision
result = rl.wrap_agent_decide(
    agent=lender_agent,
    user_id='user123',
    decision_input={'amount': 10000, 'rate': 8.0},
    recent_metrics={'coverage_ratio': 1.5, 'risk_score': 0.3}
)

# result now includes 'rl' field with action, reward, policy_version
```

## Configuration

**File:** `config/rl.yaml`

Key sections:
- `reward`: Weight configuration
- `bandit`: Algorithm parameters (alpha, reg)
- `horizons`: Time windows (eval, retention)
- `exploration`: Epsilon, temperature
- `evolution`: Meta-optimization settings
- `agents`: Per-agent action spaces

## Safety & Alignment

### Ethics Gate
- **Zero reward** on violations (fairness < 0.5, compliance fail)
- Agents default to conservative actions when uncertain
- Contract violations immediately flagged

### Confidence Calibration
- Reward scaled by model calibration (Brier score / NLL)
- Poor calibration reduces effective reward
- Encourages accurate confidence estimates

### Explainability
- All experiences stored with metrics and context
- Action spaces human-readable
- Reward decomposition visible (components logged)
- Policy versions allow rollback

### Rollback Support
- All policy versions persisted
- Can pin/rollback per user
- Gradual rollout of new policies

## Testing

### Unit Tests

**`tests/rl/test_bandit_update.py`:**
- Simulated linear reward environment
- Verifies LinUCB beats random policy
- Convergence to best action
- Numerical stability

**`tests/rl/test_reward.py`:**
- Fairness and compliance gates
- Reward component scaling
- Zero reward on violations

**`tests/rl/test_replay_and_policy_io.py`:**
- In-memory replay buffer
- Policy serialization round-trip
- Version management

### Running Tests

```bash
pytest tests/rl/ -v
```

## Demo Mode

**Activate mock mode:**
```python
rl = RLOrchestrator(db_client, mock_mode=True)
```

**Mock Feedback:**
- Better actions → higher metrics
- Gaussian noise for realism
- Compliance failures at low action quality

**Demo Output:**
- Reward components over time
- Action distribution shifts (personalization)
- Fairness gate activity
- Policy improvement tracking

## Performance

### Per-Decision Overhead
- Context building: ~1ms
- Bandit suggestion: ~2ms (matrix operations)
- Reward computation: <1ms
- Replay storage: ~5ms (MongoDB write)
- **Total**: ~10ms per decision

### Nightly Meta-Optimization
- Evolution (20 pop, 30 gen): ~2-5 minutes
- Depends on replay buffer size
- Scheduled at 2 AM (configurable)

### Scalability
- Bandits are per-agent (not per-user) → O(agents)
- Replay buffer sharded by user_id
- MongoDB indexes on agent, ts, user_id
- Policy versions O(100s) max

## Integration Examples

### Example 1: Lender with RL

```python
from alphashield.orchestration.rl_hooks import RLOrchestrator
from alphashield.agents.lender_agent import LenderAgent

rl = RLOrchestrator(db_client)
lender = LenderAgent(db_client)

result = rl.wrap_agent_decide(
    agent=lender,
    user_id='borrower_123',
    decision_input={
        'borrower_id': 'borrower_123',
        'principal': 10000,
        'interest_rate': 8.0,
        'term_months': 36
    },
    recent_metrics={
        'coverage_ratio': 1.4,
        'risk_score': 0.25,
        'satisfaction': 0.75
    }
)

print(f"RL Action: {result['rl']['action']}")
print(f"RL Reward: {result['rl']['reward']:.3f}")
```

### Example 2: Nightly Optimization

```python
# Run as scheduled job (e.g., cron)
results = rl.run_nightly_optimization(n_days=30, max_generations=30)

if results['improved']:
    print(f"Fitness improved: {results['baseline_fitness']:.3f} → {results['optimized_fitness']:.3f}")
    print(f"New config: {results['new_config']}")
else:
    print("No improvement found, keeping current config")
```

### Example 3: Statistics Dashboard

```python
# Overall statistics
stats = rl.get_statistics(days=7)
print(f"Active agents: {stats['agents_active']}")
print(f"Avg reward (7d): {stats['avg_reward']:.3f}")

# Per-agent statistics
lender_stats = rl.get_statistics(agent='Lender', days=7)
print(f"Lender experiences: {lender_stats['count']}")
print(f"Lender avg reward: {lender_stats['avg_reward']:.3f}")
```

## Future Enhancements

1. **Thompson Sampling**: Alternative to LinUCB with Bayesian inference
2. **Multi-objective optimization**: Pareto frontier for competing objectives
3. **Transfer learning**: Share parameters across similar agents
4. **Counterfactual evaluation**: Off-policy evaluation for safer updates
5. **Contextual embeddings**: Use Voyage embeddings directly as features
6. **Adaptive exploration**: Dynamic alpha based on uncertainty
7. **Hierarchical RL**: Meta-policies over agent policies

## References

- **LinUCB**: Li et al. "A Contextual-Bandit Approach to Personalized News Article Recommendation" (WWW 2010)
- **Evolutionary Strategies**: Hansen "The CMA Evolution Strategy" (2016)
- **Reward Shaping**: Ng et al. "Policy Invariance Under Reward Transformations" (ICML 1999)
- **Ethics-Aligned AI**: IEEE "Ethically Aligned Design" (2019)

---

**Questions?** See `config/rl.yaml` for all tunable parameters or run `python demo.py --mock` for interactive demo.
