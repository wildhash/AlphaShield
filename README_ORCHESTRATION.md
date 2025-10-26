# AlphaShield Orchestration System

This document describes the orchestration system with shared context, learning hooks, and automated monitoring.

## Overview

The orchestration system provides:
- **Context Management**: Shared state across agents with capsule/packet pattern
- **Deterministic DAG**: Predictable workflow with audit trail
- **Treasury RL Hooks**: Reinforcement learning integration (optional)
- **Quantum Optimization**: QUBO formulation for quantum annealing (optional)
- **Spending Guard**: Automated anomaly detection with micro-refi triggers
- **End-to-End Testing**: Comprehensive test coverage with integration tests

## Architecture

### Context Management

**Capsule**: Aggregated financial context for a user
```python
from alphashield.context import build_financial_capsule

capsule = build_financial_capsule(
    user_id='user_123',
    db_client=db,
    embeddings_client=embeddings
)
# capsule.rolling_features: dict of aggregated metrics
# capsule.similar_case_ids: list of similar borrower IDs
```

**Packet**: Context passed through orchestration DAG
```python
from alphashield.context import make_packet

packet = make_packet('trace_id', 'user_id', 'loan_app_id')
packet.add_context('agent_name', {'result': 'data'})
data = packet.get_context('agent_name')
```

### Orchestrator Graph

Deterministic DAG execution with audit trail:

```
intake_doc & identity_fraud (parallel)
    ↓
underwriting
    ↓
optional contract_review (if low credit or short_term_relief)
    ↓
risk_bridge (portfolio optimization)
    ↓
offer
    ↓
compliance
```

**Usage:**
```python
from alphashield.orchestrator import execute

bundle = execute(
    trace_id='trace_123',
    user_id='user_456',
    loan_app_id='loan_789',
    db_client=db,
    short_term_relief=False
)

# Access results
print(bundle.underwriting)
print(bundle.coverage)
print(bundle.offer)
print(bundle.compliance)

# Audit trail
for event in bundle.audit_trail:
    print(f"{event['node']}: {event['status']}")
```

### Treasury RL Hooks

Gym-like environment for reinforcement learning:

```python
from treasury.rl.env import TreasuryEnv
from treasury.rl.policy import TreasuryPolicy

# Environment
env = TreasuryEnv(n_assets=4, min_coverage=1.30)
state = env.reset()

# Policy (stub by default)
policy = TreasuryPolicy()
action = policy.select_action(state)

# Step
next_state, reward, done, info = env.step(action)
```

**Features:**
- Shielded actions (automatically clip to constraints)
- Coverage ratio constraints enforced
- Configurable max weight and min cash
- Default: disabled (USE_RL=false)

### Quantum Optimization

QUBO formulation for quantum annealing:

```python
from treasury.optimizer_qubo import build_qubo, solve_qubo

# Build QUBO
mu = np.array([0.05, 0.08, 0.10, 0.12])
Sigma = np.array([[...]])  # covariance matrix

Q, penalty = build_qubo(mu, Sigma, levels=10)

# Solve (returns None if QUANTUM=false or D-Wave unavailable)
weights = solve_qubo(Q, penalty, num_reads=1000)
```

**Features:**
- Discretizes weights into binary variables
- Encodes constraints as penalties
- Falls back to classical QP if unavailable
- Default: disabled (QUANTUM=false)

### Spending Guard

MAD/STL-based anomaly detection:

```python
from alphashield.agents.spending_guard.agent import SpendingGuardAgent

agent = SpendingGuardAgent(
    mad_threshold=3.0,
    high_severity_multiplier=5.0,
    critical_severity_multiplier=7.0
)

events = agent.analyze_transactions(transactions, user_baseline)

for event in events:
    if event.severity == 'critical':
        # Trigger micro-refi
        print(f"Action: {event.suggested_action}")
```

**Detection Methods:**
- MAD (Median Absolute Deviation) for outliers
- Velocity spike detection
- High-risk category monitoring

**Daily Runner:**
```bash
python jobs/guard_runner.py
```

## Configuration

Add to `.env`:

```bash
# Treasury RL
USE_RL=false
RL_LAMBDA=0.1

# Quantum Optimization
QUANTUM=false
DWAVE_API_TOKEN=your_token

# Risk Constraints
CR_FLOOR=1.30        # Minimum coverage ratio
MAX_WEIGHT=0.40      # Maximum single asset weight
MIN_CASH=0.05        # Minimum cash allocation
TURNOVER_CAP=0.20    # Maximum portfolio turnover

# Spending Guard
GUARD_MAD_THRESHOLD=3.0
GUARD_HIGH_MULTIPLIER=5.0
GUARD_CRITICAL_MULTIPLIER=7.0
```

## Running Tests

```bash
# All new tests
python -m unittest tests.test_context
python -m unittest tests.test_orchestrator_graph
python -m unittest tests.test_treasury_rl
python -m unittest tests.test_treasury_qubo
python -m unittest tests.test_spending_guard
python -m unittest tests.test_refi_integration

# Integration test (happy path)
python -m unittest tests.test_refi_integration.TestRefiHappyPath.test_refi_happy_path
```

## Demo

Run the demo to see the system in action:

```bash
python demo_orchestration.py
```

Output includes:
- Complete DAG execution with audit trail
- Underwriting results
- Portfolio allocation with coverage ratio
- Offer details
- Compliance checks
- Spending guard anomaly detection

## Agent Protocol

New agents should implement the `Agent[T_in, T_out]` protocol:

```python
from alphashield.agents.base import Agent
from alphashield.context.packet import ContextPacket

class MyAgent:
    def run(self, input: MyInput, ctx: ContextPacket) -> MyOutput:
        # Access shared context
        prior_data = ctx.get_context('other_agent')
        
        # Process
        result = self.process(input, prior_data)
        
        # Add to context
        ctx.add_context('my_agent', result)
        
        return result
```

## Security

- All actions are shielded to satisfy constraints
- Audit trail tracks all operations with input hashes
- Coverage ratio enforced at environment level
- Configurable thresholds prevent extreme allocations

## Performance

- **Tests**: 69 passing (new: 42, existing: 27)
- **Coverage**: Context, orchestrator, RL, quantum, guard
- **Integration**: End-to-end refi happy path validated

## Future Enhancements

1. **RL Training**: Train policy with historical data
2. **Quantum Integration**: Connect to D-Wave hardware
3. **STL Decomposition**: Add seasonal trend analysis
4. **Live Monitoring**: Real-time guard with streaming
5. **Multi-Agent RL**: Coordinate multiple agents with RL

## References

- Context pattern: Capsule/packet for shared state
- RL environment: OpenAI Gym-like interface
- QUBO: D-Wave Ocean SDK compatible
- MAD: Robust outlier detection
- Audit trail: Cryptographic hashing for integrity
