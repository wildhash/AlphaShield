"""Example showing how agents integrate with output schemas.

This demonstrates the pattern agents should follow when using schemas
to ensure data consistency before MongoDB storage.
"""
from unittest.mock import MagicMock
from alphashield.schemas import (
    LenderAgentOutput,
    SpendingGuardAgentOutput,
)
from alphashield.agents.base_agent import BaseAgent


class ExampleLenderAgentWithSchema(BaseAgent):
    """Example showing how Lender Agent would use output schema."""
    
    def process(self, loan_id: str, **kwargs) -> dict:
        """Process loan with schema output."""
        # Get loan data
        loan_data = self.get_loan(loan_id)
        if not loan_data:
            return {'error': 'Loan not found'}
        
        # Perform underwriting analysis
        # (In production, this would extract data from documents)
        borrower_id = loan_data.get('borrower_id')
        
        # Create structured output using schema
        output = LenderAgentOutput(
            borrower_id=borrower_id,
            loan_id=loan_id,
            
            # Credit metrics (from Credit Report)
            credit_score=720,
            credit_history_length_years=5.5,
            total_credit_accounts=8,
            derogatory_marks=0,
            
            # Payment history (from Credit Card Statements)
            payment_history={
                'on_time_count': 24,
                'late_count': 0,
                'missed_count': 0
            },
            credit_utilization=0.30,
            
            # Income verification (from W-2 + Pay Stub)
            verified_income={
                'annual_gross': 60000.0,
                'monthly_gross': 5000.0,
                'monthly_net': 3800.0
            },
            employment_length_years=3.0,
            employer_name="Tech Corp Inc",
            
            # Calculated metrics
            debt_to_income_ratio=0.35,
            spending_to_income_ratio=0.65,
            default_risk_score=0.15,
            approved_loan_amount_max=15000.0,
            
            # Decision
            approved=True,
            approval_conditions=["Verify employment", "Set up auto-payment"]
        )
        
        # Store using new structured output method
        # This automatically validates and converts to dict
        self.store_structured_output('lender_assessment', output, generate_embedding=True)
        
        # Also return dict for backwards compatibility
        return output.to_dict()


class ExampleSpendingGuardWithSchema(BaseAgent):
    """Example showing how Spending Guard would use output schema."""
    
    def process(self, loan_id: str, **kwargs) -> dict:
        """Process spending analysis with schema output."""
        loan_data = self.get_loan(loan_id)
        if not loan_data:
            return {'error': 'Loan not found'}
        
        borrower_id = loan_data.get('borrower_id')
        transactions = kwargs.get('transactions', [])
        
        # Analyze spending
        # (In production, this would analyze transaction data from statements)
        
        # Create structured output using schema
        output = SpendingGuardAgentOutput(
            borrower_id=borrower_id,
            loan_id=loan_id,
            
            # Transaction summary
            total_transactions=len(transactions),
            analysis_period_months=12,
            
            # Category spending
            category_spending={
                'food': 500.0,
                'entertainment': 300.0,
                'transportation': 200.0
            },
            
            # Statistics
            category_statistics={
                'food': {
                    'mean': 450.0,
                    'std_dev': 75.0,
                    'anomaly_threshold': 600.0
                }
            },
            
            # High-risk spending
            high_risk_categories={'gambling': 0.0, 'luxury': 0.0},
            high_risk_ratio=0.0,
            
            # Anomalies
            anomalies_detected=[],
            anomaly_count=0,
            
            # Alert
            alert_level="normal",
            alert_reasons=[],
            spending_recommendations=["Spending patterns appear normal"]
        )
        
        # Store using structured output method
        self.store_structured_output('spending_analysis', output, generate_embedding=True)
        
        return output.to_dict()


def demonstrate_old_way():
    """Show the old way without schemas (unstructured)."""
    print("\n=== OLD WAY (Unstructured Dict) ===")
    print("Problems:")
    print("- No type safety")
    print("- Inconsistent field names")
    print("- Missing required fields not caught")
    print("- Hard to validate")
    
    # Old unstructured dict
    old_output = {
        'borrower': 'borrower_123',  # Inconsistent naming
        'score': 720,  # Unclear what type of score
        'approved': True,
        # Missing: debt_to_income_ratio, risk_score, etc.
    }
    print(f"\nOld output: {old_output}")
    print("✗ No guarantee of completeness or correctness")


def demonstrate_new_way():
    """Show the new way with schemas (structured)."""
    print("\n=== NEW WAY (Structured Schema) ===")
    print("Benefits:")
    print("✓ Type safety with IDE autocomplete")
    print("✓ Consistent field names across all agents")
    print("✓ Required fields enforced at creation time")
    print("✓ Built-in validation")
    print("✓ Self-documenting code")
    
    # New structured schema
    output = LenderAgentOutput(
        borrower_id="borrower_123",  # Consistent naming
        credit_score=720,  # Clear what this is
        debt_to_income_ratio=0.35,
        default_risk_score=0.15,
        approved=True
    )
    
    print(f"\nNew output has {len(output.to_dict())} fields")
    print(f"✓ All required fields present")
    print(f"✓ Ready for MongoDB storage")
    print(f"✓ Can be validated programmatically")


def demonstrate_agent_integration():
    """Show how agents integrate schemas."""
    print("\n=== AGENT INTEGRATION EXAMPLE ===")
    
    # Create mock database
    mock_db = MagicMock()
    mock_db.get_loan.return_value = {
        'borrower_id': 'borrower_123',
        'principal': 10000.0
    }
    
    # Create agent with schema support
    agent = ExampleLenderAgentWithSchema("LenderExample", mock_db)
    
    print("\nProcessing loan with schema-based output...")
    result = agent.process("loan_123")
    
    print(f"✓ Output contains {len(result)} structured fields")
    print(f"✓ Borrower: {result['borrower_id']}")
    print(f"✓ Credit Score: {result['credit_score']}")
    print(f"✓ Approved: {result['approved']}")
    print(f"✓ Risk Score: {result['default_risk_score']}")
    print(f"✓ Data automatically validated before MongoDB storage")


def main():
    """Run all demonstrations."""
    print("=" * 70)
    print("AGENT SCHEMA INTEGRATION DEMONSTRATION")
    print("=" * 70)
    
    demonstrate_old_way()
    demonstrate_new_way()
    demonstrate_agent_integration()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
Benefits of using schemas:

1. TYPE SAFETY: Catch errors at development time
2. CONSISTENCY: All agents use same structure
3. VALIDATION: Required fields enforced automatically
4. DOCUMENTATION: Self-documenting with clear field names
5. EVOLUTION: Easy to add fields without breaking code
6. TESTING: Simple to create test fixtures
7. COORDINATION: Other agents know exactly what to expect

Recommended Usage:
------------------
1. Create output using schema class
2. Use agent.store_structured_output() to save
3. Schema is automatically validated and converted
4. Data is safely stored in MongoDB

See docs/AGENT_SCHEMAS.md for complete documentation.
    """)


if __name__ == '__main__':
    main()
