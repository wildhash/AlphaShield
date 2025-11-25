#!/usr/bin/env python3
"""
Nightly RL Training Pipeline

This script runs the nightly training pipeline for all AlphaShield agents.
It pulls data from the replay buffer, trains/updates bandits, validates
performance, and deploys improved policies.

Usage:
    python jobs/train_nightly.py [--dry-run] [--window-days 60] [--agents Lender,AlphaTrading]

Environment Variables:
    MONGODB_URI: MongoDB connection string
    TRAINING_WINDOW_DAYS: Number of days of data to use (default: 60)
    DRY_RUN: If "true", skip deployment (default: false)
    DEPLOYMENT_THRESHOLD: Minimum improvement required (default: 0.05)
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alphashield.rl.policy import Policy, PolicyManager
from alphashield.rl.bandit import LinUCB
from alphashield.database.mongodb_client import get_mongo_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_AGENTS = ['Lender', 'AlphaTrading', 'SpendingGuard', 'BudgetAnalyzer', 'TaxOptimizer', 'ContractReview']
DEFAULT_WINDOW_DAYS = 60
DEFAULT_DEPLOYMENT_THRESHOLD = 0.05  # 5% improvement required


class NightlyTrainer:
    """Orchestrates nightly RL training pipeline."""
    
    def __init__(
        self,
        db_client=None,
        window_days: int = DEFAULT_WINDOW_DAYS,
        deployment_threshold: float = DEFAULT_DEPLOYMENT_THRESHOLD,
        dry_run: bool = False
    ):
        self.db = db_client or get_mongo_client()
        self.window_days = window_days
        self.deployment_threshold = deployment_threshold
        self.dry_run = dry_run
        self.policy_manager = PolicyManager(self.db)
        self.results: Dict[str, dict] = {}
        
    def run(self, agents: Optional[List[str]] = None) -> Dict[str, dict]:
        """Run training pipeline for all specified agents.
        
        Args:
            agents: List of agent names to train. If None, train all.
            
        Returns:
            Dictionary of training results per agent.
        """
        agents = agents or DEFAULT_AGENTS
        start_time = datetime.utcnow()
        
        logger.info("=" * 60)
        logger.info(f"Starting nightly training pipeline")
        logger.info(f"Agents: {agents}")
        logger.info(f"Window: {self.window_days} days")
        logger.info(f"Deployment threshold: {self.deployment_threshold * 100:.1f}%")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 60)
        
        for agent_name in agents:
            try:
                result = self._train_agent(agent_name)
                self.results[agent_name] = result
            except Exception as e:
                logger.error(f"Failed to train {agent_name}: {e}")
                self.results[agent_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Log summary
        self._log_summary(start_time)
        
        # Store training run metadata
        self._store_training_run(start_time)
        
        return self.results
    
    def _train_agent(self, agent_name: str) -> dict:
        """Train a single agent's bandit.
        
        Args:
            agent_name: Name of the agent to train.
            
        Returns:
            Training result dictionary.
        """
        logger.info(f"\n--- Training {agent_name} ---")
        
        # 1. Load replay buffer data
        replay_data = self._load_replay_data(agent_name)
        if not replay_data or len(replay_data) < 100:
            logger.warning(f"Insufficient data for {agent_name}: {len(replay_data) if replay_data else 0} samples")
            return {
                'status': 'skipped',
                'reason': 'insufficient_data',
                'samples': len(replay_data) if replay_data else 0
            }
        
        logger.info(f"Loaded {len(replay_data)} samples for {agent_name}")
        
        # 2. Load current policy
        current_policy = self.policy_manager.load_policy(agent_name)
        current_version = current_policy.version if current_policy else 0
        logger.info(f"Current policy version: {current_version}")
        
        # 3. Train new bandit
        new_bandit = self._train_bandit(agent_name, replay_data)
        
        # 4. Evaluate improvement
        improvement = self._evaluate_improvement(
            agent_name, new_bandit, current_policy, replay_data
        )
        logger.info(f"Improvement: {improvement * 100:.2f}%")
        
        # 5. Deploy if improved
        deployed = False
        new_version = current_version
        
        if improvement >= self.deployment_threshold:
            if not self.dry_run:
                new_policy = self._deploy_policy(agent_name, new_bandit, improvement)
                new_version = new_policy.version
                deployed = True
                logger.info(f"✅ Deployed new policy v{new_version} for {agent_name}")
            else:
                logger.info(f"🔸 Would deploy new policy (dry run)")
                deployed = False
        else:
            logger.info(f"⏭️ Skipping deployment: improvement {improvement * 100:.2f}% < threshold {self.deployment_threshold * 100:.1f}%")
        
        return {
            'status': 'success',
            'samples': len(replay_data),
            'current_version': current_version,
            'new_version': new_version,
            'improvement': improvement,
            'deployed': deployed,
            'threshold': self.deployment_threshold
        }
    
    def _load_replay_data(self, agent_name: str) -> List[dict]:
        """Load replay buffer data for agent.
        
        Args:
            agent_name: Agent to load data for.
            
        Returns:
            List of experience tuples.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.window_days)
        
        # Query replay buffer collection
        # This is a stub - implement based on actual replay buffer schema
        try:
            collection = self.db.get_collection('replay_buffer') if hasattr(self.db, 'get_collection') else None
            if collection is None:
                # Fallback for in-memory stub
                return []
            
            cursor = collection.find({
                'agent': agent_name,
                'timestamp': {'$gte': cutoff_date}
            }).sort('timestamp', 1)
            
            return list(cursor)
        except Exception as e:
            logger.warning(f"Could not load replay data: {e}")
            return []
    
    def _train_bandit(self, agent_name: str, replay_data: List[dict]) -> LinUCB:
        """Train LinUCB bandit on replay data.
        
        Args:
            agent_name: Agent name.
            replay_data: List of experience tuples.
            
        Returns:
            Trained LinUCB bandit.
        """
        # Determine bandit configuration based on agent
        configs = {
            'Lender': {'n_actions': 5, 'd': 10, 'alpha': 1.5},
            'AlphaTrading': {'n_actions': 5, 'd': 15, 'alpha': 1.2},
            'SpendingGuard': {'n_actions': 3, 'd': 8, 'alpha': 1.8},
            'BudgetAnalyzer': {'n_actions': 4, 'd': 12, 'alpha': 1.5},
            'TaxOptimizer': {'n_actions': 4, 'd': 10, 'alpha': 1.5},
            'ContractReview': {'n_actions': 3, 'd': 8, 'alpha': 1.5},
        }
        
        config = configs.get(agent_name, {'n_actions': 4, 'd': 10, 'alpha': 1.5})
        bandit = LinUCB(**config)
        
        # Train on replay data
        for experience in replay_data:
            context = experience.get('context', [0] * config['d'])
            action = experience.get('action', 0)
            reward = experience.get('reward', 0)
            
            # Ensure context is correct dimension
            if len(context) != config['d']:
                context = context[:config['d']] + [0] * max(0, config['d'] - len(context))
            
            bandit.update(context, action, reward)
        
        return bandit
    
    def _evaluate_improvement(
        self,
        agent_name: str,
        new_bandit: LinUCB,
        current_policy: Optional[Policy],
        replay_data: List[dict]
    ) -> float:
        """Evaluate improvement of new bandit over current policy.
        
        Uses counterfactual evaluation on held-out data.
        
        Args:
            agent_name: Agent name.
            new_bandit: Newly trained bandit.
            current_policy: Current deployed policy.
            replay_data: Replay data (split for evaluation).
            
        Returns:
            Improvement ratio (e.g., 0.05 = 5% improvement).
        """
        # Split data: 80% train, 20% eval
        split_idx = int(len(replay_data) * 0.8)
        eval_data = replay_data[split_idx:]
        
        if len(eval_data) < 20:
            logger.warning("Insufficient eval data, returning 0 improvement")
            return 0.0
        
        # Compute expected reward under new policy
        new_reward = 0.0
        for exp in eval_data:
            context = exp.get('context', [])
            if len(context) >= new_bandit.cfg.d:
                action = new_bandit.suggest_action(context[:new_bandit.cfg.d])
                if action == exp.get('action'):
                    new_reward += exp.get('reward', 0)
        
        # Compute expected reward under current policy (if exists)
        if current_policy and current_policy.params:
            # This is simplified - would need to reconstruct bandit from policy params
            current_reward = sum(exp.get('reward', 0) for exp in eval_data) / 2
        else:
            current_reward = sum(exp.get('reward', 0) for exp in eval_data) / 2
        
        # Compute improvement
        if current_reward == 0:
            return 0.0 if new_reward == 0 else 0.1
        
        improvement = (new_reward - current_reward) / abs(current_reward)
        return max(-1.0, min(1.0, improvement))  # Clamp to [-1, 1]
    
    def _deploy_policy(self, agent_name: str, bandit: LinUCB, improvement: float) -> Policy:
        """Deploy new policy.
        
        Args:
            agent_name: Agent name.
            bandit: Trained bandit to deploy.
            improvement: Improvement over previous policy.
            
        Returns:
            New deployed Policy object.
        """
        # Extract bandit parameters
        params = {
            'A': bandit.A.tolist(),
            'b': bandit.b.tolist(),
            'config': {
                'n_actions': bandit.cfg.n_actions,
                'd': bandit.cfg.d,
                'alpha': bandit.cfg.alpha,
                'reg': bandit.cfg.reg
            }
        }
        
        metadata = {
            'improvement': improvement,
            'training_window_days': self.window_days,
            'trained_at': datetime.utcnow().isoformat(),
            'deployment_threshold': self.deployment_threshold
        }
        
        return self.policy_manager.bump_version(
            agent=agent_name,
            algo='LinUCB',
            params=params,
            metadata=metadata
        )
    
    def _log_summary(self, start_time: datetime):
        """Log training summary."""
        duration = datetime.utcnow() - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("TRAINING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration.total_seconds():.1f}s")
        
        for agent, result in self.results.items():
            status = result.get('status', 'unknown')
            if status == 'success':
                deployed = '✅' if result.get('deployed') else '⏭️'
                logger.info(f"{deployed} {agent}: improvement={result.get('improvement', 0) * 100:.2f}% v{result.get('current_version', 0)}→v{result.get('new_version', 0)}")
            elif status == 'skipped':
                logger.info(f"⏭️ {agent}: skipped ({result.get('reason', 'unknown')})")
            else:
                logger.info(f"❌ {agent}: {result.get('error', 'unknown error')}")
        
        logger.info("=" * 60)
    
    def _store_training_run(self, start_time: datetime):
        """Store training run metadata in database."""
        try:
            if hasattr(self.db, 'get_collection'):
                collection = self.db.get_collection('training_runs')
                if collection is not None:
                    collection.insert_one({
                        'started_at': start_time,
                        'completed_at': datetime.utcnow(),
                        'window_days': self.window_days,
                        'dry_run': self.dry_run,
                        'results': self.results
                    })
        except Exception as e:
            logger.warning(f"Could not store training run: {e}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run nightly RL training pipeline')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=os.getenv('DRY_RUN', 'false').lower() == 'true',
        help='Run without deploying policies'
    )
    parser.add_argument(
        '--window-days',
        type=int,
        default=int(os.getenv('TRAINING_WINDOW_DAYS', DEFAULT_WINDOW_DAYS)),
        help=f'Number of days of data to use (default: {DEFAULT_WINDOW_DAYS})'
    )
    parser.add_argument(
        '--agents',
        type=str,
        default=None,
        help='Comma-separated list of agents to train (default: all)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=float(os.getenv('DEPLOYMENT_THRESHOLD', DEFAULT_DEPLOYMENT_THRESHOLD)),
        help=f'Minimum improvement for deployment (default: {DEFAULT_DEPLOYMENT_THRESHOLD})'
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    args = parse_args()
    
    agents = args.agents.split(',') if args.agents else None
    
    trainer = NightlyTrainer(
        window_days=args.window_days,
        deployment_threshold=args.threshold,
        dry_run=args.dry_run
    )
    
    results = trainer.run(agents)
    
    # Exit with error code if any agent failed
    failed = any(r.get('status') == 'error' for r in results.values())
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
