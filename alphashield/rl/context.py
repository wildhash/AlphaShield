"""Context builder for RL decision-making.

Builds feature vectors from agent states, user data, and memory lookups.
"""
from typing import Dict, Any, List, Optional
import numpy as np
from datetime import datetime


def build_context(
    agent_name: str,
    user_id: str,
    decision_input: Dict[str, Any],
    recent_metrics: Optional[Dict[str, Any]] = None,
    memory_hits: Optional[List[Dict[str, Any]]] = None
) -> np.ndarray:
    """Build context feature vector for RL decision.
    
    Parameters
    ----------
    agent_name : str
        Name of the agent making the decision
    user_id : str
        User identifier
    decision_input : dict
        Current decision input data
    recent_metrics : dict, optional
        Recent performance metrics
    memory_hits : list, optional
        Memory/context retrievals from semantic search
    
    Returns
    -------
    np.ndarray
        Feature vector for the context
    """
    features = []
    
    # Bias term (always 1.0)
    features.append(1.0)
    
    # Agent encoding (one-hot or hash)
    agent_hash = hash(agent_name) % 100
    features.append(agent_hash / 100.0)
    
    # User encoding (hash for anonymity)
    user_hash = hash(user_id) % 1000
    features.append(user_hash / 1000.0)
    
    # Time features
    now = datetime.utcnow()
    hour_of_day = now.hour / 24.0
    day_of_week = now.weekday() / 7.0
    features.extend([hour_of_day, day_of_week])
    
    # Decision input features (generic extraction)
    if decision_input:
        # Extract numeric fields
        amount = decision_input.get('amount', decision_input.get('principal', 0))
        features.append(np.log1p(amount) / 10.0)  # log-scaled amount
        
        interest_rate = decision_input.get('interest_rate', 0)
        features.append(interest_rate / 100.0)
        
        term = decision_input.get('term_months', decision_input.get('term', 0))
        features.append(term / 60.0)  # normalize by 5 years
    else:
        features.extend([0.0, 0.0, 0.0])
    
    # Recent metrics features
    if recent_metrics:
        features.append(recent_metrics.get('coverage_ratio', 1.0) / 2.0)
        features.append(recent_metrics.get('risk_score', 0.5))
        features.append(recent_metrics.get('satisfaction', 0.5))
    else:
        features.extend([0.5, 0.5, 0.5])
    
    # Memory/embedding features (count and quality)
    if memory_hits:
        memory_count = min(len(memory_hits), 10) / 10.0
        avg_similarity = np.mean([h.get('similarity', 0.5) for h in memory_hits])
        features.extend([memory_count, avg_similarity])
    else:
        features.extend([0.0, 0.5])
    
    return np.array(features, dtype=np.float64)


def get_context_dimension() -> int:
    """Return the dimension of the context feature vector.
    
    Returns
    -------
    int
        Feature dimension (currently 13)
    """
    # bias + agent_hash + user_hash + hour + day + amount + rate + term + 
    # coverage + risk + satisfaction + memory_count + memory_similarity
    return 13


def build_action_space(agent_name: str) -> Dict[str, Any]:
    """Define action space for a given agent.
    
    Parameters
    ----------
    agent_name : str
        Name of the agent
    
    Returns
    -------
    dict
        Action space definition with number of actions and descriptions
    """
    action_spaces = {
        'Lender': {
            'n_actions': 9,
            'actions': [
                'approve_standard',
                'approve_reduced_rate',
                'approve_extended_term',
                'revise_amount_down',
                'revise_amount_up',
                'request_more_info',
                'deny_high_risk',
                'deny_insufficient_income',
                'defer_review'
            ]
        },
        'AlphaTrading': {
            'n_actions': 5,
            'actions': [
                'conservative_allocation',
                'balanced_allocation',
                'growth_allocation',
                'rebalance_defensive',
                'rebalance_aggressive'
            ]
        },
        'SpendingGuard': {
            'n_actions': 4,
            'actions': [
                'no_alert',
                'soft_warning',
                'strong_warning',
                'block_transaction'
            ]
        },
        'BudgetAnalyzer': {
            'n_actions': 5,
            'actions': [
                'no_changes',
                'minor_adjustments',
                'major_reallocation',
                'emergency_mode',
                'savings_optimization'
            ]
        },
        'TaxOptimizer': {
            'n_actions': 4,
            'actions': [
                'standard_deduction',
                'itemized_deduction',
                'retirement_optimization',
                'aggressive_optimization'
            ]
        },
        'ContractReview': {
            'n_actions': 3,
            'actions': [
                'approve_contract',
                'request_revisions',
                'reject_contract'
            ]
        }
    }
    
    return action_spaces.get(agent_name, {'n_actions': 3, 'actions': ['low', 'medium', 'high']})
