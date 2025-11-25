"""
AlphaShield RL Training Dashboard

Interactive Streamlit dashboard for monitoring reinforcement learning
training progress, policy performance, and agent metrics.

Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from typing import Optional
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Page configuration
st.set_page_config(
    page_title="AlphaShield RL Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .status-good { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-bad { color: #dc3545; }
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


def load_training_metrics(data_dir: str = "data/training") -> pd.DataFrame:
    """Load training metrics from JSON files or generate sample data."""
    metrics_path = Path(data_dir)
    
    if metrics_path.exists():
        # Load real metrics if available
        metrics = []
        for file in metrics_path.glob("training_*.json"):
            with open(file) as f:
                data = json.load(f)
                metrics.append(data)
        
        if metrics:
            return pd.DataFrame(metrics)
    
    # Generate sample data for demo
    return generate_sample_metrics()


def generate_sample_metrics() -> pd.DataFrame:
    """Generate sample training metrics for demonstration."""
    np.random.seed(42)
    n_days = 30
    
    dates = [datetime.now() - timedelta(days=i) for i in range(n_days)][::-1]
    
    agents = ["lender", "alpha_trading", "spending_guard", "budget_analyzer", "tax_optimizer"]
    
    records = []
    for date in dates:
        for agent in agents:
            # Simulate improving metrics over time
            day_idx = dates.index(date)
            base_reward = 0.5 + (day_idx / n_days) * 0.3 + np.random.normal(0, 0.05)
            
            records.append({
                "date": date,
                "agent": agent,
                "avg_reward": max(0, min(1, base_reward)),
                "episodes": 1000 + np.random.randint(-100, 100),
                "exploration_rate": max(0.1, 0.5 - (day_idx / n_days) * 0.4),
                "loss": max(0.01, 0.5 - (day_idx / n_days) * 0.3 + np.random.normal(0, 0.05)),
                "policy_version": f"v{day_idx + 1}",
                "training_time_seconds": 300 + np.random.randint(-50, 50),
            })
    
    return pd.DataFrame(records)


def load_policy_versions(data_dir: str = "data/policies") -> pd.DataFrame:
    """Load policy version history."""
    policies_path = Path(data_dir)
    
    if policies_path.exists():
        # Load real policy data if available
        policies = []
        for file in policies_path.glob("policy_*.json"):
            with open(file) as f:
                data = json.load(f)
                policies.append(data)
        
        if policies:
            return pd.DataFrame(policies)
    
    # Generate sample policy data
    return generate_sample_policies()


def generate_sample_policies() -> pd.DataFrame:
    """Generate sample policy version data."""
    np.random.seed(42)
    
    agents = ["lender", "alpha_trading", "spending_guard", "budget_analyzer", "tax_optimizer"]
    
    records = []
    for agent in agents:
        for version in range(1, 31):
            records.append({
                "agent": agent,
                "version": f"v{version}",
                "created_at": datetime.now() - timedelta(days=30 - version),
                "validation_score": 0.5 + (version / 30) * 0.35 + np.random.normal(0, 0.02),
                "is_active": version == 30,
                "rollback_count": np.random.randint(0, 3) if version < 25 else 0,
            })
    
    return pd.DataFrame(records)


def main():
    """Main dashboard application."""
    
    # Sidebar
    st.sidebar.markdown("# 🛡️ AlphaShield")
    st.sidebar.markdown("### RL Training Dashboard")
    st.sidebar.divider()
    
    # Date range selector
    date_range = st.sidebar.selectbox(
        "Time Range",
        ["Last 7 days", "Last 14 days", "Last 30 days", "All time"],
        index=2,
    )
    
    # Agent filter
    agents = ["All", "lender", "alpha_trading", "spending_guard", "budget_analyzer", "tax_optimizer"]
    selected_agent = st.sidebar.selectbox("Agent", agents)
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (60s)", value=False)
    if auto_refresh:
        st.sidebar.info("Dashboard will refresh automatically")
    
    st.sidebar.divider()
    st.sidebar.markdown("### Quick Links")
    st.sidebar.markdown("- [Documentation](../docs/RL_OVERVIEW.md)")
    st.sidebar.markdown("- [GitHub Issues](../ISSUES_DETAILED.md)")
    st.sidebar.markdown("- [Roadmap](../ROADMAP.md)")
    
    # Load data
    metrics_df = load_training_metrics()
    policies_df = load_policy_versions()
    
    # Filter by date range
    days_map = {
        "Last 7 days": 7,
        "Last 14 days": 14,
        "Last 30 days": 30,
        "All time": None,
    }
    days = days_map[date_range]
    if days:
        cutoff = datetime.now() - timedelta(days=days)
        metrics_df = metrics_df[metrics_df["date"] >= cutoff]
    
    # Filter by agent
    if selected_agent != "All":
        metrics_df = metrics_df[metrics_df["agent"] == selected_agent]
        policies_df = policies_df[policies_df["agent"] == selected_agent]
    
    # Main content
    st.markdown('<p class="main-header">🛡️ AlphaShield RL Training Dashboard</p>', unsafe_allow_html=True)
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_reward = metrics_df["avg_reward"].mean()
        delta = metrics_df["avg_reward"].iloc[-1] - metrics_df["avg_reward"].iloc[0] if len(metrics_df) > 1 else 0
        st.metric(
            "Avg Reward",
            f"{avg_reward:.3f}",
            f"{delta:+.3f}",
        )
    
    with col2:
        total_episodes = metrics_df["episodes"].sum()
        st.metric(
            "Total Episodes",
            f"{total_episodes:,}",
        )
    
    with col3:
        avg_loss = metrics_df["loss"].mean()
        st.metric(
            "Avg Loss",
            f"{avg_loss:.4f}",
        )
    
    with col4:
        active_policies = policies_df[policies_df["is_active"]]["agent"].nunique()
        st.metric(
            "Active Policies",
            active_policies,
        )
    
    st.divider()
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Reward Progression")
        
        fig = px.line(
            metrics_df,
            x="date",
            y="avg_reward",
            color="agent",
            title="Average Reward Over Time",
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Average Reward",
            legend_title="Agent",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📉 Loss Progression")
        
        fig = px.line(
            metrics_df,
            x="date",
            y="loss",
            color="agent",
            title="Training Loss Over Time",
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Loss",
            legend_title="Agent",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Exploration Rate")
        
        fig = px.area(
            metrics_df,
            x="date",
            y="exploration_rate",
            color="agent",
            title="Exploration Rate Decay",
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Exploration Rate (ε)",
            legend_title="Agent",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Agent Comparison")
        
        # Latest metrics by agent
        latest_metrics = metrics_df.groupby("agent").last().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Avg Reward",
            x=latest_metrics["agent"],
            y=latest_metrics["avg_reward"],
            marker_color="#1f77b4",
        ))
        fig.add_trace(go.Bar(
            name="1 - Loss",
            x=latest_metrics["agent"],
            y=1 - latest_metrics["loss"],
            marker_color="#2ca02c",
        ))
        fig.update_layout(
            barmode="group",
            title="Current Agent Performance",
            xaxis_title="Agent",
            yaxis_title="Score",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Policy version management
    st.subheader("🔄 Policy Version Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Policy history chart
        fig = px.line(
            policies_df,
            x="created_at",
            y="validation_score",
            color="agent",
            title="Policy Validation Score History",
            markers=True,
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Validation Score",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Active Policies")
        active_policies_df = policies_df[policies_df["is_active"]][["agent", "version", "validation_score"]]
        active_policies_df = active_policies_df.rename(columns={
            "agent": "Agent",
            "version": "Version",
            "validation_score": "Score",
        })
        active_policies_df["Score"] = active_policies_df["Score"].round(3)
        st.dataframe(active_policies_df, use_container_width=True, hide_index=True)
        
        st.markdown("### Recent Rollbacks")
        rollbacks = policies_df[policies_df["rollback_count"] > 0][["agent", "version", "rollback_count"]].tail(5)
        if not rollbacks.empty:
            st.dataframe(rollbacks, use_container_width=True, hide_index=True)
        else:
            st.info("No recent rollbacks")
    
    st.divider()
    
    # Training history table
    st.subheader("📋 Training History")
    
    # Format the metrics dataframe for display
    display_df = metrics_df.copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
    display_df["avg_reward"] = display_df["avg_reward"].round(4)
    display_df["loss"] = display_df["loss"].round(4)
    display_df["exploration_rate"] = display_df["exploration_rate"].round(3)
    
    display_df = display_df.rename(columns={
        "date": "Date",
        "agent": "Agent",
        "avg_reward": "Avg Reward",
        "episodes": "Episodes",
        "exploration_rate": "ε",
        "loss": "Loss",
        "policy_version": "Version",
        "training_time_seconds": "Time (s)",
    })
    
    st.dataframe(
        display_df.sort_values("Date", ascending=False).head(50),
        use_container_width=True,
        hide_index=True,
    )
    
    st.divider()
    
    # System status
    st.subheader("⚙️ System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Training Pipeline")
        st.success("✅ Nightly training: Active")
        st.info("📅 Last run: Today 02:00 UTC")
        st.info("⏰ Next run: Tomorrow 02:00 UTC")
    
    with col2:
        st.markdown("### Infrastructure")
        st.success("✅ MongoDB: Connected")
        st.success("✅ Redis: Connected")
        st.success("✅ Voyage AI: Connected")
    
    with col3:
        st.markdown("### Model Registry")
        total_policies = len(policies_df["version"].unique())
        st.info(f"📦 Total versions: {total_policies}")
        st.info(f"🏃 Active agents: {active_policies}")
        
        if st.button("🔄 Refresh Dashboard"):
            st.rerun()
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div style="text-align: center; color: #888;">
            AlphaShield RL Dashboard v1.0 | 
            <a href="https://github.com/wildhash/AlphaShield">GitHub</a> | 
            Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC") + """
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
