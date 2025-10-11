"""Experience replay buffer for RL training.

Stores experiences in MongoDB with efficient sampling and retrieval.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np


class ReplayBuffer:
    """MongoDB-backed experience replay buffer.
    
    Stores experiences with schema:
    {
        'ts': datetime,
        'user_id': str,
        'agent': str,
        'context': array,
        'action': int,
        'metrics': dict,
        'reward': float,
        'policy_version': int
    }
    """
    
    def __init__(self, db_client=None, retention_days: int = 90):
        """Initialize replay buffer.
        
        Parameters
        ----------
        db_client : MongoDBClient, optional
            Database client for persistence
        retention_days : int
            Number of days to retain experiences (default 90)
        """
        self.db = db_client
        self.retention_days = retention_days
        self._buffer: List[Dict[str, Any]] = []  # In-memory buffer
    
    def append(self, user_id: str, agent: str, context: np.ndarray, 
              action: int, metrics: Dict[str, Any], reward: float, 
              policy_version: int) -> str:
        """Add an experience to the replay buffer.
        
        Parameters
        ----------
        user_id : str
            User identifier
        agent : str
            Agent name
        context : np.ndarray
            Context feature vector
        action : int
            Action taken
        metrics : dict
            Raw metrics collected
        reward : float
            Computed reward
        policy_version : int
            Policy version used
        
        Returns
        -------
        str
            Experience ID
        """
        experience = {
            'ts': datetime.utcnow(),
            'user_id': user_id,
            'agent': agent,
            'context': context.tolist(),
            'action': int(action),
            'metrics': metrics,
            'reward': float(reward),
            'policy_version': int(policy_version)
        }
        
        # Add to in-memory buffer
        self._buffer.append(experience)
        
        # Persist to database if available
        if self.db:
            collection = self.db.get_collection('rl_experiences')
            result = collection.insert_one(experience)
            return str(result.inserted_id)
        
        return f"mem_{len(self._buffer)}"
    
    def sample(self, agent: Optional[str] = None, user_id: Optional[str] = None,
              n: int = 100, recent_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Sample experiences from the replay buffer.
        
        Parameters
        ----------
        agent : str, optional
            Filter by agent name
        user_id : str, optional
            Filter by user ID
        n : int
            Number of samples to retrieve (default 100)
        recent_days : int, optional
            Only sample from last N days
        
        Returns
        -------
        list
            List of experience dictionaries
        """
        if not self.db:
            # Sample from in-memory buffer
            filtered = self._buffer
            if agent:
                filtered = [e for e in filtered if e['agent'] == agent]
            if user_id:
                filtered = [e for e in filtered if e['user_id'] == user_id]
            if recent_days:
                cutoff = datetime.utcnow() - timedelta(days=recent_days)
                filtered = [e for e in filtered if e['ts'] >= cutoff]
            
            if len(filtered) <= n:
                return filtered
            
            # Random sample
            indices = np.random.choice(len(filtered), size=n, replace=False)
            return [filtered[i] for i in indices]
        
        # Sample from database
        collection = self.db.get_collection('rl_experiences')
        query = {}
        
        if agent:
            query['agent'] = agent
        if user_id:
            query['user_id'] = user_id
        if recent_days:
            cutoff = datetime.utcnow() - timedelta(days=recent_days)
            query['ts'] = {'$gte': cutoff}
        
        # MongoDB sampling (limited aggregation)
        cursor = collection.find(query).limit(n * 2)
        experiences = list(cursor)
        
        # Random sample if we got more than needed
        if len(experiences) > n:
            indices = np.random.choice(len(experiences), size=n, replace=False)
            experiences = [experiences[i] for i in indices]
        
        return experiences
    
    def get_recent(self, agent: str, user_id: Optional[str] = None,
                  n: int = 50, days: int = 30) -> List[Dict[str, Any]]:
        """Get most recent experiences for an agent/user.
        
        Parameters
        ----------
        agent : str
            Agent name
        user_id : str, optional
            User ID filter
        n : int
            Number of experiences to retrieve
        days : int
            Look back window in days
        
        Returns
        -------
        list
            List of recent experiences
        """
        if not self.db:
            cutoff = datetime.utcnow() - timedelta(days=days)
            filtered = [
                e for e in self._buffer 
                if e['agent'] == agent and e['ts'] >= cutoff
            ]
            if user_id:
                filtered = [e for e in filtered if e['user_id'] == user_id]
            
            # Sort by timestamp descending
            filtered.sort(key=lambda e: e['ts'], reverse=True)
            return filtered[:n]
        
        # Query database
        collection = self.db.get_collection('rl_experiences')
        query = {
            'agent': agent,
            'ts': {'$gte': datetime.utcnow() - timedelta(days=days)}
        }
        if user_id:
            query['user_id'] = user_id
        
        cursor = collection.find(query).sort('ts', -1).limit(n)
        return list(cursor)
    
    def cleanup_old_experiences(self) -> int:
        """Remove experiences older than retention period.
        
        Returns
        -------
        int
            Number of experiences removed
        """
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        
        # Clean in-memory buffer
        original_len = len(self._buffer)
        self._buffer = [e for e in self._buffer if e['ts'] >= cutoff]
        removed = original_len - len(self._buffer)
        
        # Clean database
        if self.db:
            collection = self.db.get_collection('rl_experiences')
            result = collection.delete_many({'ts': {'$lt': cutoff}})
            removed = result.deleted_count
        
        return removed
    
    def get_statistics(self, agent: Optional[str] = None, 
                      days: int = 30) -> Dict[str, Any]:
        """Get buffer statistics.
        
        Parameters
        ----------
        agent : str, optional
            Filter by agent
        days : int
            Look back window in days
        
        Returns
        -------
        dict
            Statistics including count, avg reward, etc.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        if not self.db:
            filtered = [e for e in self._buffer if e['ts'] >= cutoff]
            if agent:
                filtered = [e for e in filtered if e['agent'] == agent]
            
            if not filtered:
                return {'count': 0, 'avg_reward': 0.0}
            
            rewards = [e['reward'] for e in filtered]
            return {
                'count': len(filtered),
                'avg_reward': np.mean(rewards),
                'std_reward': np.std(rewards),
                'min_reward': np.min(rewards),
                'max_reward': np.max(rewards)
            }
        
        # Query database for statistics
        collection = self.db.get_collection('rl_experiences')
        query = {'ts': {'$gte': cutoff}}
        if agent:
            query['agent'] = agent
        
        experiences = list(collection.find(query))
        if not experiences:
            return {'count': 0, 'avg_reward': 0.0}
        
        rewards = [e['reward'] for e in experiences]
        return {
            'count': len(experiences),
            'avg_reward': np.mean(rewards),
            'std_reward': np.std(rewards),
            'min_reward': np.min(rewards),
            'max_reward': np.max(rewards)
        }
