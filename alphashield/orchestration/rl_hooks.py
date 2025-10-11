"""RL orchestration hooks for AlphaShield agents.

Integrates RL training into agent decision-making flow.
"""
from typing import Dict, Any, Optional
from alphashield.rl.trainer import RLTrainer


class RLOrchestrator:
    """Orchestrates RL-enhanced agent decisions."""
    
    def __init__(self, db_client=None, mock_mode: bool = False):
        """Initialize RL orchestrator.
        
        Parameters
        ----------
        db_client : MongoDBClient, optional
            Database client
        mock_mode : bool
            If True, uses mock feedback for testing
        """
        self.trainer = RLTrainer(db_client=db_client, mock_mode=mock_mode)
        self.enabled = True
    
    def wrap_agent_decide(self, 
                         agent,
                         user_id: str,
                         decision_input: Dict[str, Any],
                         recent_metrics: Optional[Dict[str, Any]] = None,
                         memory_hits: Optional[list] = None) -> Dict[str, Any]:
        """Wrap agent decision with RL training.
        
        Parameters
        ----------
        agent : BaseAgent
            Agent instance
        user_id : str
            User identifier
        decision_input : dict
            Input to agent decision
        recent_metrics : dict, optional
            Recent performance metrics
        memory_hits : list, optional
            Memory search results
        
        Returns
        -------
        dict
            Agent output enhanced with RL information
        """
        # Execute agent decision (original behavior)
        agent_output = agent.process(**decision_input)
        
        # If RL is disabled, return original output
        if not self.enabled:
            return agent_output
        
        # Train RL on this decision
        try:
            rl_result = self.trainer.train_step(
                agent_name=agent.name,
                user_id=user_id,
                decision_input=decision_input,
                agent_output=agent_output,
                recent_metrics=recent_metrics,
                memory_hits=memory_hits
            )
            
            # Augment output with RL info
            agent_output['rl'] = rl_result
            
        except Exception as e:
            # Log error but don't break agent decision
            agent_output['rl_error'] = str(e)
        
        return agent_output
    
    def get_suggested_action(self, 
                           agent_name: str,
                           user_id: str,
                           decision_input: Dict[str, Any],
                           recent_metrics: Optional[Dict[str, Any]] = None) -> int:
        """Get RL-suggested action without executing agent.
        
        Parameters
        ----------
        agent_name : str
            Agent name
        user_id : str
            User identifier
        decision_input : dict
            Decision input
        recent_metrics : dict, optional
            Recent metrics
        
        Returns
        -------
        int
            Suggested action index
        """
        from alphashield.rl.context import build_context
        
        context = build_context(
            agent_name=agent_name,
            user_id=user_id,
            decision_input=decision_input,
            recent_metrics=recent_metrics
        )
        
        bandit = self.trainer._get_bandit(agent_name)
        return bandit.suggest_action(context)
    
    def run_nightly_optimization(self, 
                                n_days: int = 30,
                                max_generations: int = 30) -> Dict[str, Any]:
        """Run nightly meta-optimization.
        
        Parameters
        ----------
        n_days : int
            Evaluation window
        max_generations : int
            Max evolutionary generations
        
        Returns
        -------
        dict
            Optimization results
        """
        return self.trainer.nightly_meta_optimization(
            n_days=n_days,
            max_generations=max_generations
        )
    
    def get_statistics(self, agent: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """Get RL training statistics.
        
        Parameters
        ----------
        agent : str, optional
            Filter by agent
        days : int
            Look back window
        
        Returns
        -------
        dict
            Statistics
        """
        return self.trainer.get_statistics(agent=agent, days=days)
    
    def enable(self):
        """Enable RL training."""
        self.enabled = True
    
    def disable(self):
        """Disable RL training."""
        self.enabled = False
