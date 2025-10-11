"""Example usage of AlphaShield multi-agent loan system."""
import os
from dotenv import load_dotenv
from alphashield.orchestrator import AlphaShieldOrchestrator

# Load environment variables
load_dotenv()


def main():
    """Demonstrate AlphaShield system with a complete loan lifecycle."""
    
    print("=" * 70)
    print("AlphaShield: Self-Funding Loans with Multi-Agent AI")
    print("Eliminating the Poverty Tax: 8% vs 24% Predatory Rates")
    print("=" * 70)
    
    # Initialize AlphaShield (requires MongoDB and Voyage AI credentials)
    # For demo purposes, we'll show the structure without actual API calls
    try:
        shield = AlphaShieldOrchestrator(
            mongodb_uri=os.getenv('MONGODB_URI'),
            voyage_api_key=os.getenv('VOYAGE_API_KEY')
        )
        print("\n✓ AlphaShield initialized with 6 AI agents:")
        print("  1. Lender - Loan origination and portfolio management")
        print("  2. Alpha Trading - 60% algorithmic investment")
        print("  3. Spending Guard - Anomaly detection")
        print("  4. Budget Analyzer - Budget optimization")
        print("  5. Tax Optimizer - Tax strategy")
        print("  6. Contract Review - Contract analysis")
        
    except Exception as e:
        print(f"\n⚠ Demo mode: {e}")
        print("\nTo run with real agents, set environment variables:")
        print("  - MONGODB_URI: MongoDB Atlas connection string")
        print("  - VOYAGE_API_KEY: Voyage AI API key")
        print("\nShowing system architecture instead...\n")
        demonstrate_architecture()
        return
    
    # Example: Originate a $10,000 loan at 8% for 36 months
    print("\n" + "=" * 70)
    print("STEP 1: Loan Origination")
    print("=" * 70)
    
    borrower_id = "borrower_123"
    principal = 10000
    
    # Contract terms for review
    contract_terms = {
        'interest_rate': 8.0,
        'term_months': 36,
        'fees': {
            'origination': 200,  # 2% origination fee
            'processing': 0,
        },
        'penalties': {
            'prepayment': 0,  # No prepayment penalty
            'late_payment': 25,
        }
    }
    
    result = shield.originate_loan(
        borrower_id=borrower_id,
        principal=principal,
        interest_rate=8.0,
        term_months=36,
        contract_terms=contract_terms
    )
    
    if result['status'] == 'success':
        loan_id = result['loan_id']
        print(f"\n✓ Loan originated successfully!")
        print(f"  Loan ID: {loan_id}")
        print(f"  Principal: ${principal:,.2f}")
        print(f"  Interest Rate: 8% (vs 24% predatory rate)")
        print(f"\n  Loan Split (60/40 Model):")
        print(f"    Investment Fund: ${result['split']['investment']:,.2f} (60%)")
        print(f"    To Borrower: ${result['split']['borrower']:,.2f} (40%)")
        
        inv_plan = result['investment_plan']
        print(f"\n  Investment Strategy: {inv_plan.get('strategy', 'N/A').title()}")
        print(f"    Expected Annual Return: {inv_plan.get('expected_annual_return', 0)*100:.1f}%")
        print(f"    Expected Monthly Return: ${inv_plan.get('expected_monthly_return', 0):,.2f}")
        print(f"    Monthly Payment Needed: ${inv_plan.get('monthly_payment_needed', 0):,.2f}")
        print(f"    Coverage Ratio: {inv_plan.get('coverage_ratio', 0):.2f}x")
        
        # Example: Monitor loan with borrower data
        print("\n" + "=" * 70)
        print("STEP 2: Ongoing Monitoring")
        print("=" * 70)
        
        borrower_data = {
            'income': 4500,  # Monthly income
            'expenses': {
                'housing': 1200,
                'utilities': 200,
                'food': 400,
                'transportation': 300,
                'insurance': 250,
                'entertainment': 200,
                'other': 150,
            },
            'transactions': [
                {'amount': 150, 'category': 'food', 'timestamp': '2024-01-15'},
                {'amount': 80, 'category': 'entertainment', 'timestamp': '2024-01-16'},
                {'amount': 1200, 'category': 'housing', 'timestamp': '2024-01-01'},
                {'amount': 50, 'category': 'utilities', 'timestamp': '2024-01-10'},
            ],
            'deductions': {
                'retirement': 500,
                'mortgage_interest': 0,
                'charitable': 100,
            },
            'filing_status': 'single'
        }
        
        monitoring = shield.monitor_loan(loan_id, borrower_data)
        
        print("\n📊 Portfolio Metrics:")
        portfolio = monitoring['portfolio_metrics']
        print(f"  Status: {portfolio.get('status', 'N/A')}")
        print(f"  Outstanding Balance: ${portfolio.get('outstanding_balance', 0):,.2f}")
        print(f"  Investment Balance: ${portfolio.get('investment_balance', 0):,.2f}")
        
        print("\n📈 Investment Performance:")
        inv_perf = monitoring['investment']['performance']
        print(f"  Current Value: ${inv_perf.get('investment_balance', 0):,.2f}")
        print(f"  Period Return: ${inv_perf.get('period_return', 0):,.2f}")
        print(f"  Status: {inv_perf.get('performance', 'N/A')}")
        
        if monitoring['budget_analysis']:
            print("\n💰 Budget Analysis:")
            budget = monitoring['budget_analysis']
            print(f"  Monthly Income: ${budget.get('monthly_income', 0):,.2f}")
            print(f"  Total Expenses: ${budget.get('total_expenses', 0):,.2f}")
            print(f"  Discretionary Income: ${budget.get('discretionary_income', 0):,.2f}")
            print(f"  Budget Health: {budget.get('budget_health', 'N/A')}")
            print(f"  Loan Payment Affordable: {budget.get('payment_affordable', False)}")
        
        if monitoring['tax_optimization']:
            print("\n📋 Tax Optimization:")
            tax = monitoring['tax_optimization']
            print(f"  Estimated Tax: ${tax.get('estimated_tax', 0):,.2f}")
            print(f"  Effective Rate: {tax.get('effective_rate', 0):.1f}%")
            print(f"  Potential Savings: ${tax.get('potential_annual_savings', 0):,.2f}/year")
        
        # Get recommendations
        print("\n" + "=" * 70)
        print("STEP 3: AI-Generated Recommendations")
        print("=" * 70)
        
        recommendations = shield.get_borrower_recommendations(loan_id)
        
        if recommendations.get('spending_recommendations'):
            print("\n🛡️ Spending Guard Recommendations:")
            for rec in recommendations['spending_recommendations']:
                print(f"  • {rec}")
        
        if recommendations.get('budget_recommendations'):
            print("\n💡 Budget Analyzer Recommendations:")
            for rec in recommendations['budget_recommendations']:
                print(f"  • {rec}")
        
        if recommendations.get('tax_recommendations'):
            print("\n📊 Tax Optimizer Recommendations:")
            tax_rec = recommendations['tax_recommendations']
            if tax_rec.get('short_term'):
                print("  Short-term actions:")
                for action in tax_rec['short_term']:
                    print(f"    • {action.get('action', 'N/A')}")
            if tax_rec.get('long_term'):
                print("  Long-term actions:")
                for action in tax_rec['long_term']:
                    print(f"    • {action.get('action', 'N/A')}")
        
        print("\n" + "=" * 70)
        print("IMPACT SUMMARY")
        print("=" * 70)
        print(f"\n💵 Savings vs Predatory Lender (24% rate):")
        print(f"  AlphaShield Rate: 8%")
        print(f"  Predatory Rate: 24%")
        print(f"  Rate Difference: 16 percentage points")
        
        # Calculate savings
        alphashield_interest = principal * 0.08 * (36/12)
        predatory_interest = principal * 0.24 * (36/12)
        savings = predatory_interest - alphashield_interest
        
        print(f"\n  AlphaShield Interest (3 years): ${alphashield_interest:,.2f}")
        print(f"  Predatory Interest (3 years): ${predatory_interest:,.2f}")
        print(f"  💰 TOTAL SAVINGS: ${savings:,.2f}")
        
        print("\n✨ Key Innovations:")
        print("  ✓ 60% of loan self-invests to cover payments")
        print("  ✓ 6 AI agents work together via shared context")
        print("  ✓ Real-time monitoring and recommendations")
        print("  ✓ Eliminating the poverty tax")
        
        shield.close()
        
    else:
        print(f"\n✗ Loan not approved: {result.get('reason', 'Unknown')}")


def demonstrate_architecture():
    """Show system architecture when APIs not available."""
    print("=" * 70)
    print("ALPHASHIELD ARCHITECTURE")
    print("=" * 70)
    
    print("\n📊 Multi-Agent System:")
    print("""
    ┌─────────────────────────────────────────────────────────┐
    │                    AlphaShield                          │
    │              Self-Funding Loan System                   │
    └─────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴──────────────┐
                │                            │
         ┌──────▼──────┐            ┌───────▼───────┐
         │   MongoDB   │            │   Voyage AI   │
         │   Atlas     │            │  Embeddings   │
         │  (Context)  │            │   (Search)    │
         └──────┬──────┘            └───────┬───────┘
                │                            │
    ────────────┴────────────────────────────┴───────────────
                    Shared Context Layer
    ─────────────────────────────────────────────────────────
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
    ┌───▼───┐  ┌─────▼─────┐ ┌──▼───┐  ┌──────▼──────┐
    │Lender │  │  Alpha    │ │Budget│  │  Spending   │
    │Agent  │  │  Trading  │ │Analyz│  │   Guard     │
    └───┬───┘  └─────┬─────┘ └──┬───┘  └──────┬──────┘
        │            │           │             │
        └────────────┼───────────┼─────────────┘
                     │           │
              ┌──────▼───┐  ┌───▼──────┐
              │   Tax    │  │ Contract │
              │Optimizer │  │  Review  │
              └──────────┘  └──────────┘
    """)
    
    print("\n💡 Loan Split (60/40 Model):")
    print("  $10,000 Loan Example:")
    print("    ├─ $6,000 (60%) → Investment Fund")
    print("    │   └─ Generates returns to cover payments")
    print("    └─ $4,000 (40%) → To Borrower")
    
    print("\n🎯 Mission:")
    print("  Replace 24% predatory rates with 8% self-sustaining loans")
    print("  Eliminate the poverty tax through AI-powered finance")


if __name__ == "__main__":
    main()
