"""Demo script for orchestration system.

NOTE: This script uses synthetic/demo data for illustration purposes only.
All user IDs, loan IDs, and trace IDs are non-sensitive test identifiers.
"""
import os
os.environ['USE_RL'] = 'false'
os.environ['QUANTUM'] = 'false'

from alphashield.orchestrator import execute
from alphashield.agents.spending_guard.agent import SpendingGuardAgent


def demo_orchestration():
    """Demonstrate the orchestration system with synthetic data."""
    print("=" * 60)
    print("AlphaShield Orchestration Demo")
    print("=" * 60)
    print()
    
    # Execute orchestrator without DB (using synthetic stub data)
    # NOTE: Using demo identifiers, not real user data
    print("1. Executing orchestrator DAG...")
    bundle = execute(
        trace_id='demo_trace_001',  # Synthetic trace ID for demo
        user_id='demo_user_123',  # Synthetic user ID for demo
        loan_app_id='demo_loan_456'  # Synthetic loan ID for demo
    )
    
    print(f"   ✓ Trace ID: {bundle.trace_id}")
    print(f"   ✓ User ID: {bundle.user_id}")
    print(f"   ✓ Loan App ID: {bundle.loan_app_id}")
    print()
    
    # Show audit trail
    print("2. Audit Trail:")
    for i, event in enumerate(bundle.audit_trail, 1):
        print(f"   {i}. {event['node']:20s} - {event['status']:8s} - Hash: {event['input_hash']}")
    print()
    
    # Show underwriting results
    print("3. Underwriting Results:")
    print(f"   Approved: {bundle.underwriting.get('approved')}")
    print(f"   Credit Score: {bundle.underwriting.get('credit_score')}")
    print(f"   Max Loan Amount: ${bundle.underwriting.get('max_loan_amount'):,.2f}")
    print()
    
    # Show coverage ratio
    print("4. Risk Bridge (Portfolio):")
    print(f"   Coverage Ratio: {bundle.coverage.get('coverage_ratio'):.2f}")
    print(f"   Risk Level: {bundle.coverage.get('risk_level')}")
    print("   Allocation:")
    for asset, weight in bundle.coverage.get('allocation', {}).items():
        print(f"      {asset:20s}: {weight*100:5.1f}%")
    print()
    
    # Show offer
    print("5. Offer:")
    print(f"   Principal: ${bundle.offer.get('principal'):,.2f}")
    print(f"   Interest Rate: {bundle.offer.get('interest_rate'):.1f}%")
    print(f"   Term: {bundle.offer.get('term_months')} months")
    print(f"   Monthly Payment: ${bundle.offer.get('monthly_payment'):,.2f}")
    print()
    
    # Show compliance
    print("6. Compliance:")
    print(f"   Compliant: {bundle.compliance.get('compliant')}")
    for check, passed in bundle.compliance.get('checks', {}).items():
        status = "✓" if passed else "✗"
        print(f"   {status} {check}")
    print()


def demo_spending_guard():
    """Demonstrate the spending guard."""
    print("=" * 60)
    print("Spending Guard Demo")
    print("=" * 60)
    print()
    
    agent = SpendingGuardAgent()
    
    # Simulate transactions with an anomaly
    transactions = [
        {'category': 'groceries', 'amount': 150.0, 'date': '2024-01-01'},
        {'category': 'groceries', 'amount': 145.0, 'date': '2024-01-08'},
        {'category': 'groceries', 'amount': 155.0, 'date': '2024-01-15'},
        {'category': 'groceries', 'amount': 148.0, 'date': '2024-01-22'},
        {'category': 'groceries', 'amount': 800.0, 'date': '2024-01-29'},  # Anomaly
        {'category': 'dining', 'amount': 50.0, 'date': '2024-01-05'},
        {'category': 'dining', 'amount': 45.0, 'date': '2024-01-12'},
        {'category': 'gambling', 'amount': 200.0, 'date': '2024-01-20'},  # High risk
    ]
    
    print("Analyzing transactions...")
    events = agent.analyze_transactions(transactions)
    
    print(f"Found {len(events)} events:")
    print()
    
    for i, event in enumerate(events, 1):
        print(f"{i}. {event.event_type.upper()}")
        print(f"   Severity: {event.severity}")
        print(f"   Suggested Action: {event.suggested_action}")
        if event.category:
            print(f"   Category: {event.category}")
        if event.amount:
            print(f"   Amount: ${event.amount:,.2f}")
        if event.deviation:
            print(f"   Deviation: {event.deviation:.2f}x")
        print()


if __name__ == '__main__':
    demo_orchestration()
    print()
    demo_spending_guard()
