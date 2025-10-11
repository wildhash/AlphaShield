# AlphaShield Agent Output Schemas

This directory contains standardized output schemas for all AlphaShield agents. These schemas ensure consistent data structures before uploading to MongoDB.

## Purpose

Based on the **Agent Document Requirements & Processing Strategy**, these schemas define the exact output format each agent should use when processing documents and storing results in MongoDB.

## Files

- **`agent_schemas.py`**: Core schema definitions for all 6 agents
- **`validation.py`**: Helper functions for schema validation and MongoDB preparation
- **`__init__.py`**: Package exports

## Schemas Overview

### 1. LenderAgentOutput
**Purpose**: Comprehensive underwriting and risk assessment  
**Documents**: Credit Report, Credit Card Statements, W-2, Pay Stub, Bank Statements

Key fields:
- Credit metrics (score, history, utilization)
- Payment history (on-time, late, missed)
- Income verification (gross, net, employment)
- Risk scores and approval decisions

### 2. AlphaTradingAgentOutput
**Purpose**: Investment performance and tax-efficient portfolio management  
**Documents**: Brokerage Statement, Form 1040

Key fields:
- Portfolio positions with unrealized gains/losses
- Asset allocation and performance metrics
- Tax bracket and optimization opportunities
- Loan coverage calculations

### 3. SpendingGuardAgentOutput
**Purpose**: Transaction-level analysis and anomaly detection  
**Documents**: Credit Card Statements, Bank Statements

Key fields:
- Category spending and statistics
- Anomaly detection and alerts
- High-risk spending patterns
- Velocity analysis and recommendations

### 4. BudgetAnalyzerAgentOutput
**Purpose**: Income/expense analysis using 50/30/20 rule  
**Documents**: Pay Stub, Credit Card Statements, Credit Report

Key fields:
- Income (gross, net) and expenses by category
- 50/30/20 breakdown (needs/wants/savings)
- Budget health ratios and warnings
- Loan affordability assessment

### 5. TaxOptimizerAgentOutput
**Purpose**: Tax analysis and optimization strategies  
**Documents**: Form 1040, W-2, Pay Stub, Brokerage Statement

Key fields:
- Prior year tax data and brackets
- Current year projections
- Optimization opportunities (401k, HSA, etc.)
- Short and long-term tax strategies

### 6. ContractReviewAgentOutput
**Purpose**: Contract fairness and compliance checking  
**Documents**: Loan Agreement, Credit Report, Pay Stub

Key fields:
- Contract terms (principal, APR, fees)
- Affordability ratios
- Market comparison and competitive position
- Compliance checks and final approval

## Usage

### Basic Usage

```python
from alphashield.schemas import LenderAgentOutput

# Create structured output
output = LenderAgentOutput(
    borrower_id="borrower_123",
    credit_score=720,
    approved=True
)

# Convert to dict for MongoDB
mongo_data = output.to_dict()
```

### Agent Integration

Agents should use the `store_structured_output()` method from `BaseAgent`:

```python
from alphashield.agents.base_agent import BaseAgent
from alphashield.schemas import LenderAgentOutput

class MyLenderAgent(BaseAgent):
    def process(self, loan_id: str, **kwargs):
        # Create schema output
        output = LenderAgentOutput(
            borrower_id="borrower_123",
            credit_score=720,
            approved=True
        )
        
        # Store using structured method (auto-validates)
        self.store_structured_output('lender_assessment', output)
        
        # Return dict for backwards compatibility
        return output.to_dict()
```

### Validation

```python
from alphashield.schemas.agent_schemas import validate_schema
from alphashield.schemas import LenderAgentOutput

# Validate data before creating schema
data = {'borrower_id': 'borrower_123', 'credit_score': 720}
validate_schema(data, LenderAgentOutput)  # Raises ValueError if invalid
```

### Helper Functions

```python
from alphashield.schemas.validation import (
    prepare_lender_output,
    validate_and_prepare_for_mongo
)

# Quick creation with required fields
output = prepare_lender_output(
    borrower_id="borrower_123",
    credit_score=720
)

# Validate and prepare for MongoDB
mongo_data = validate_and_prepare_for_mongo(output)
```

## Benefits

1. **Type Safety**: Catch errors at development time with type hints
2. **Consistency**: All agents use identical structures for similar data
3. **Validation**: Required fields enforced automatically
4. **Documentation**: Self-documenting code with clear field names
5. **Evolution**: Easy to add new fields without breaking existing code
6. **Testing**: Simple to create test fixtures with known schemas
7. **Coordination**: Other agents know exactly what data to expect

## Testing

Comprehensive tests available in `tests/test_agent_schemas.py`:

```bash
# Run schema tests
python3 -m unittest tests.test_agent_schemas -v
```

All 16 schema tests are passing.

## Examples

See the `examples/` directory for complete working examples:

- **`schema_usage_example.py`**: Basic schema creation and conversion
- **`agent_schema_integration.py`**: Full agent integration patterns

Run examples:
```bash
PYTHONPATH=. python3 examples/schema_usage_example.py
PYTHONPATH=. python3 examples/agent_schema_integration.py
```

## Documentation

For detailed field specifications and document requirements, see:
- **[docs/AGENT_SCHEMAS.md](../../docs/AGENT_SCHEMAS.md)**: Complete schema documentation

## Design Principles

1. **Dataclass-based**: Using Python dataclasses for simplicity and type safety
2. **Optional by default**: Most fields optional to support incremental data gathering
3. **Nested structures**: Support complex data with proper typing
4. **MongoDB ready**: All schemas provide `to_dict()` for storage
5. **Timestamp tracking**: Automatic timestamp on all schema instances

## Future Enhancements

- [ ] Pydantic migration for enhanced validation
- [ ] JSON Schema export for API documentation
- [ ] Schema versioning for evolution support
- [ ] Automatic embedding generation integration
- [ ] MongoDB index recommendations

## Questions?

For detailed information about:
- **Schema specifications**: See [docs/AGENT_SCHEMAS.md](../../docs/AGENT_SCHEMAS.md)
- **Integration patterns**: See [examples/agent_schema_integration.py](../../examples/agent_schema_integration.py)
- **Architecture**: See [ARCHITECTURE.md](../../ARCHITECTURE.md)
