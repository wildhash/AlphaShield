# Document Processing Flow and Schema Usage

## Overview

This document describes how documents are processed by agents and how output schemas ensure data consistency before MongoDB storage.

## Document Processing Pipeline

```
┌─────────────────────────────────────────────────────┐
│         Document Ingestion Layer                    │
│  (Borrower uploads required documents)              │
└──────────────────┬──────────────────────────────────┘
                   │
     ┌─────────────┴─────────────┐
     │   Document Classifier      │
     │   (Routes docs to agents)  │
     └─────────────┬──────────────┘
                   │
    ┌──────────────┼──────────────┬────────────┐
    │              │              │            │
┌───▼────┐   ┌────▼─────┐   ┌────▼────┐  ┌───▼──────┐
│Credit  │   │Credit    │   │W-2 +    │  │Brokerage │
│Report  │   │Card Stmt │   │Pay Stub │  │Statement │
└───┬────┘   └────┬─────┘   └────┬────┘  └──┬───────┘
    │             │              │           │
    ├─────────────┼──────────────┼───────────┤
    │             │              │           │
┌───▼────────┐ ┌─▼────────┐ ┌───▼─────┐ ┌──▼────────┐
│Lender      │ │Spending  │ │Budget   │ │Alpha      │
│Agent       │ │Guard     │ │Analyzer │ │Trading    │
│            │ │          │ │         │ │           │
│Schema:     │ │Schema:   │ │Schema:  │ │Schema:    │
│Lender      │ │Spending  │ │Budget   │ │Trading    │
│Output      │ │Guard     │ │Analyzer │ │Output     │
└───┬────────┘ └────┬─────┘ └────┬────┘ └──┬────────┘
    │               │             │          │
    │               └─────────────┴──────────┘
    │                             │
    │                    ┌────────▼────────┐
    │                    │Tax Optimizer    │
    │                    │                 │
    │                    │Schema:          │
    │                    │TaxOptimizer     │
    │                    │Output           │
    │                    └────────┬────────┘
    │                             │
    └─────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │Contract Review     │
         │(Final Gatekeeper)  │
         │                    │
         │Schema:             │
         │ContractReview      │
         │Output              │
         └─────────┬──────────┘
                   │
            ┌──────▼──────┐
            │MongoDB      │
            │Storage      │
            │             │
            │✓ Validated  │
            │✓ Structured │
            │✓ Consistent │
            └─────────────┘
```

## Agent-Schema-Document Mapping

### 1. Lender Agent → LenderAgentOutput

**Input Documents**:
- ✅ Credit Report (primary)
- ✅ Credit Card Statements (24 months)
- ✅ W-2 Form
- ✅ Recent Pay Stub
- ✅ Bank Statements (optional)

**Processing**:
```
Credit Report          → credit_score, credit_history_length_years,
                         total_credit_accounts, derogatory_marks

Credit Card Statements → payment_history, credit_utilization,
                         monthly_spending_patterns

W-2 + Pay Stub        → verified_income, employment_length_years,
                         employer_name

Calculations          → debt_to_income_ratio, spending_to_income_ratio,
                         default_risk_score
```

**Output Schema**: `LenderAgentOutput`
- 22 fields total
- Required: `borrower_id`
- Key metrics: credit scores, income, DTI, risk scores
- Decision: `approved`, `approval_conditions`

---

### 2. Alpha Trading Agent → AlphaTradingAgentOutput

**Input Documents**:
- ✅ Brokerage Statement (primary)
- ✅ Form 1040 (previous year - tax bracket)

**Processing**:
```
Brokerage Statement   → portfolio_positions, cash_balance,
                         total_portfolio_value, asset_allocation

Form 1040            → tax_bracket

Calculations         → months_of_coverage, coverage_adequate,
                         performance metrics
```

**Output Schema**: `AlphaTradingAgentOutput`
- 16 fields total
- Required: `loan_id`
- Key metrics: portfolio value, asset allocation, tax status
- Risk: coverage months, risk level

---

### 3. Spending Guard Agent → SpendingGuardAgentOutput

**Input Documents**:
- ✅ Credit Card Statements (12 months, primary)
- ✅ Bank Statements (optional)

**Processing**:
```
Credit Card Statements → all_transactions, category_spending,
                          category_statistics

Statistical Analysis   → anomaly detection, threshold calculations,
                          high_risk_categories

Velocity Analysis     → post_disbursement_spending,
                         rapid_depletion_risk
```

**Output Schema**: `SpendingGuardAgentOutput`
- 19 fields total
- Required: `borrower_id`
- Key metrics: anomaly count, alert level, high-risk ratio
- Recommendations: spending guidance

---

### 4. Budget Analyzer Agent → BudgetAnalyzerAgentOutput

**Input Documents**:
- ✅ Pay Stub (recent, primary)
- ✅ Credit Card Statements (12 months)
- ✅ Bank Statements (optional)
- ✅ Credit Report (existing debt)

**Processing**:
```
Pay Stub              → monthly_gross_income, monthly_net_income

Credit Card Statements → monthly_expenses_by_category,
                          average_monthly_spending

Credit Report         → existing_debt_payments

50/30/20 Analysis     → needs_spending, wants_spending, savings_rate,
                         recommended allocations

Calculations          → expense_ratio, debt_service_ratio,
                         affordability_score
```

**Output Schema**: `BudgetAnalyzerAgentOutput`
- 27 fields total
- Required: `borrower_id`
- Key metrics: income, expenses, 50/30/20 breakdown, ratios
- Health: budget status, warnings, affordability

---

### 5. Tax Optimizer Agent → TaxOptimizerAgentOutput

**Input Documents**:
- ✅ Form 1040 (previous year, primary)
- ✅ W-2 Form (current year)
- ✅ Pay Stub (recent)
- ✅ Brokerage Statement
- ✅ Credit Card Statements (deductions)

**Processing**:
```
Form 1040             → prior_year_agi, taxable_income, tax_paid,
                         effective_rate, marginal_bracket

W-2 + Pay Stub        → projected_w2_wages, withholding_ytd,
                         retirement_contribution_ytd

Brokerage Statement   → investment_income, unrealized gains/losses,
                         tax_loss_harvesting_opportunities

Credit Card Statements → charitable_contributions, medical_expenses

Calculations          → retirement_contribution_room,
                         estimated_tax_savings, optimization strategies
```

**Output Schema**: `TaxOptimizerAgentOutput`
- 29 fields total
- Required: `borrower_id`
- Key metrics: tax brackets, contribution room, savings potential
- Strategies: short-term and long-term optimization plans

---

### 6. Contract Review Agent → ContractReviewAgentOutput

**Input Documents**:
- ✅ Loan Agreement (primary)
- ✅ Credit Report (borrower credit score)
- ✅ Pay Stub (income verification)
- ⚠️ Outputs from other agents

**Processing**:
```
Loan Agreement        → principal, interest_rate, APR, term, fees,
                         loan_features

Credit Report         → borrower_credit_score

Pay Stub             → borrower_monthly_income

Other Agent Outputs  → risk assessments, affordability

Calculations         → payment_to_income_ratio,
                         total_debt_to_income_ratio

Market Comparison    → market_average_apr, competitive_position

Compliance Checks    → TILA compliance, usury laws, disclosures

Risk Assessment      → predatory indicators, concerning terms
```

**Output Schema**: `ContractReviewAgentOutput`
- 36 fields total
- Required: `loan_id`
- Key metrics: contract terms, affordability ratios, compliance
- Decision: `approved`, risk score, overall rating

---

## Schema Benefits in Practice

### Before Schemas (Unstructured)
```python
# Different agents use different field names
lender_result = {'score': 720, 'borrower': 'user123'}
trading_result = {'credit_score': 720, 'borrower_id': 'user123'}
spending_result = {'score': 720, 'user_id': 'user123'}

# Missing fields, inconsistent types
# No validation, hard to coordinate
```

### After Schemas (Structured)
```python
from alphashield.schemas import LenderAgentOutput, AlphaTradingAgentOutput

# All agents use consistent field names
lender_output = LenderAgentOutput(
    borrower_id='user123',
    credit_score=720
)

trading_output = AlphaTradingAgentOutput(
    loan_id='loan456',
    borrower_id='user123'  # Same field name!
)

# ✓ Type safe
# ✓ Validated
# ✓ Consistent
# ✓ Complete
```

## Document Overlap Strategy

Multiple agents need the same documents. To avoid redundant processing:

### Credit Card Statements
Used by:
- **Lender Agent**: Payment history, utilization
- **Spending Guard**: Transaction anomalies
- **Budget Analyzer**: Monthly expense totals
- **Tax Optimizer**: Deductible expenses

**Solution**: 
1. Parse transactions once
2. Store in MongoDB with embeddings
3. All agents query the same structured data
4. Each agent creates its own schema output

### Example Flow
```
Credit Card Statement → Parse once → MongoDB (raw transactions)
                                         ↓
                         ┌───────────────┼───────────────┐
                         ↓               ↓               ↓
                   Lender Schema   Spending Schema  Budget Schema
                         ↓               ↓               ↓
                   MongoDB (lender) MongoDB (spending) MongoDB (budget)
```

## Validation Flow

```
Agent Process
     ↓
Create Schema Instance
     ↓
Automatic Validation
  (dataclass __init__)
     ↓
Convert to Dict
  (schema.to_dict())
     ↓
Optional: validate_and_prepare_for_mongo()
     ↓
Store in MongoDB
  (agent.store_structured_output())
     ↓
✓ Data is validated
✓ Data is consistent
✓ Data is complete
```

## MongoDB Collections Structure

```javascript
// agent_contexts collection
{
  _id: ObjectId,
  agent_name: "Lender",
  context_type: "lender_assessment",
  data: {
    // LenderAgentOutput fields
    borrower_id: String,
    credit_score: Number,
    approved: Boolean,
    // ... all 22 fields
    timestamp: Date
  },
  embedding: [Float],  // Voyage AI vector
  timestamp: Date
}

// All agent outputs follow same pattern
// Different agents, different schemas, same structure
```

## Integration with Existing Code

The schemas are designed to integrate seamlessly with existing agents:

1. **Backwards Compatible**: Schemas have `to_dict()` so existing code that expects dicts still works
2. **Opt-in**: Agents can gradually adopt schemas
3. **BaseAgent Support**: `store_structured_output()` method added for easy integration
4. **No Breaking Changes**: All existing tests still pass

## Next Steps

1. ✅ Schemas defined for all 6 agents
2. ✅ Validation and helper utilities created
3. ✅ Documentation and examples provided
4. ✅ BaseAgent integration completed
5. ⏭️ Agents can gradually adopt schemas in their `process()` methods
6. ⏭️ Document parsing utilities can populate schema fields
7. ⏭️ MongoDB queries can leverage consistent schema structure

## Summary

Output schemas ensure that **before** any data reaches MongoDB:
- ✅ All required fields are present
- ✅ Field names are consistent across agents
- ✅ Data types are correct
- ✅ Relationships between agents are clear
- ✅ Validation catches errors early
- ✅ Cross-agent coordination is simplified

This forms the foundation for reliable, scalable document processing and multi-agent coordination in AlphaShield.
