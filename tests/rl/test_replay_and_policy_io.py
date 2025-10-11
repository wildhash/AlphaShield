# tests/rl/test_replay_and_policy_io.py
"""Tests for replay buffer and policy I/O."""
import numpy as np
from alphashield.rl.replay import ReplayBuffer
from alphashield.rl.policy import Policy, PolicyManager


def test_replay_buffer_in_memory():
    """Test replay buffer without MongoDB (in-memory only)."""
    replay = ReplayBuffer(db_client=None)
    
    # Add some experiences
    context = np.array([0.1, 0.2, 0.3, 0.4])
    metrics = {'fairness': 0.8, 'reward': 0.5}
    
    exp_id = replay.append(
        user_id='user1',
        agent='Lender',
        context=context,
        action=0,
        metrics=metrics,
        reward=0.5,
        policy_version=1
    )
    
    assert exp_id.startswith('mem_')
    
    # Sample experiences
    samples = replay.sample(n=10)
    assert len(samples) == 1
    assert samples[0]['user_id'] == 'user1'
    assert samples[0]['agent'] == 'Lender'
    assert samples[0]['action'] == 0


def test_replay_buffer_statistics():
    """Test replay buffer statistics."""
    replay = ReplayBuffer(db_client=None)
    
    # Add experiences with varying rewards
    context = np.array([0.1, 0.2, 0.3])
    for i in range(10):
        replay.append(
            user_id=f'user{i}',
            agent='Lender',
            context=context,
            action=i % 3,
            metrics={'fairness': 0.8},
            reward=0.5 + i * 0.05,
            policy_version=1
        )
    
    stats = replay.get_statistics()
    assert stats['count'] == 10
    assert 0.5 <= stats['avg_reward'] <= 1.0
    assert stats['std_reward'] > 0


def test_policy_round_trip():
    """Test policy serialization and deserialization."""
    policy = Policy(
        agent='Lender',
        algo='LinUCB',
        version=1,
        created_at='2024-01-01T00:00:00',
        params={'A': [[1, 0], [0, 1]], 'b': [0, 0]},
        metadata={'fitness': 0.8}
    )
    
    # Convert to dict and back
    policy_dict = policy.to_dict()
    restored = Policy.from_dict(policy_dict)
    
    assert restored.agent == 'Lender'
    assert restored.algo == 'LinUCB'
    assert restored.version == 1
    assert restored.params['A'] == [[1, 0], [0, 1]]
    assert restored.metadata['fitness'] == 0.8


def test_policy_manager_in_memory():
    """Test policy manager without MongoDB."""
    manager = PolicyManager(db_client=None)
    
    # Create and save a policy
    policy = Policy(
        agent='Lender',
        algo='LinUCB',
        version=1,
        created_at='2024-01-01T00:00:00',
        params={'test': 'data'},
        metadata={}
    )
    
    policy_id = manager.save_policy(policy)
    assert policy_id == 'Lender_1'
    
    # Load the policy
    loaded = manager.load_policy('Lender', version=1)
    assert loaded is not None
    assert loaded.agent == 'Lender'
    assert loaded.version == 1
    
    # Bump version
    new_policy = manager.bump_version(
        agent='Lender',
        algo='LinUCB',
        params={'test': 'new_data'}
    )
    assert new_policy.version == 2
    
    # Get latest version
    latest_version = manager.get_latest_version('Lender')
    assert latest_version == 2


def test_policy_manager_list_versions():
    """Test listing policy versions."""
    manager = PolicyManager(db_client=None)
    
    # Create multiple versions
    for v in range(1, 4):
        policy = Policy(
            agent='Lender',
            algo='LinUCB',
            version=v,
            created_at=f'2024-01-0{v}T00:00:00',
            params={'version': v},
            metadata={}
        )
        manager.save_policy(policy)
    
    # List versions
    versions = manager.list_versions('Lender', limit=10)
    assert len(versions) == 3
    # Should be sorted by version descending
    assert versions[0].version == 3
    assert versions[1].version == 2
    assert versions[2].version == 1
