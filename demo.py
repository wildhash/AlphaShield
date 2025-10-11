"""Simple demo of AlphaShield system without external dependencies."""
from alphashield.models.loan import Loan, LoanSplit


def main():
    """Demonstrate AlphaShield core concepts."""
    
    print("=" * 70)
    print("AlphaShield: Self-Funding Loans with Multi-Agent AI")
    print("Eliminating the Poverty Tax: 8% vs 24% Predatory Rates")
    print("=" * 70)
    
    # Demonstrate the 60/40 split
    print("\n" + "=" * 70)
    print("THE 60/40 MODEL")
    print("=" * 70)
    
    principal = 10000
    split = LoanSplit.from_total(principal)
    
    print(f"\nLoan Amount: ${principal:,.2f}")
    print(f"\nSplit Allocation:")
    print(f"  ├─ Investment Fund (60%): ${split.investment_amount:,.2f}")
    print(f"  │   └─ Invests algorithmically to generate returns")
    print(f"  └─ To Borrower (40%):     ${split.borrower_amount:,.2f}")
    print(f"      └─ Available for immediate use")
    
    # Create a sample loan
    print("\n" + "=" * 70)
    print("LOAN EXAMPLE")
    print("=" * 70)
    
    loan = Loan(
        borrower_id="borrower_123",
        principal=principal,
        interest_rate=8.0,
        term_months=36
    )
    
    print(f"\nBorrower ID: {loan.borrower_id}")
    print(f"Principal: ${loan.principal:,.2f}")
    print(f"Interest Rate: {loan.interest_rate}%")
    print(f"Term: {loan.term_months} months")
    print(f"\nMonthly Payment: ${loan.monthly_payment:.2f}")
    print(f"Total to Repay: ${loan.monthly_payment * loan.term_months:,.2f}")
    
    # Calculate savings vs predatory lender
    print("\n" + "=" * 70)
    print("SAVINGS vs PREDATORY LENDER")
    print("=" * 70)
    
    predatory_loan = Loan(
        borrower_id="borrower_123",
        principal=principal,
        interest_rate=24.0,
        term_months=36
    )
    
    alphashield_total = loan.monthly_payment * loan.term_months
    predatory_total = predatory_loan.monthly_payment * predatory_loan.term_months
    
    alphashield_interest = alphashield_total - principal
    predatory_interest = predatory_total - principal
    
    savings = predatory_total - alphashield_total
    
    print(f"\n{'':20} AlphaShield (8%)  Predatory (24%)")
    print(f"{'─' * 60}")
    print(f"{'Principal:':20} ${principal:>12,.2f}  ${principal:>12,.2f}")
    print(f"{'Monthly Payment:':20} ${loan.monthly_payment:>12,.2f}  ${predatory_loan.monthly_payment:>12,.2f}")
    print(f"{'Total Interest:':20} ${alphashield_interest:>12,.2f}  ${predatory_interest:>12,.2f}")
    print(f"{'Total Paid:':20} ${alphashield_total:>12,.2f}  ${predatory_total:>12,.2f}")
    print(f"\n💰 TOTAL SAVINGS: ${savings:,.2f}")
    print(f"   (That's {(savings/predatory_total)*100:.1f}% less than predatory rates!)")
    
    # Investment strategy
    print("\n" + "=" * 70)
    print("INVESTMENT STRATEGY")
    print("=" * 70)
    
    investment_amount = split.investment_amount
    
    print(f"\nInvestment Fund: ${investment_amount:,.2f}")
    print(f"\nBalanced Strategy Allocation:")
    print(f"  ├─ Bonds (30%):          ${investment_amount * 0.30:,.2f}")
    print(f"  ├─ Index Funds (40%):    ${investment_amount * 0.40:,.2f}")
    print(f"  ├─ Dividend Stocks (20%): ${investment_amount * 0.20:,.2f}")
    print(f"  └─ Growth Stocks (10%):  ${investment_amount * 0.10:,.2f}")
    
    # Expected returns
    expected_return = 0.10  # 10% annual
    monthly_return = (investment_amount * expected_return) / 12
    coverage = monthly_return / loan.monthly_payment
    
    print(f"\nExpected Performance:")
    print(f"  Annual Return Rate: {expected_return*100:.1f}%")
    print(f"  Expected Monthly Return: ${monthly_return:.2f}")
    print(f"  Monthly Payment: ${loan.monthly_payment:.2f}")
    print(f"  Coverage Ratio: {coverage:.2%}")
    print(f"\n  Note: Investment returns help offset loan costs,")
    print(f"        making the 8% rate even more affordable!")
    
    # The 6 AI Agents
    print("\n" + "=" * 70)
    print("SIX AI AGENTS")
    print("=" * 70)
    
    agents = [
        ("Lender", "Originates loans and manages portfolio"),
        ("Alpha Trading", "Invests 60% algorithmically"),
        ("Spending Guard", "Detects spending anomalies"),
        ("Budget Analyzer", "Optimizes borrower budget"),
        ("Tax Optimizer", "Identifies tax savings"),
        ("Contract Review", "Analyzes loan fairness"),
    ]
    
    print("\nAll agents share context via MongoDB Atlas & Voyage AI embeddings:")
    for i, (name, description) in enumerate(agents, 1):
        print(f"  {i}. {name:20} - {description}")
    
    # Impact summary
    print("\n" + "=" * 70)
    print("SOCIAL IMPACT")
    print("=" * 70)
    
    print("\n🎯 Mission: Eliminate the Poverty Tax")
    print("\n   Predatory lenders charge 24%+ interest rates, trapping")
    print("   borrowers in cycles of debt. AlphaShield uses AI and")
    print("   algorithmic investment to offer 8% rates, saving borrowers")
    print("   thousands of dollars.")
    
    print("\n✨ Key Benefits:")
    print("   ✓ 70% lower interest rates (8% vs 24%)")
    print("   ✓ AI-powered financial guidance")
    print("   ✓ Investment education through participation")
    print("   ✓ Real-time spending and budget monitoring")
    print("   ✓ Tax optimization strategies")
    print("   ✓ Self-sustaining loan model")
    
    print("\n📈 Example Impact:")
    print(f"   With a ${principal:,} loan over 3 years:")
    print(f"   • Save ${savings:,.2f} vs predatory lender")
    print(f"   • Build ${split.investment_amount:,.2f} investment portfolio")
    print(f"   • Receive ongoing AI financial guidance")
    print(f"   • Avoid debt trap and build wealth instead")
    
    print("\n" + "=" * 70)
    print("\nAlphaShield: Making finance work for everyone. 💰🛡️")
    print("=" * 70)


if __name__ == "__main__":
    main()
