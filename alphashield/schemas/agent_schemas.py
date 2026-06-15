"""Output schema definitions for AlphaShield agents.

These schemas ensure consistent data structures before uploading to MongoDB.
Based on the Agent Document Requirements & Processing Strategy specification.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LenderAgentOutput:
    """Output schema for Lender Agent.

    Documents Required: Credit Report, Credit Card Statements, W-2, Pay Stub, Bank Statements

    Purpose: Comprehensive underwriting and risk assessment for loan approval decisions.
    """

    # Borrower identification
    borrower_id: str
    loan_id: str | None = None

    # Credit metrics (from Credit Report)
    credit_score: int | None = None
    credit_history_length_years: float | None = None
    total_credit_accounts: int | None = None
    derogatory_marks: int | None = None

    # Payment history (from Credit Card Statements - 24 months)
    payment_history: dict[str, Any] | None = None  # {on_time_count, late_count, missed_count}
    credit_utilization: float | None = None  # percentage
    monthly_spending_patterns: dict[str, float] | None = None
    spending_volatility: float | None = None  # std deviation

    # Income verification (from W-2 + Pay Stub)
    verified_income: dict[str, float] | None = None  # {annual_gross, monthly_gross, monthly_net}
    employment_length_years: float | None = None
    employer_name: str | None = None

    # Existing obligations (from Credit Report)
    existing_obligations: dict[str, float] | None = None  # {student_loans, auto_loans, etc}

    # Calculated metrics
    debt_to_income_ratio: float | None = None
    spending_to_income_ratio: float | None = None
    default_risk_score: float | None = None  # 0.0 to 1.0
    approved_loan_amount_max: float | None = None

    # Loan approval decision
    approved: bool = False
    approval_conditions: list[str] = field(default_factory=list)
    denial_reasons: list[str] = field(default_factory=list)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return asdict(self)


@dataclass
class AlphaTradingAgentOutput:
    """Output schema for Alpha Trading Agent.

    Documents Required: Brokerage Statement, Form 1040 (previous year for tax bracket)

    Purpose: Investment performance tracking and tax-efficient portfolio management.
    """

    # Loan and portfolio identification
    loan_id: str
    borrower_id: str | None = None

    # Portfolio positions (from Brokerage Statement)
    portfolio_positions: list[dict[str, Any]] = field(default_factory=list)
    # Each position: {symbol, shares, cost_basis, current_price, market_value,
    #                 unrealized_gain_loss, holding_period, tax_status}

    # Portfolio totals
    cash_balance: float = 0.0
    total_portfolio_value: float = 0.0

    # Asset allocation
    asset_allocation: dict[str, float] = field(
        default_factory=dict
    )  # {stocks_pct, bonds_pct, cash_pct}

    # Performance metrics
    performance: dict[str, Any] = field(default_factory=dict)
    # {ytd_return_pct, net_unrealized_gains, short_term_gains, long_term_gains}

    # Tax considerations (from Form 1040)
    tax_bracket: str | None = None  # e.g., "22%", "24%"
    tax_optimization_score: float | None = None

    # Loan coverage metrics (if loan exists)
    monthly_payment_due: float | None = None
    months_of_coverage: float | None = None  # cash_balance / monthly_payment
    coverage_adequate: bool = False

    # Risk assessment
    risk_level: str = "medium"  # low, medium, high
    risk_factors: list[str] = field(default_factory=list)

    # Recommendations
    rebalancing_recommendations: list[str] = field(default_factory=list)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return asdict(self)


@dataclass
class SpendingGuardAgentOutput:
    """Output schema for Spending Guard Agent.

    Documents Required: Credit Card Statements (12 months), Bank Statements (optional)

    Purpose: Transaction-level analysis and anomaly detection for spending behavior.
    """

    # Borrower and loan identification
    borrower_id: str
    loan_id: str | None = None

    # Transaction summary
    total_transactions: int = 0
    analysis_period_months: int = 12

    # Spending categories (from Credit Card Statements)
    category_spending: dict[str, float] = field(default_factory=dict)
    # Each category: amount spent

    # Statistical analysis per category
    category_statistics: dict[str, dict[str, float]] = field(default_factory=dict)
    # {category: {mean, std_dev, max, min, anomaly_threshold}}

    # High-risk spending
    high_risk_categories: dict[str, float] = field(default_factory=dict)
    # {gambling, luxury, crypto}: amounts
    high_risk_ratio: float = 0.0  # high_risk_spending / total_spending

    # Anomaly detection
    anomalies_detected: list[dict[str, Any]] = field(default_factory=list)
    # Each anomaly: {date, amount, merchant, category, threshold_exceeded_by}
    anomaly_count: int = 0

    # Velocity analysis
    post_disbursement_spending: dict[str, Any] | None = None
    # {days_since_disbursement, amount_spent, percentage_of_loan}
    spending_acceleration_rate: float | None = None
    rapid_depletion_risk: bool = False

    # Alert levels
    alert_level: str = "normal"  # normal, elevated, high, critical
    alert_reasons: list[str] = field(default_factory=list)

    # Spending recommendations
    spending_recommendations: list[str] = field(default_factory=list)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return asdict(self)


@dataclass
class BudgetAnalyzerAgentOutput:
    """Output schema for Budget Analyzer Agent.

    Documents Required: Pay Stub, Credit Card Statements (12 months), Bank Statements, Credit Report

    Purpose: Income/expense analysis and affordability assessment using 50/30/20 rule.
    """

    # Borrower and loan identification
    borrower_id: str
    loan_id: str | None = None

    # Income (from Pay Stub)
    monthly_gross_income: float = 0.0
    monthly_net_income: float = 0.0  # take-home pay
    annual_gross_income: float | None = None

    # Expenses (from Credit Card Statements + Bank Statements)
    monthly_expenses_by_category: dict[str, float] = field(default_factory=dict)
    average_monthly_spending: float = 0.0

    # Existing debt obligations (from Credit Report)
    existing_debt_payments: dict[str, float] = field(default_factory=dict)
    # {student_loan, auto_loan, credit_cards, etc}
    total_debt_payments: float = 0.0

    # 50/30/20 rule breakdown
    needs_spending: float = 0.0  # housing, utilities, food, debt, insurance
    wants_spending: float = 0.0  # dining, entertainment, shopping
    savings_rate: float = 0.0  # actual savings as percentage of income

    # Recommended 50/30/20
    recommended_needs: float = 0.0  # 50% of gross income
    recommended_wants: float = 0.0  # 30% of gross income
    recommended_savings: float = 0.0  # 20% of gross income

    # Budget health ratios
    expense_ratio: float = 0.0  # total_expenses / net_income
    debt_service_ratio: float = 0.0  # debt_payments / gross_income

    # Budget health assessment
    budget_health_status: str = "unknown"  # healthy, concerning, critical
    budget_warnings: list[str] = field(default_factory=list)

    # Loan affordability (if loan proposed)
    proposed_monthly_payment: float | None = None
    new_expense_ratio: float | None = None  # with loan payment included
    affordability_score: float | None = None  # 0.0 to 1.0
    payment_affordable: bool = False

    # Budget recommendations
    optimization_recommendations: list[str] = field(default_factory=list)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return asdict(self)


@dataclass
class TaxOptimizerAgentOutput:
    """Output schema for Tax Optimizer Agent.

    Documents Required: Form 1040, W-2, Pay Stub, Brokerage Statement, Credit Card Statements

    Purpose: Comprehensive tax analysis and optimization strategy generation.
    """

    # Borrower and loan identification
    borrower_id: str
    loan_id: str | None = None

    # Prior year tax data (from Form 1040)
    prior_year_agi: float | None = None  # Adjusted Gross Income
    prior_year_taxable_income: float | None = None
    prior_year_total_tax: float | None = None
    prior_year_effective_rate: float | None = None
    marginal_tax_bracket: str | None = None  # e.g., "24%"

    # Current year projections (from W-2 + Pay Stub)
    projected_w2_wages: float | None = None
    federal_withholding_ytd: float | None = None
    state_withholding_ytd: float | None = None
    retirement_contribution_ytd: float | None = None  # 401k
    hsa_contribution_ytd: float | None = None

    # Investment income (from Brokerage Statement)
    investment_income: dict[str, float] | None = None  # {dividends, interest, capital_gains}
    unrealized_gains: float | None = None
    unrealized_losses: float | None = None
    tax_loss_harvesting_opportunities: list[dict[str, Any]] = field(default_factory=list)

    # Deductible expenses (from Credit Card Statements)
    charitable_contributions: float | None = None
    medical_expenses: float | None = None
    state_local_taxes: float | None = None

    # Optimization opportunities
    retirement_contribution_room: float | None = None  # remaining 401k space
    hsa_contribution_room: float | None = None  # remaining HSA space
    itemized_vs_standard: str = "unknown"  # which is better
    estimated_tax_savings: float = 0.0

    # Tax optimization strategies
    short_term_strategies: list[dict[str, Any]] = field(default_factory=list)
    # Each: {strategy, description, potential_savings, timeline}
    long_term_strategies: list[dict[str, Any]] = field(default_factory=list)
    # Each: {strategy, description, potential_savings, timeline}

    # Total optimization potential
    total_potential_savings: float = 0.0

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return asdict(self)


@dataclass
class ContractReviewAgentOutput:
    """Output schema for Contract Review Agent.

    Documents Required: Loan Agreement, Credit Report (borrower credit score), Pay Stub,
                        Outputs from other agents

    Purpose: Contract fairness assessment, compliance checking, and final approval gating.
    """

    # Loan and contract identification
    loan_id: str
    borrower_id: str | None = None
    contract_id: str | None = None

    # Contract terms (from Loan Agreement)
    principal_amount: float = 0.0
    stated_interest_rate: float = 0.0
    annual_percentage_rate: float = 0.0  # APR including fees
    loan_term_months: int = 0
    monthly_payment: float = 0.0

    # Fees breakdown
    fees: dict[str, float] = field(default_factory=dict)
    # {origination, application, late_payment, prepayment, etc}
    total_fees: float = 0.0

    # Loan features
    loan_features: dict[str, Any] = field(default_factory=dict)
    # {fixed_rate, variable_rate, prepayment_allowed, balloon_payment, etc}

    # Borrower context (from Credit Report + Pay Stub)
    borrower_credit_score: int | None = None
    borrower_monthly_income: float | None = None

    # Affordability ratios
    payment_to_income_ratio: float | None = None
    total_debt_to_income_ratio: float | None = None
    affordability_rating: str = "unknown"  # excellent, good, fair, poor

    # Market comparison
    market_average_apr: float | None = None  # for borrower's credit score
    loan_percentile_ranking: str | None = None  # e.g., "top 25%"
    competitive_position: str = "unknown"  # excellent, competitive, expensive, predatory

    # Risk assessment
    predatory_indicators: list[str] = field(default_factory=list)
    # e.g., "excessive fees", "balloon payment", "prepayment penalty"
    concerning_terms: list[str] = field(default_factory=list)
    positive_terms: list[str] = field(default_factory=list)

    # Compliance checks
    truth_in_lending_compliant: bool = False
    state_usury_laws_compliant: bool = False
    mandatory_disclosures_present: bool = False
    compliance_issues: list[str] = field(default_factory=list)

    # Final recommendation
    approved: bool = False
    approval_conditions: list[str] = field(default_factory=list)
    risk_score: float = 0.5  # 0.0 to 1.0
    overall_rating: str = "unknown"  # excellent, good, fair, poor

    # Recommendations
    recommendations: list[str] = field(default_factory=list)

    # Agent coordination (inputs from other agents)
    lender_agent_input: dict[str, Any] | None = None
    budget_analyzer_input: dict[str, Any] | None = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return asdict(self)


def validate_schema(data: dict[str, Any], schema_class) -> bool:
    """Validate that data conforms to schema.

    Args:
        data: Dictionary to validate
        schema_class: Schema class to validate against

    Returns:
        True if valid, raises ValueError otherwise
    """
    try:
        # Try to instantiate the schema with the data
        schema_class(**data)
        return True
    except TypeError as e:
        raise ValueError(f"Schema validation failed: {str(e)}") from e
