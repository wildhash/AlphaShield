"""Example demonstrating agent schema usage.

This example shows how agents should use output schemas before storing
data in MongoDB, ensuring consistent data structures across the system.
"""
from alphashield.schemas import (
    LenderAgentOutput,
    AlphaTradingAgentOutput,
    SpendingGuardAgentOutput,
    BudgetAnalyzerAgentOutput,
    TaxOptimizerAgentOutput,
    ContractReviewAgentOutput,
)


def example_lender_agent():
    """Example: Lender Agent using output schema."""
    print("\n=== Lender Agent Output Schema Example ===")
    
    # Create structured output
    output = LenderAgentOutput(
        borrower_id="borrower_12345",
        loan_id="loan_67890",
        credit_score=720,
        credit_history_length_years=5.5,
        verified_income={
            'annual_gross': 60000.0,
            'monthly_gross': 5000.0,
            'monthly_net': 3800.0
        },
        debt_to_income_ratio=0.35,
        default_risk_score=0.15,
        approved=True
    )
    
    print(f"Borrower ID: {output.borrower_id}")
    print(f"Credit Score: {output.credit_score}")
    print(f"Approved: {output.approved}")
    print(f"Risk Score: {output.default_risk_score}")
    
    return output.to_dict()


def example_trading_agent():
    """Example: Alpha Trading Agent using output schema."""
    print("\n=== Alpha Trading Agent Output Schema Example ===")
    
    output = AlphaTradingAgentOutput(
        loan_id="loan_67890",
        cash_balance=1000.0,
        total_portfolio_value=7200.0,
        months_of_coverage=3.2,
        coverage_adequate=True
    )
    
    print(f"Portfolio Value: ${output.total_portfolio_value:,.2f}")
    print(f"Months of Coverage: {output.months_of_coverage:.1f}")
    
    return output.to_dict()


def main():
    """Run examples."""
    print("=" * 60)
    print("Agent Output Schema Usage Examples")
    print("=" * 60)
    
    lender_data = example_lender_agent()
    trading_data = example_trading_agent()
    
    print(f"\n✓ All schemas ready for MongoDB storage")
    print(f"✓ Lender schema: {len(lender_data)} fields")
    print(f"✓ Trading schema: {len(trading_data)} fields")


if __name__ == '__main__':
    main()
