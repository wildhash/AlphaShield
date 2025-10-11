# AlphaShield RL Module

Self-optimizing reinforcement learning module for personalized agent decisions.

## Quick Start

```python
from alphashield.orchestration.rl_hooks import RLOrchestrator

# Initialize (mock mode for testing)
rl = RLOrchestrator(db_client=None, mock_mode=True)

# Wrap agent decision
result = rl.wrap_agent_decide(
    agent=my_agent,
    user_id='user123',
    decision_input={'amount': 10000, 'rate': 8.0},
    recent_metrics={'coverage_ratio': 1.5, 'risk_score': 0.3}
)

# Access RL info
print(f"Action: {result['rl']['action']}")
print(f"Reward: {result['rl']['reward']:.3f}")
```

## Architecture

```
Context → Bandit → Agent → Metrics → Reward → Update → Replay
    ↓                                                      ↓
    └──────────── Nightly Evolution ←─────────────────────┘
```

## Components

### Bandit (`bandit.py`)
- **LinUCB**: Contextual bandit with upper confidence bounds
- Balances exploration and exploitation
- Per-action parameter tracking

### Context (`context.py`)
- 13-dimensional feature vectors
- Agent, user, time, metrics, memory
- Normalized for stability

### Reward (`reward.py`)
- Multi-objective: `R = G·Q·(αW + βC + γF + δS - penalties)`
- Ethics gates (G=0 on violations)
- Calibration scaling (Q)

### Replay (`replay.py`)
- MongoDB-backed experience storage
- 90-day retention
- Efficient sampling

### Policy (`policy.py`)
- Version management
- Rollback support
- Metadata tracking

### Evolution (`evolution.py`)
- Evolutionary search for meta-optimization
- (μ, λ) strategy
- Fitness = avg_reward - volatility - fairness_penalty

### Trainer (`trainer.py`)
- Coordinates training loop
- Handles metrics extraction
- Mock mode for testing

### Hooks (`orchestration/rl_hooks.py`)
- Integration with agents
- Statistics API
- Nightly optimization scheduler

## Configuration

Edit `config/rl.yaml`:

```yaml
reward:
  alpha: 0.40      # wealth weight
  beta: 0.15       # coverage weight
  gamma: 0.15      # fairness weight
  delta: 0.10      # satisfaction weight

bandit:
  alpha: 1.5       # exploration weight
  reg: 0.01        # regularization

evolution:
  population: 20
  max_generations: 30
```

## Testing

```bash
# Run all RL tests
pytest tests/rl/ -v

# Run demo
python demo_rl.py
```

## Safety Features

1. **Ethics Gates**: Zero reward on fairness < 0.5 or compliance failures
2. **Confidence Calibration**: Reward scaled by model accuracy
3. **Explainable Actions**: Human-readable action spaces
4. **Rollback Support**: All policy versions persisted
5. **Gradual Rollout**: Per-user policy pinning

## Action Spaces

- **Lender**: 9 actions (approve variants, revise, deny)
- **AlphaTrading**: 5 actions (allocation strategies)
- **SpendingGuard**: 4 actions (alert levels)
- **BudgetAnalyzer**: 5 actions (adjustment levels)
- **TaxOptimizer**: 4 actions (optimization strategies)
- **ContractReview**: 3 actions (approve, revise, reject)

## Performance

- Per-decision overhead: ~10ms
- Memory: O(agents × dimensions²)
- Nightly optimization: 2-5 minutes
- Scales horizontally (stateless bandits)

## Documentation

- Full overview: `docs/RL_OVERVIEW.md`
- API docs: See docstrings in each module
- Demo: `demo_rl.py`
- Tests: `tests/rl/`

## Example: Training Statistics

```python
# Get statistics
stats = rl.get_statistics(agent='Lender', days=7)
print(f"Experiences: {stats['count']}")
print(f"Avg reward: {stats['avg_reward']:.3f}")
print(f"Std reward: {stats['std_reward']:.3f}")
```

## Example: Nightly Optimization

```python
# Run meta-optimization
results = rl.run_nightly_optimization(n_days=30)
if results['improved']:
    print(f"New config: {results['new_config']}")
```

## Future Enhancements

- Thompson Sampling algorithm
- Multi-objective Pareto optimization
- Transfer learning across agents
- Contextual embeddings from Voyage
- Adaptive exploration

## License

Part of AlphaShield project.
