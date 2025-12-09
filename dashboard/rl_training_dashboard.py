"""Streamlit dashboard for monitoring RL training and model health.

Usage:
    streamlit run dashboard/rl_training_dashboard.py
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alphashield.database.mongodb_client import get_mongo_client
from alphashield.rl.policy import PolicyManager


# Page configuration
st.set_page_config(
    page_title="AlphaShield RL Training Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
.big-metric {
    font-size: 2.5rem;
    font-weight: bold;
}
.success-metric {
    color: #28a745;
}
.warning-metric {
    color: #ffc107;
}
.danger-metric {
    color: #dc3545;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db_client():
    """Get MongoDB client (cached)."""
    return get_mongo_client()


@st.cache_data(ttl=60)
def load_training_runs(days: int = 30) -> pd.DataFrame:
    """Load training run history."""
    db = get_db_client()
    
    if not hasattr(db, 'get_collection'):
        return pd.DataFrame()
    
    collection = db.get_collection('training_runs')
    if collection is None:
        return pd.DataFrame()
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    runs = list(collection.find({
        'started_at': {'$gte': cutoff}
    }).sort('started_at', -1))
    
    if not runs:
        return pd.DataFrame()
    
    # Flatten results for analysis
    rows = []
    for run in runs:
        for agent, result in run.get('results', {}).items():
            rows.append({
                'date': run['started_at'],
                'agent': agent,
                'status': result.get('status', 'unknown'),
                'improvement': result.get('improvement', 0) * 100,
                'samples': result.get('samples', 0),
                'deployed': result.get('deployed', False),
                'current_version': result.get('current_version', 0),
                'new_version': result.get('new_version', 0),
            })
    
    return pd.DataFrame(rows)


@st.cache_data(ttl=60)
def load_policies() -> Dict[str, dict]:
    """Load current policies for all agents."""
    db = get_db_client()
    policy_manager = PolicyManager(db)
    
    agents = ['Lender', 'AlphaTrading', 'SpendingGuard', 'BudgetAnalyzer', 'TaxOptimizer', 'ContractReview']
    
    policies = {}
    for agent in agents:
        policy = policy_manager.load_policy(agent)
        if policy:
            policies[agent] = {
                'version': policy.version,
                'algorithm': policy.algorithm,
                'created_at': policy.created_at,
                'metadata': policy.metadata,
            }
    
    return policies


@st.cache_data(ttl=60)
def load_replay_buffer_stats() -> Dict[str, int]:
    """Get replay buffer statistics."""
    db = get_db_client()
    
    if not hasattr(db, 'get_collection'):
        return {}
    
    collection = db.get_collection('replay_buffer')
    if collection is None:
        return {}
    
    # Get counts per agent
    pipeline = [
        {'$group': {
            '_id': '$agent',
            'count': {'$sum': 1},
            'avg_reward': {'$avg': '$reward'}
        }}
    ]
    
    results = list(collection.aggregate(pipeline))
    
    return {
        item['_id']: {
            'samples': item['count'],
            'avg_reward': item.get('avg_reward', 0)
        }
        for item in results
    }


def main():
    """Main dashboard."""
    
    # Header
    st.title("🎓 AlphaShield RL Training Dashboard")
    st.markdown("Real-time monitoring of reinforcement learning training and model health")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    days = st.sidebar.slider("Training History (days)", 7, 90, 30)
    selected_agents = st.sidebar.multiselect(
        "Agents",
        ['All', 'Lender', 'AlphaTrading', 'SpendingGuard', 'BudgetAnalyzer', 'TaxOptimizer', 'ContractReview'],
        default=['All']
    )
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Load data
    with st.spinner("Loading training data..."):
        training_runs = load_training_runs(days)
        policies = load_policies()
        replay_stats = load_replay_buffer_stats()
    
    # Overview metrics
    st.header("📊 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_runs = len(training_runs) if not training_runs.empty else 0
        st.metric("Total Training Runs", total_runs, help="Last 30 days")
    
    with col2:
        successful = len(training_runs[training_runs['status'] == 'success']) if not training_runs.empty else 0
        success_rate = (successful / total_runs * 100) if total_runs > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%", help="Successful training runs")
    
    with col3:
        deployed = len(training_runs[training_runs['deployed'] == True]) if not training_runs.empty else 0
        st.metric("Policies Deployed", deployed, help="New policies deployed")
    
    with col4:
        avg_improvement = training_runs['improvement'].mean() if not training_runs.empty else 0
        st.metric("Avg Improvement", f"{avg_improvement:.2f}%", help="Average policy improvement")
    
    # Current Policies
    st.header("📋 Current Policies")
    
    if policies:
        policy_data = []
        for agent, policy_info in policies.items():
            policy_data.append({
                'Agent': agent,
                'Version': policy_info['version'],
                'Algorithm': policy_info['algorithm'],
                'Last Updated': policy_info['created_at'].strftime('%Y-%m-%d %H:%M') if policy_info['created_at'] else 'N/A',
            })
        
        st.dataframe(
            pd.DataFrame(policy_data),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No policies found. Run training to create policies.")
    
    # Training History
    st.header("📈 Training History")
    
    if not training_runs.empty:
        # Filter by selected agents
        if 'All' not in selected_agents:
            training_runs = training_runs[training_runs['agent'].isin(selected_agents)]
        
        # Improvement over time
        fig_improvement = px.line(
            training_runs,
            x='date',
            y='improvement',
            color='agent',
            title='Policy Improvement Over Time',
            labels={'improvement': 'Improvement (%)', 'date': 'Date'},
        )
        fig_improvement.add_hline(y=5.0, line_dash="dash", line_color="green", annotation_text="Deployment Threshold")
        st.plotly_chart(fig_improvement, use_container_width=True)
        
        # Training samples distribution
        fig_samples = px.box(
            training_runs,
            x='agent',
            y='samples',
            color='agent',
            title='Training Samples Distribution by Agent',
            labels={'samples': 'Number of Samples'},
        )
        st.plotly_chart(fig_samples, use_container_width=True)
        
        # Deployment rate by agent
        deployment_rate = training_runs.groupby('agent')['deployed'].agg(['sum', 'count'])
        deployment_rate['rate'] = (deployment_rate['sum'] / deployment_rate['count'] * 100).round(1)
        
        fig_deployment = px.bar(
            deployment_rate.reset_index(),
            x='agent',
            y='rate',
            title='Deployment Rate by Agent',
            labels={'rate': 'Deployment Rate (%)'},
            color='rate',
            color_continuous_scale='RdYlGn',
        )
        st.plotly_chart(fig_deployment, use_container_width=True)
        
    else:
        st.info("No training runs found in the selected period.")
    
    # Replay Buffer Health
    st.header("💾 Replay Buffer Health")
    
    if replay_stats:
        buffer_data = []
        for agent, stats in replay_stats.items():
            status = "✅ Healthy" if stats['samples'] >= 100 else "⚠️ Low Samples"
            buffer_data.append({
                'Agent': agent,
                'Samples': stats['samples'],
                'Avg Reward': f"{stats['avg_reward']:.3f}",
                'Status': status,
            })
        
        st.dataframe(
            pd.DataFrame(buffer_data),
            use_container_width=True,
            hide_index=True,
        )
        
        # Visualize sample counts
        df_buffer = pd.DataFrame(buffer_data)
        fig_buffer = px.bar(
            df_buffer,
            x='Agent',
            y='Samples',
            title='Replay Buffer Sample Counts',
            color='Samples',
            color_continuous_scale='Blues',
        )
        fig_buffer.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Minimum Threshold")
        st.plotly_chart(fig_buffer, use_container_width=True)
        
    else:
        st.warning("No replay buffer data found. System may not be collecting experiences.")
    
    # Model Health Alerts
    st.header("⚠️ Health Alerts")
    
    alerts = []
    
    # Check for agents with insufficient samples
    for agent, stats in replay_stats.items():
        if stats['samples'] < 100:
            alerts.append({
                'severity': 'warning',
                'agent': agent,
                'message': f"Insufficient training samples ({stats['samples']}/100 minimum)",
            })
    
    # Check for agents with low deployment rate
    if not training_runs.empty:
        for agent in training_runs['agent'].unique():
            agent_runs = training_runs[training_runs['agent'] == agent]
            deployed_count = agent_runs['deployed'].sum()
            deployment_rate = deployed_count / len(agent_runs) * 100
            
            if deployment_rate < 10 and len(agent_runs) >= 5:
                alerts.append({
                    'severity': 'info',
                    'agent': agent,
                    'message': f"Low deployment rate ({deployment_rate:.1f}%). Policies may not be improving.",
                })
    
    # Check for agents with negative average improvement
    if not training_runs.empty:
        avg_by_agent = training_runs.groupby('agent')['improvement'].mean()
        for agent, avg_imp in avg_by_agent.items():
            if avg_imp < 0:
                alerts.append({
                    'severity': 'error',
                    'agent': agent,
                    'message': f"Negative average improvement ({avg_imp:.2f}%). Check training data quality.",
                })
    
    if alerts:
        for alert in alerts:
            if alert['severity'] == 'error':
                st.error(f"🚨 **{alert['agent']}**: {alert['message']}")
            elif alert['severity'] == 'warning':
                st.warning(f"⚠️ **{alert['agent']}**: {alert['message']}")
            else:
                st.info(f"ℹ️ **{alert['agent']}**: {alert['message']}")
    else:
        st.success("✅ All systems healthy! No alerts.")
    
    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")


if __name__ == "__main__":
    main()
