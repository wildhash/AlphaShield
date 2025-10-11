"""Policy objects for RL module.

Handles policy versioning, serialization, and persistence.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from datetime import datetime
import json


@dataclass
class Policy:
    """Policy metadata and parameters.
    
    Attributes
    ----------
    agent : str
        Agent name (e.g., 'Lender', 'AlphaTrading')
    algo : str
        Algorithm name (e.g., 'LinUCB', 'ThompsonSampling')
    version : int
        Policy version number
    created_at : str
        ISO timestamp of creation
    params : dict
        Algorithm parameters (e.g., A, b matrices for LinUCB)
    metadata : dict
        Additional metadata (fitness, performance metrics, etc.)
    """
    agent: str
    algo: str
    version: int
    created_at: str
    params: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary for storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Policy':
        """Load policy from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize policy to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Policy':
        """Deserialize policy from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class PolicyManager:
    """Manages policy storage and retrieval."""
    
    def __init__(self, db_client=None):
        """Initialize policy manager.
        
        Parameters
        ----------
        db_client : MongoDBClient, optional
            Database client for persistence
        """
        self.db = db_client
        self._policies: Dict[str, Policy] = {}  # In-memory cache
    
    def save_policy(self, policy: Policy) -> str:
        """Save policy to database.
        
        Parameters
        ----------
        policy : Policy
            Policy object to save
        
        Returns
        -------
        str
            Policy ID
        """
        # Cache in memory
        key = f"{policy.agent}_{policy.version}"
        self._policies[key] = policy
        
        # Persist to database if available
        if self.db:
            collection = self.db.get_collection('rl_policies')
            doc = policy.to_dict()
            doc['_id'] = key
            collection.replace_one({'_id': key}, doc, upsert=True)
        
        return key
    
    def load_policy(self, agent: str, version: Optional[int] = None) -> Optional[Policy]:
        """Load policy from database.
        
        Parameters
        ----------
        agent : str
            Agent name
        version : int, optional
            Specific version to load. If None, loads latest.
        
        Returns
        -------
        Policy or None
            Loaded policy or None if not found
        """
        if not self.db:
            # Try in-memory cache
            if version is not None:
                key = f"{agent}_{version}"
                return self._policies.get(key)
            # Find latest version in cache
            agent_policies = [p for k, p in self._policies.items() if k.startswith(agent)]
            if agent_policies:
                return max(agent_policies, key=lambda p: p.version)
            return None
        
        collection = self.db.get_collection('rl_policies')
        
        if version is not None:
            # Load specific version
            key = f"{agent}_{version}"
            doc = collection.find_one({'_id': key})
            if doc:
                doc.pop('_id', None)
                return Policy.from_dict(doc)
        else:
            # Load latest version
            cursor = collection.find({'agent': agent}).sort('version', -1).limit(1)
            docs = list(cursor)
            if docs:
                doc = docs[0]
                doc.pop('_id', None)
                return Policy.from_dict(doc)
        
        return None
    
    def get_latest_version(self, agent: str) -> int:
        """Get the latest policy version number for an agent.
        
        Parameters
        ----------
        agent : str
            Agent name
        
        Returns
        -------
        int
            Latest version number (0 if none exist)
        """
        policy = self.load_policy(agent)
        return policy.version if policy else 0
    
    def bump_version(self, agent: str, algo: str, params: Dict[str, Any], 
                    metadata: Optional[Dict[str, Any]] = None) -> Policy:
        """Create a new policy version.
        
        Parameters
        ----------
        agent : str
            Agent name
        algo : str
            Algorithm name
        params : dict
            Algorithm parameters
        metadata : dict, optional
            Additional metadata
        
        Returns
        -------
        Policy
            New policy with incremented version
        """
        current_version = self.get_latest_version(agent)
        new_version = current_version + 1
        
        policy = Policy(
            agent=agent,
            algo=algo,
            version=new_version,
            created_at=datetime.utcnow().isoformat(),
            params=params,
            metadata=metadata
        )
        
        self.save_policy(policy)
        return policy
    
    def list_versions(self, agent: str, limit: int = 10) -> list:
        """List recent policy versions for an agent.
        
        Parameters
        ----------
        agent : str
            Agent name
        limit : int
            Maximum number of versions to return
        
        Returns
        -------
        list
            List of Policy objects
        """
        if not self.db:
            # Use in-memory cache
            agent_policies = [p for k, p in self._policies.items() if k.startswith(agent)]
            agent_policies.sort(key=lambda p: p.version, reverse=True)
            return agent_policies[:limit]
        
        collection = self.db.get_collection('rl_policies')
        cursor = collection.find({'agent': agent}).sort('version', -1).limit(limit)
        
        policies = []
        for doc in cursor:
            doc.pop('_id', None)
            policies.append(Policy.from_dict(doc))
        
        return policies
