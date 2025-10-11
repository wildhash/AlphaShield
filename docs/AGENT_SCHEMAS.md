# Agent Output Schemas Documentation

## Overview

This document describes the standardized output schemas that each AlphaShield agent must use before uploading data to MongoDB. These schemas ensure data consistency, enable cross-agent coordination, and facilitate document-based processing.

## Design Principles

1. **Type Safety**: All schemas use Python dataclasses with type annotations
2. **Required vs Optional**: Clearly distinguish between required and optional fields
3. **Nested Structures**: Support complex nested data for detailed information
4. **MongoDB Ready**: All schemas provide `to_dict()` for MongoDB storage
5. **Validation**: Built-in validation through dataclass instantiation

## Agent Schemas

### 1. LenderAgent Output Schema

**Purpose**: Comprehensive underwriting and risk assessment for loan approval decisions.

**Documents Required**: Credit Report, Credit Card Statements (24 months), W-2 Form, Pay Stub, Bank Statements (optional)

**Key Fields**:
```python
@dataclass
class LenderAgentOutput:
    # Required
    borrower_id: str
    
    # Credit metrics (from Credit Report)
    credit_score: Optional[int]
    credit_history_length_years: Optional[float]
    total_credit_accounts: Optional[int]
    derogatory_marks: Optional[int]
    
    # Payment history (from Credit Card Statements)
    payment_history: Optional[Dict[str, Any]]  # {on_time, late, missed counts}
    credit_utilization: Optional[float]
    monthly_spending_patterns: Optional[Dict[str, float]]
    spending_volatility: Optional[float]
    
    # Income verification (from W-2 + Pay Stub)
    verified_income: Optional[Dict[str, float]]  # {annual_gross, monthly_gross, monthly_net}
    employment_length_years: Optional[float]
    employer_name: Optional[str]
    
    # Calculated metrics
    debt_to_income_ratio: Optional[float]
    spending_to_income_ratio: Optional[float]
    default_risk_score: Optional[float]  # 0.0 to 1.0
    approved_loan_amount_max: Optional[float]
    
    # Decision
    approved: bool = False
    approval_conditions: List[str] = field(default_factory=list)
```

**Example Usage**:
```python
from alphashield.schemas import LenderAgentOutput

output = LenderAgentOutput(
    borrower_id="borrower_123",
    credit_score=720,
    verified_income={'annual_gross': 60000, 'monthly_gross': 5000, 'monthly_net': 3800},
    debt_to_income_ratio=0.35,
    default_risk_score=0.15,
    approved=True
)

# Store in MongoDB
db.store_context('lender_assessment', output.to_dict())
```

---

### 2. AlphaTradingAgent Output Schema

**Purpose**: Investment performance tracking and tax-efficient portfolio management.

**Documents Required**: Brokerage Statement, Form 1040 (previous year for tax bracket)

**Key Fields**:
```python
@dataclass
class AlphaTradingAgentOutput:
    # Required
    loan_id: str
    
    # Portfolio positions (from Brokerage Statement)
    portfolio_positions: List[Dict[str, Any]]  # Each: {symbol, shares, cost_basis, current_price, ...}
    
    # Totals
    cash_balance: float = 0.0
    total_portfolio_value: float = 0.0
    
    # Allocation
    asset_allocation: Dict[str, float]  # {stocks_pct, bonds_pct, cash_pct}
    
    # Performance
    performance: Dict[str, Any]  # {ytd_return_pct, net_unrealized_gains, ...}
    
    # Tax considerations
    tax_bracket: Optional[str]
    
    # Loan coverage
    monthly_payment_due: Optional[float]
    months_of_coverage: Optional[float]  # cash / monthly_payment
    coverage_adequate: bool = False
```

**Example Usage**:
```python
from alphashield.schemas import AlphaTradingAgentOutput

output = AlphaTradingAgentOutput(
    loan_id="loan_456",
    portfolio_positions=[
        {
            'symbol': 'AAPL',
            'shares': 10,
            'current_price': 180.00,
            'unrealized_gain_loss': 300.00
        }
    ],
    cash_balance=1000.0,
    total_portfolio_value=2800.0,
    tax_bracket="22%",
    months_of_coverage=8.9,
    coverage_adequate=True
)

db.store_context('trading_performance', output.to_dict())
```

---

### 3. SpendingGuardAgent Output Schema

**Purpose**: Transaction-level analysis and anomaly detection for spending behavior.

**Documents Required**: Credit Card Statements (12 months), Bank Statements (optional)

**Key Fields**:
```python
@dataclass
class SpendingGuardAgentOutput:
    # Required
    borrower_id: str
    
    # Transaction summary
    total_transactions: int = 0
    analysis_period_months: int = 12
    
    # Spending by category
    category_spending: Dict[str, float]
    category_statistics: Dict[str, Dict[str, float]]  # {category: {mean, std_dev, threshold}}
    
    # High-risk spending
    high_risk_categories: Dict[str, float]  # {gambling, luxury, crypto}
    high_risk_ratio: float = 0.0
    
    # Anomalies
    anomalies_detected: List[Dict[str, Any]]
    anomaly_count: int = 0
    
    # Velocity analysis
    post_disbursement_spending: Optional[Dict[str, Any]]
    spending_acceleration_rate: Optional[float]
    rapid_depletion_risk: bool = False
    
    # Alerts
    alert_level: str = "normal"  # normal, elevated, high, critical
    spending_recommendations: List[str]
```

**Example Usage**:
```python
from alphashield.schemas import SpendingGuardAgentOutput

output = SpendingGuardAgentOutput(
    borrower_id="borrower_123",
    total_transactions=120,
    category_spending={'food': 500, 'entertainment': 300},
    anomaly_count=2,
    alert_level="elevated",
    spending_recommendations=["Review large entertainment purchases"]
)

db.store_context('spending_analysis', output.to_dict())
```

---

### 4. BudgetAnalyzerAgent Output Schema

**Purpose**: Income/expense analysis and affordability assessment using 50/30/20 rule.

**Documents Required**: Pay Stub, Credit Card Statements (12 months), Bank Statements, Credit Report

**Key Fields**:
```python
@dataclass
class BudgetAnalyzerAgentOutput:
    # Required
    borrower_id: str
    
    # Income
    monthly_gross_income: float = 0.0
    monthly_net_income: float = 0.0
    
    # Expenses
    monthly_expenses_by_category: Dict[str, float]
    average_monthly_spending: float = 0.0
    
    # 50/30/20 breakdown
    needs_spending: float = 0.0
    wants_spending: float = 0.0
    savings_rate: float = 0.0
    recommended_needs: float = 0.0
    recommended_wants: float = 0.0
    recommended_savings: float = 0.0
    
    # Ratios
    expense_ratio: float = 0.0  # total_expenses / net_income
    debt_service_ratio: float = 0.0  # debt_payments / gross_income
    
    # Health assessment
    budget_health_status: str = "unknown"  # healthy, concerning, critical
    budget_warnings: List[str]
    
    # Loan affordability
    proposed_monthly_payment: Optional[float]
    affordability_score: Optional[float]
    payment_affordable: bool = False
```

**Example Usage**:
```python
from alphashield.schemas import BudgetAnalyzerAgentOutput

output = BudgetAnalyzerAgentOutput(
    borrower_id="borrower_123",
    monthly_gross_income=5000.0,
    monthly_net_income=3800.0,
    needs_spending=2400.0,
    wants_spending=800.0,
    savings_rate=0.16,
    expense_ratio=0.84,
    budget_health_status="healthy",
    payment_affordable=True
)

db.store_context('budget_analysis', output.to_dict())
```

---

### 5. TaxOptimizerAgent Output Schema

**Purpose**: Comprehensive tax analysis and optimization strategy generation.

**Documents Required**: Form 1040, W-2, Pay Stub, Brokerage Statement, Credit Card Statements

**Key Fields**:
```python
@dataclass
class TaxOptimizerAgentOutput:
    # Required
    borrower_id: str
    
    # Prior year (from Form 1040)
    prior_year_agi: Optional[float]
    prior_year_effective_rate: Optional[float]
    marginal_tax_bracket: Optional[str]
    
    # Current year projections
    projected_w2_wages: Optional[float]
    retirement_contribution_ytd: Optional[float]
    hsa_contribution_ytd: Optional[float]
    
    # Investment income
    investment_income: Optional[Dict[str, float]]
    tax_loss_harvesting_opportunities: List[Dict[str, Any]]
    
    # Deductible expenses
    charitable_contributions: Optional[float]
    medical_expenses: Optional[float]
    
    # Optimization opportunities
    retirement_contribution_room: Optional[float]
    hsa_contribution_room: Optional[float]
    estimated_tax_savings: float = 0.0
    
    # Strategies
    short_term_strategies: List[Dict[str, Any]]
    long_term_strategies: List[Dict[str, Any]]
    total_potential_savings: float = 0.0
```

**Example Usage**:
```python
from alphashield.schemas import TaxOptimizerAgentOutput

output = TaxOptimizerAgentOutput(
    borrower_id="borrower_123",
    marginal_tax_bracket="22%",
    projected_w2_wages=60000.0,
    retirement_contribution_room=17500.0,
    short_term_strategies=[
        {'strategy': 'tax_loss_harvesting', 'potential_savings': 440.00}
    ],
    total_potential_savings=5390.00
)

db.store_context('tax_analysis', output.to_dict())
```

---

### 6. ContractReviewAgent Output Schema

**Purpose**: Contract fairness assessment, compliance checking, and final approval gating.

**Documents Required**: Loan Agreement, Credit Report, Pay Stub, Other agent outputs

**Key Fields**:
```python
@dataclass
class ContractReviewAgentOutput:
    # Required
    loan_id: str
    
    # Contract terms
    principal_amount: float = 0.0
    stated_interest_rate: float = 0.0
    annual_percentage_rate: float = 0.0
    loan_term_months: int = 0
    monthly_payment: float = 0.0
    
    # Fees
    fees: Dict[str, float]
    total_fees: float = 0.0
    
    # Borrower context
    borrower_credit_score: Optional[int]
    borrower_monthly_income: Optional[float]
    
    # Affordability
    payment_to_income_ratio: Optional[float]
    affordability_rating: str = "unknown"
    
    # Market comparison
    market_average_apr: Optional[float]
    competitive_position: str = "unknown"  # excellent, competitive, expensive, predatory
    
    # Risk assessment
    predatory_indicators: List[str]
    concerning_terms: List[str]
    positive_terms: List[str]
    
    # Compliance
    truth_in_lending_compliant: bool = False
    state_usury_laws_compliant: bool = False
    compliance_issues: List[str]
    
    # Decision
    approved: bool = False
    risk_score: float = 0.5
    overall_rating: str = "unknown"
```

**Example Usage**:
```python
from alphashield.schemas import ContractReviewAgentOutput

output = ContractReviewAgentOutput(
    loan_id="loan_123",
    principal_amount=10000.0,
    stated_interest_rate=8.0,
    annual_percentage_rate=8.5,
    fees={'origination': 100.0},
    competitive_position="excellent",
    positive_terms=["Low interest rate", "No prepayment penalty"],
    truth_in_lending_compliant=True,
    approved=True,
    overall_rating="excellent"
)

db.store_context('contract_review', output.to_dict())
```

---

## Usage Guidelines

### 1. Creating Schema Instances

```python
from alphashield.schemas import LenderAgentOutput

# Minimal instance
output = LenderAgentOutput(borrower_id="borrower_123")

# Complete instance
output = LenderAgentOutput(
    borrower_id="borrower_123",
    credit_score=720,
    debt_to_income_ratio=0.35,
    approved=True
)
```

### 2. Converting to Dictionary for MongoDB

```python
# Convert to dict
data = output.to_dict()

# Store in MongoDB
db.store_context('lender_assessment', data)
```

### 3. Validation

```python
from alphashield.schemas.agent_schemas import validate_schema

# Validate data before creating schema
data = {'borrower_id': 'borrower_123', 'credit_score': 720}
validate_schema(data, LenderAgentOutput)  # Returns True or raises ValueError
```

### 4. Using Helper Functions

```python
from alphashield.schemas.validation import (
    prepare_lender_output,
    validate_and_prepare_for_mongo
)

# Prepare output
output = prepare_lender_output(
    borrower_id="borrower_123",
    credit_score=720,
    approved=True
)

# Validate and prepare for MongoDB
mongo_data = validate_and_prepare_for_mongo(output)
db.store_context('lender_assessment', mongo_data)
```

## Benefits

1. **Type Safety**: Catch errors at development time, not runtime
2. **Documentation**: Self-documenting code with clear field names and types
3. **Consistency**: All agents use the same structure for similar data
4. **Validation**: Automatic validation of required fields
5. **Evolution**: Easy to add new fields without breaking existing code
6. **Testing**: Simple to create test fixtures with known schemas
7. **Cross-Agent Coordination**: Other agents know exactly what data to expect

## Testing

Each schema has comprehensive unit tests in `tests/test_agent_schemas.py`:

```bash
# Run schema tests
python3 -m unittest tests.test_agent_schemas -v
```

## Future Enhancements

1. **Pydantic Integration**: Consider migrating to Pydantic for enhanced validation
2. **JSON Schema Export**: Generate JSON schemas for API documentation
3. **Schema Versioning**: Add version fields to support schema evolution
4. **Embedding Support**: Integrate with Voyage AI embedding generation
5. **MongoDB Indexes**: Auto-generate index recommendations from schemas
