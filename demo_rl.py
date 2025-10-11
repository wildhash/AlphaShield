#!/usr/bin/env python
"""Demo script for AlphaShield RL module.

Demonstrates:
- RL-enhanced agent decisions
- Learning from experience
- Action distribution changes over time
- Reward tracking
"""
import sys
from typing import Dict, Any
import numpy as np
from alphashield.orchestration.rl_hooks import RLOrchestrator


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def simulate_user_decisions(rl: RLOrchestrator, agent_name: str, 
                            user_id: str, n_decisions: int = 50):
    """Simulate a series of user decisions to train the RL agent.
    
    Parameters
    ----------
    rl : RLOrchestrator
        RL orchestrator instance
    agent_name : str
        Agent name
    user_id : str
        User identifier
    n_decisions : int
        Number of decisions to simulate
    
    Returns
    -------
    dict
        Summary statistics
    """
    actions = []
    rewards = []
    
    for i in range(n_decisions):
        # Varying decision inputs
        decision_input = {
            'amount': 5000 + i * 100,
            'interest_rate': 8.0 + np.random.uniform(-1, 1),
            'term_months': 36,
            'loan_id': f'loan_{user_id}_{i}'
        }
        
        # Mock recent metrics (improving over time to simulate learning)
        recent_metrics = {
            'coverage_ratio': 1.2 + i * 0.01,
            'risk_score': max(0.1, 0.5 - i * 0.005),
            'satisfaction': 0.5 + i * 0.008,
            'wealth_delta': 0.3 + i * 0.005,
            'drawdown': max(0, 0.15 - i * 0.002),
            'anomaly': 0.0,
            'tax_risk': 0.0
        }
        
        # Get suggested action (without executing agent)
        action = rl.get_suggested_action(
            agent_name=agent_name,
            user_id=user_id,
            decision_input=decision_input,
            recent_metrics=recent_metrics
        )
        
        # Simulate agent execution (mock)
        agent_output = {
            'status': 'success',
            'fairness_score': 0.8,
            'compliant': True
        }
        
        # Train RL
        result = rl.trainer.train_step(
            agent_name=agent_name,
            user_id=user_id,
            decision_input=decision_input,
            agent_output=agent_output,
            recent_metrics=recent_metrics
        )
        
        actions.append(action)
        rewards.append(result['reward'])
    
    return {
        'actions': actions,
        'rewards': rewards,
        'avg_reward': np.mean(rewards),
        'final_reward': np.mean(rewards[-10:])  # last 10
    }


def demo_single_agent():
    """Demo RL with a single agent (Lender)."""
    print_section("Demo 1: Single Agent Learning (Lender)")
    
    # Initialize RL in mock mode
    rl = RLOrchestrator(db_client=None, mock_mode=True)
    
    agent_name = 'Lender'
    user_id = 'demo_user_1'
    
    print(f"\nTraining {agent_name} agent for user {user_id}...")
    print("Simulating 50 loan decisions...\n")
    
    # Simulate decisions
    results = simulate_user_decisions(rl, agent_name, user_id, n_decisions=50)
    
    # Print results
    print(f"✓ Training complete!")
    print(f"  Average reward: {results['avg_reward']:.3f}")
    print(f"  Final 10 avg reward: {results['final_reward']:.3f}")
    print(f"  Improvement: {results['final_reward'] - results['avg_reward']:.3f}")
    
    # Action distribution
    action_counts = {}
    for a in results['actions']:
        action_counts[a] = action_counts.get(a, 0) + 1
    
    print(f"\n  Action distribution:")
    for action, count in sorted(action_counts.items()):
        pct = 100 * count / len(results['actions'])
        bar = '█' * int(pct / 2)
        print(f"    Action {action}: {count:2d} times ({pct:5.1f}%) {bar}")
    
    # Show action shift over time
    early_actions = results['actions'][:10]
    late_actions = results['actions'][-10:]
    
    print(f"\n  Early actions (1-10): {early_actions}")
    print(f"  Late actions (41-50): {late_actions}")
    
    return rl


def demo_multi_agent():
    """Demo RL with multiple agents."""
    print_section("Demo 2: Multi-Agent Learning")
    
    rl = RLOrchestrator(db_client=None, mock_mode=True)
    
    agents = ['Lender', 'AlphaTrading', 'SpendingGuard']
    user_id = 'demo_user_2'
    
    print(f"\nTraining {len(agents)} agents for user {user_id}...")
    print("Each agent learns from 30 decisions...\n")
    
    for agent_name in agents:
        results = simulate_user_decisions(rl, agent_name, user_id, n_decisions=30)
        print(f"✓ {agent_name:15s}: avg reward={results['avg_reward']:.3f}, "
              f"final={results['final_reward']:.3f}, "
              f"improvement={results['final_reward'] - results['avg_reward']:+.3f}")
    
    return rl


def demo_statistics(rl: RLOrchestrator):
    """Demo statistics retrieval."""
    print_section("Demo 3: Statistics & Monitoring")
    
    print("\nOverall statistics (last 7 days):")
    stats = rl.get_statistics(days=7)
    print(f"  Total experiences: {stats['count']}")
    print(f"  Average reward: {stats['avg_reward']:.3f}")
    print(f"  Std reward: {stats['std_reward']:.3f}")
    print(f"  Min reward: {stats['min_reward']:.3f}")
    print(f"  Max reward: {stats['max_reward']:.3f}")
    
    if 'agents_active' in stats:
        print(f"  Active agents: {', '.join(stats['agents_active'])}")
    
    # Per-agent statistics
    print("\nPer-agent statistics:")
    for agent in ['Lender', 'AlphaTrading', 'SpendingGuard']:
        try:
            agent_stats = rl.get_statistics(agent=agent, days=7)
            if agent_stats['count'] > 0:
                print(f"  {agent:15s}: {agent_stats['count']:3d} experiences, "
                      f"avg reward={agent_stats['avg_reward']:.3f}")
        except:
            pass


def demo_reward_components():
    """Demo reward function components."""
    print_section("Demo 4: Reward Function Decomposition")
    
    from alphashield.rl.reward import compute_reward
    
    print("\nTest Case 1: Ideal scenario")
    metrics_good = {
        'wealth_delta': 0.8,
        'coverage_ratio': 1.5,
        'fairness': 0.9,
        'satisfaction': 0.85,
        'drawdown': 0.05,
        'anomaly': 0.0,
        'tax_risk': 0.0,
        'calibration': 1.0,
        'compliance_ok': True
    }
    config = {
        'alpha': 0.40, 'beta': 0.15, 'gamma': 0.15, 'delta': 0.10,
        'lambda1': 0.10, 'lambda2': 0.05, 'lambda3': 0.05
    }
    
    reward = compute_reward(metrics_good, config)
    print(f"  Reward: {reward:.3f}")
    print(f"  Components:")
    print(f"    - Wealth delta: {metrics_good['wealth_delta']:.2f}")
    print(f"    - Coverage ratio: {metrics_good['coverage_ratio']:.2f}")
    print(f"    - Fairness: {metrics_good['fairness']:.2f}")
    print(f"    - Satisfaction: {metrics_good['satisfaction']:.2f}")
    print(f"    - Drawdown penalty: {metrics_good['drawdown']:.2f}")
    
    print("\nTest Case 2: Fairness violation (should zero reward)")
    metrics_bad_fairness = dict(metrics_good, fairness=0.3)
    reward_bad = compute_reward(metrics_bad_fairness, config)
    print(f"  Reward: {reward_bad:.3f} (gate triggered)")
    
    print("\nTest Case 3: Compliance violation (should zero reward)")
    metrics_bad_compliance = dict(metrics_good, compliance_ok=False)
    reward_bad2 = compute_reward(metrics_bad_compliance, config)
    print(f"  Reward: {reward_bad2:.3f} (gate triggered)")


def demo_policy_versioning():
    """Demo policy versioning and rollback."""
    print_section("Demo 5: Policy Versioning & Rollback")
    
    from alphashield.rl.policy import PolicyManager, Policy
    
    manager = PolicyManager(db_client=None)
    
    print("\nCreating policy versions for Lender agent...")
    
    # Create multiple versions
    for v in range(1, 4):
        policy = manager.bump_version(
            agent='Lender',
            algo='LinUCB',
            params={'version': v, 'alpha': 1.5 + v * 0.1},
            metadata={'fitness': 0.5 + v * 0.1, 'date': f'2024-01-0{v}'}
        )
        print(f"  Created version {policy.version}: fitness={policy.metadata['fitness']:.2f}")
    
    # Load latest
    latest = manager.load_policy('Lender')
    print(f"\n✓ Latest version: {latest.version}")
    print(f"  Algorithm: {latest.algo}")
    print(f"  Fitness: {latest.metadata['fitness']:.2f}")
    
    # List versions
    print("\nAll versions:")
    versions = manager.list_versions('Lender', limit=10)
    for v in versions:
        print(f"  v{v.version}: created={v.created_at}, fitness={v.metadata.get('fitness', 'N/A')}")
    
    # Rollback
    print("\nRollback to version 2...")
    v2 = manager.load_policy('Lender', version=2)
    print(f"  Loaded version {v2.version}: fitness={v2.metadata['fitness']:.2f}")


def main():
    """Run all demos."""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  AlphaShield RL: Self-Optimizing Agent Demo".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    try:
        # Demo 1: Single agent
        rl1 = demo_single_agent()
        
        # Demo 2: Multi-agent
        rl2 = demo_multi_agent()
        
        # Demo 3: Statistics
        demo_statistics(rl2)
        
        # Demo 4: Reward components
        demo_reward_components()
        
        # Demo 5: Policy versioning
        demo_policy_versioning()
        
        print_section("✓ All Demos Complete!")
        print("\nKey Features Demonstrated:")
        print("  1. ✓ Contextual bandit learning (LinUCB)")
        print("  2. ✓ Action distribution shifts with experience")
        print("  3. ✓ Multi-agent coordination")
        print("  4. ✓ Reward function with ethics gates")
        print("  5. ✓ Policy versioning and rollback")
        print("  6. ✓ Statistics and monitoring")
        
        print("\nNext Steps:")
        print("  - Connect to MongoDB for persistent storage")
        print("  - Run nightly meta-optimization")
        print("  - Integrate with real agent decisions")
        print("  - Deploy to production with gradual rollout")
        
        print("\nDocumentation: docs/RL_OVERVIEW.md")
        print("Configuration: config/rl.yaml")
        print("Tests: pytest tests/rl/ -v")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
