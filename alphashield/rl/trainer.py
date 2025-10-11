"""Training loop for RL module.

Coordinates bandit updates, reward computation, and experience replay.
"""
from typing import Dict, Any, Optional
import numpy as np
from datetime import datetime

from alphashield.rl.bandit import LinUCB
from alphashield.rl.context import build_context, get_context_dimension, build_action_space
from alphashield.rl.reward import compute_reward, RewardConfig
from alphashield.rl.replay import ReplayBuffer
from alphashield.rl.policy import Policy, PolicyManager
from alphashield.rl.evolution import optimize_reward_weights


class RLTrainer:
    """RL trainer for AlphaShield agents."""
    
    def __init__(self, 
                 db_client=None,
                 reward_config: Optional[RewardConfig] = None,
                 mock_mode: bool = False):
        """Initialize RL trainer.
        
        Parameters
        ----------
        db_client : MongoDBClient, optional
            Database client for persistence
        reward_config : RewardConfig, optional
            Reward configuration (uses defaults if None)
        mock_mode : bool
            If True, uses mock feedback for testing
        """
        self.db = db_client
        self.reward_config = reward_config or RewardConfig()
        self.mock_mode = mock_mode
        
        # Initialize components
        self.replay = ReplayBuffer(db_client)
        self.policy_manager = PolicyManager(db_client)
        
        # Bandits per agent (lazy initialization)
        self._bandits: Dict[str, LinUCB] = {}
    
    def _get_bandit(self, agent_name: str) -> LinUCB:
        """Get or create bandit for an agent.
        
        Parameters
        ----------
        agent_name : str
            Agent name
        
        Returns
        -------
        LinUCB
            Bandit instance for the agent
        """
        if agent_name not in self._bandits:
            action_space = build_action_space(agent_name)
            n_actions = action_space['n_actions']
            d = get_context_dimension()
            
            self._bandits[agent_name] = LinUCB(
                n_actions=n_actions,
                d=d,
                alpha=1.5,
                reg=1e-2
            )
        
        return self._bandits[agent_name]
    
    def train_step(self, 
                  agent_name: str,
                  user_id: str,
                  decision_input: Dict[str, Any],
                  agent_output: Dict[str, Any],
                  recent_metrics: Optional[Dict[str, Any]] = None,
                  memory_hits: Optional[list] = None) -> Dict[str, Any]:
        """Execute a single training step.
        
        Parameters
        ----------
        agent_name : str
            Name of the agent
        user_id : str
            User identifier
        decision_input : dict
            Input to the agent decision
        agent_output : dict
            Output from the agent
        recent_metrics : dict, optional
            Recent performance metrics
        memory_hits : list, optional
            Memory search results
        
        Returns
        -------
        dict
            Training step results including reward and action
        """
        # Build context
        context = build_context(
            agent_name=agent_name,
            user_id=user_id,
            decision_input=decision_input,
            recent_metrics=recent_metrics,
            memory_hits=memory_hits
        )
        
        # Get bandit and suggest action
        bandit = self._get_bandit(agent_name)
        action = bandit.suggest_action(context)
        
        # Extract or mock metrics
        if self.mock_mode:
            metrics = self._mock_metrics(agent_name, action)
        else:
            metrics = self._extract_metrics(agent_output, recent_metrics)
        
        # Compute reward
        reward = compute_reward(metrics, self.reward_config.to_dict())
        
        # Update bandit
        bandit.update(context, action, reward)
        
        # Store experience
        policy_version = self.policy_manager.get_latest_version(agent_name)
        self.replay.append(
            user_id=user_id,
            agent=agent_name,
            context=context,
            action=action,
            metrics=metrics,
            reward=reward,
            policy_version=policy_version
        )
        
        return {
            'action': action,
            'reward': reward,
            'metrics': metrics,
            'policy_version': policy_version,
            'context_dim': len(context)
        }
    
    def _extract_metrics(self, agent_output: Dict[str, Any], 
                        recent_metrics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract metrics from agent output and recent data.
        
        Parameters
        ----------
        agent_output : dict
            Agent decision output
        recent_metrics : dict, optional
            Recent performance metrics
        
        Returns
        -------
        dict
            Extracted metrics for reward computation
        """
        metrics = {}
        
        # Extract from recent metrics if available
        if recent_metrics:
            metrics['wealth_delta'] = recent_metrics.get('wealth_delta', 0.0)
            metrics['coverage_ratio'] = recent_metrics.get('coverage_ratio', 1.0)
            metrics['drawdown'] = recent_metrics.get('drawdown', 0.0)
            metrics['anomaly'] = recent_metrics.get('anomaly', 0.0)
            metrics['tax_risk'] = recent_metrics.get('tax_risk', 0.0)
            metrics['satisfaction'] = recent_metrics.get('satisfaction', 0.5)
            metrics['calibration'] = recent_metrics.get('calibration', 1.0)
        else:
            # Defaults
            metrics['wealth_delta'] = 0.0
            metrics['coverage_ratio'] = 1.0
            metrics['drawdown'] = 0.0
            metrics['anomaly'] = 0.0
            metrics['tax_risk'] = 0.0
            metrics['satisfaction'] = 0.5
            metrics['calibration'] = 1.0
        
        # Fairness and compliance from agent output
        metrics['fairness'] = agent_output.get('fairness_score', 
                                               agent_output.get('fairness', 0.8))
        metrics['compliance_ok'] = agent_output.get('compliant', 
                                                    agent_output.get('compliance_ok', True))
        
        return metrics
    
    def _mock_metrics(self, agent_name: str, action: int) -> Dict[str, Any]:
        """Generate mock metrics for testing.
        
        Parameters
        ----------
        agent_name : str
            Agent name
        action : int
            Action taken
        
        Returns
        -------
        dict
            Mock metrics
        """
        # Simple mock: better actions get better metrics
        action_space = build_action_space(agent_name)
        n_actions = action_space['n_actions']
        action_quality = 1.0 - (action / max(1, n_actions - 1))
        
        noise = np.random.normal(0, 0.1)
        
        return {
            'wealth_delta': max(0, min(1, 0.5 + 0.3 * action_quality + noise)),
            'coverage_ratio': 1.2 + 0.4 * action_quality,
            'fairness': max(0.5, min(1, 0.8 + 0.2 * action_quality + noise)),
            'satisfaction': max(0, min(1, 0.6 + 0.3 * action_quality + noise)),
            'drawdown': max(0, min(1, 0.1 - 0.1 * action_quality + abs(noise))),
            'anomaly': max(0, min(1, 0.05 + abs(noise) * 0.1)),
            'tax_risk': max(0, min(1, 0.03 + abs(noise) * 0.05)),
            'calibration': 1.0,
            'compliance_ok': action_quality > 0.3
        }
    
    def nightly_meta_optimization(self, 
                                 agents: Optional[list] = None,
                                 n_days: int = 30,
                                 max_generations: int = 30) -> Dict[str, Any]:
        """Run nightly meta-optimization of reward weights.
        
        Parameters
        ----------
        agents : list, optional
            List of agent names to optimize (None = all)
        n_days : int
            Number of days to evaluate over
        max_generations : int
            Maximum evolutionary generations
        
        Returns
        -------
        dict
            Optimization results
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'agents_optimized': [],
            'improvements': {}
        }
        
        # Get current reward config
        base_config = self.reward_config.to_dict()
        
        # Optimize reward weights
        optimized_config = optimize_reward_weights(
            replay_buffer=self.replay,
            base_config=base_config,
            n_days=n_days,
            max_generations=max_generations
        )
        
        # Check if improvement is significant
        baseline_fitness = self._evaluate_config(base_config, n_days)
        optimized_fitness = self._evaluate_config(optimized_config, n_days)
        
        if optimized_fitness > baseline_fitness + 0.01:
            # Update configuration
            self.reward_config = RewardConfig(**optimized_config)
            results['improved'] = True
            results['baseline_fitness'] = baseline_fitness
            results['optimized_fitness'] = optimized_fitness
            results['new_config'] = optimized_config
        else:
            results['improved'] = False
            results['fitness'] = baseline_fitness
        
        return results
    
    def _evaluate_config(self, config: Dict[str, float], n_days: int) -> float:
        """Evaluate a reward configuration.
        
        Parameters
        ----------
        config : dict
            Reward configuration
        n_days : int
            Evaluation window
        
        Returns
        -------
        float
            Average reward over evaluation window
        """
        experiences = self.replay.sample(n=500, recent_days=n_days)
        
        if not experiences:
            return 0.0
        
        rewards = []
        for exp in experiences:
            metrics = exp.get('metrics', {})
            reward = compute_reward(metrics, config)
            rewards.append(reward)
        
        return float(np.mean(rewards))
    
    def get_statistics(self, agent: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """Get training statistics.
        
        Parameters
        ----------
        agent : str, optional
            Filter by agent
        days : int
            Look back window
        
        Returns
        -------
        dict
            Training statistics
        """
        stats = self.replay.get_statistics(agent=agent, days=days)
        
        if agent:
            bandit = self._bandits.get(agent)
            if bandit:
                stats['bandit_initialized'] = True
            else:
                stats['bandit_initialized'] = False
        else:
            stats['agents_active'] = list(self._bandits.keys())
        
        return stats
