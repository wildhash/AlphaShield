"""Output schema definitions for AlphaShield agents.

These schemas ensure consistent data structures before uploading to MongoDB.
Based on the Agent Document Requirements & Processing Strategy specification.
"""
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class LenderAgentOutput:
    """Output schema for Lender Agent.
    
    Documents Required: Credit Report, Credit Card Statements, W-2, Pay Stub, Bank Statements
    
    Purpose: Comprehensive underwriting and risk assessment for loan approval decisions.
    """
    # Borrower identification
    borrower_id: str
    loan_id: Optional[str] = None
    
    # Credit metrics (from Credit Report)
    credit_score: Optional[int] = None
    credit_history_length_years: Optional[float] = None
    total_credit_accounts: Optional[int] = None
    derogatory_marks: Optional[int] = None
    
    # Payment history (from Credit Card Statements - 24 months)
    payment_history: Optional[Dict[str, Any]] = None  # {on_time_count, late_count, missed_count}
    credit_utilization: Optional[float] = None  # percentage
    monthly_spending_patterns: Optional[Dict[str, float]] = None
    spending_volatility: Optional[float] = None  # std deviation
    
    # Income verification (from W-2 + Pay Stub)
    verified_income: Optional[Dict[str, float]] = None  # {annual_gross, monthly_gross, monthly_net}
    employment_length_years: Optional[float] = None
    employer_name: Optional[str] = None
    
    # Existing obligations (from Credit Report)
    existing_obligations: Optional[Dict[str, float]] = None  # {student_loans, auto_loans, etc}
    
    # Calculated metrics
    debt_to_income_ratio: Optional[float] = None
    spending_to_income_ratio: Optional[float] = None
    default_risk_score: Optional[float] = None  # 0.0 to 1.0
    approved_loan_amount_max: Optional[float] = None
    
    # Loan approval decision
    approved: bool = False
    approval_conditions: List[str] = field(default_factory=list)
    denial_reasons: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
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
    borrower_id: Optional[str] = None
    
    # Portfolio positions (from Brokerage Statement)
    portfolio_positions: List[Dict[str, Any]] = field(default_factory=list)
    # Each position: {symbol, shares, cost_basis, current_price, market_value, 
    #                 unrealized_gain_loss, holding_period, tax_status}
    
    # Portfolio totals
    cash_balance: float = 0.0
    total_portfolio_value: float = 0.0
    
    # Asset allocation
    asset_allocation: Dict[str, float] = field(default_factory=dict)  # {stocks_pct, bonds_pct, cash_pct}
    
    # Performance metrics
    performance: Dict[str, Any] = field(default_factory=dict)
    # {ytd_return_pct, net_unrealized_gains, short_term_gains, long_term_gains}
    
    # Tax considerations (from Form 1040)
    tax_bracket: Optional[str] = None  # e.g., "22%", "24%"
    tax_optimization_score: Optional[float] = None
    
    # Loan coverage metrics (if loan exists)
    monthly_payment_due: Optional[float] = None
    months_of_coverage: Optional[float] = None  # cash_balance / monthly_payment
    coverage_adequate: bool = False
    
    # Risk assessment
    risk_level: str = "medium"  # low, medium, high
    risk_factors: List[str] = field(default_factory=list)
    
    # Recommendations
    rebalancing_recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
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
    loan_id: Optional[str] = None
    
    # Transaction summary
    total_transactions: int = 0
    analysis_period_months: int = 12
    
    # Spending categories (from Credit Card Statements)
    category_spending: Dict[str, float] = field(default_factory=dict)
    # Each category: amount spent
    
    # Statistical analysis per category
    category_statistics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # {category: {mean, std_dev, max, min, anomaly_threshold}}
    
    # High-risk spending
    high_risk_categories: Dict[str, float] = field(default_factory=dict)
    # {gambling, luxury, crypto}: amounts
    high_risk_ratio: float = 0.0  # high_risk_spending / total_spending
    
    # Anomaly detection
    anomalies_detected: List[Dict[str, Any]] = field(default_factory=list)
    # Each anomaly: {date, amount, merchant, category, threshold_exceeded_by}
    anomaly_count: int = 0
    
    # Velocity analysis
    post_disbursement_spending: Optional[Dict[str, Any]] = None
    # {days_since_disbursement, amount_spent, percentage_of_loan}
    spending_acceleration_rate: Optional[float] = None
    rapid_depletion_risk: bool = False
    
    # Alert levels
    alert_level: str = "normal"  # normal, elevated, high, critical
    alert_reasons: List[str] = field(default_factory=list)
    
    # Spending recommendations
    spending_recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
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
    loan_id: Optional[str] = None
    
    # Income (from Pay Stub)
    monthly_gross_income: float = 0.0
    monthly_net_income: float = 0.0  # take-home pay
    annual_gross_income: Optional[float] = None
    
    # Expenses (from Credit Card Statements + Bank Statements)
    monthly_expenses_by_category: Dict[str, float] = field(default_factory=dict)
    average_monthly_spending: float = 0.0
    
    # Existing debt obligations (from Credit Report)
    existing_debt_payments: Dict[str, float] = field(default_factory=dict)
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
    budget_warnings: List[str] = field(default_factory=list)
    
    # Loan affordability (if loan proposed)
    proposed_monthly_payment: Optional[float] = None
    new_expense_ratio: Optional[float] = None  # with loan payment included
    affordability_score: Optional[float] = None  # 0.0 to 1.0
    payment_affordable: bool = False
    
    # Budget recommendations
    optimization_recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
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
    loan_id: Optional[str] = None
    
    # Prior year tax data (from Form 1040)
    prior_year_agi: Optional[float] = None  # Adjusted Gross Income
    prior_year_taxable_income: Optional[float] = None
    prior_year_total_tax: Optional[float] = None
    prior_year_effective_rate: Optional[float] = None
    marginal_tax_bracket: Optional[str] = None  # e.g., "24%"
    
    # Current year projections (from W-2 + Pay Stub)
    projected_w2_wages: Optional[float] = None
    federal_withholding_ytd: Optional[float] = None
    state_withholding_ytd: Optional[float] = None
    retirement_contribution_ytd: Optional[float] = None  # 401k
    hsa_contribution_ytd: Optional[float] = None
    
    # Investment income (from Brokerage Statement)
    investment_income: Optional[Dict[str, float]] = None  # {dividends, interest, capital_gains}
    unrealized_gains: Optional[float] = None
    unrealized_losses: Optional[float] = None
    tax_loss_harvesting_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Deductible expenses (from Credit Card Statements)
    charitable_contributions: Optional[float] = None
    medical_expenses: Optional[float] = None
    state_local_taxes: Optional[float] = None
    
    # Optimization opportunities
    retirement_contribution_room: Optional[float] = None  # remaining 401k space
    hsa_contribution_room: Optional[float] = None  # remaining HSA space
    itemized_vs_standard: str = "unknown"  # which is better
    estimated_tax_savings: float = 0.0
    
    # Tax optimization strategies
    short_term_strategies: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {strategy, description, potential_savings, timeline}
    long_term_strategies: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {strategy, description, potential_savings, timeline}
    
    # Total optimization potential
    total_potential_savings: float = 0.0
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
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
    borrower_id: Optional[str] = None
    contract_id: Optional[str] = None
    
    # Contract terms (from Loan Agreement)
    principal_amount: float = 0.0
    stated_interest_rate: float = 0.0
    annual_percentage_rate: float = 0.0  # APR including fees
    loan_term_months: int = 0
    monthly_payment: float = 0.0
    
    # Fees breakdown
    fees: Dict[str, float] = field(default_factory=dict)
    # {origination, application, late_payment, prepayment, etc}
    total_fees: float = 0.0
    
    # Loan features
    loan_features: Dict[str, Any] = field(default_factory=dict)
    # {fixed_rate, variable_rate, prepayment_allowed, balloon_payment, etc}
    
    # Borrower context (from Credit Report + Pay Stub)
    borrower_credit_score: Optional[int] = None
    borrower_monthly_income: Optional[float] = None
    
    # Affordability ratios
    payment_to_income_ratio: Optional[float] = None
    total_debt_to_income_ratio: Optional[float] = None
    affordability_rating: str = "unknown"  # excellent, good, fair, poor
    
    # Market comparison
    market_average_apr: Optional[float] = None  # for borrower's credit score
    loan_percentile_ranking: Optional[str] = None  # e.g., "top 25%"
    competitive_position: str = "unknown"  # excellent, competitive, expensive, predatory
    
    # Risk assessment
    predatory_indicators: List[str] = field(default_factory=list)
    # e.g., "excessive fees", "balloon payment", "prepayment penalty"
    concerning_terms: List[str] = field(default_factory=list)
    positive_terms: List[str] = field(default_factory=list)
    
    # Compliance checks
    truth_in_lending_compliant: bool = False
    state_usury_laws_compliant: bool = False
    mandatory_disclosures_present: bool = False
    compliance_issues: List[str] = field(default_factory=list)
    
    # Final recommendation
    approved: bool = False
    approval_conditions: List[str] = field(default_factory=list)
    risk_score: float = 0.5  # 0.0 to 1.0
    overall_rating: str = "unknown"  # excellent, good, fair, poor
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Agent coordination (inputs from other agents)
    lender_agent_input: Optional[Dict[str, Any]] = None
    budget_analyzer_input: Optional[Dict[str, Any]] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return asdict(self)


def validate_schema(data: Dict[str, Any], schema_class) -> bool:
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
        raise ValueError(f"Schema validation failed: {str(e)}")
