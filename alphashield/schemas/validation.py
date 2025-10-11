"""Schema validation and helper utilities for agents."""
from typing import Dict, Any, Type, TypeVar
from alphashield.schemas.agent_schemas import (
    LenderAgentOutput,
    AlphaTradingAgentOutput,
    SpendingGuardAgentOutput,
    BudgetAnalyzerAgentOutput,
    TaxOptimizerAgentOutput,
    ContractReviewAgentOutput,
)

T = TypeVar('T')


def create_output_from_dict(schema_class: Type[T], data: Dict[str, Any], 
                           strict: bool = False) -> T:
    """Create schema output from dictionary with optional strict validation.
    
    Args:
        schema_class: Schema class to instantiate
        data: Dictionary of data to convert
        strict: If True, only include fields defined in schema
        
    Returns:
        Instance of schema_class
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    if strict:
        # Filter data to only include fields defined in the schema
        import inspect
        valid_fields = set(inspect.signature(schema_class).parameters.keys())
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return schema_class(**filtered_data)
    else:
        # Try to create with all fields, let schema handle unknown fields
        return schema_class(**data)


def merge_with_defaults(schema_class: Type[T], partial_data: Dict[str, Any]) -> T:
    """Merge partial data with schema defaults.
    
    Useful for updating existing records or creating with partial information.
    
    Args:
        schema_class: Schema class to use
        partial_data: Partial dictionary of data
        
    Returns:
        Instance of schema_class with defaults filled in
    """
    # Get default instance
    import inspect
    sig = inspect.signature(schema_class)
    
    # Build kwargs with defaults where not provided
    kwargs = {}
    for param_name, param in sig.parameters.items():
        if param_name in partial_data:
            kwargs[param_name] = partial_data[param_name]
        elif param.default != inspect.Parameter.empty:
            kwargs[param_name] = param.default
        # If no default and not provided, required field will raise error
    
    return schema_class(**kwargs)


def validate_and_prepare_for_mongo(output_instance) -> Dict[str, Any]:
    """Validate schema instance and prepare for MongoDB storage.
    
    Args:
        output_instance: Instance of any agent output schema
        
    Returns:
        Dictionary ready for MongoDB insertion
        
    Raises:
        ValueError: If instance is not a valid schema type
    """
    valid_types = (
        LenderAgentOutput,
        AlphaTradingAgentOutput,
        SpendingGuardAgentOutput,
        BudgetAnalyzerAgentOutput,
        TaxOptimizerAgentOutput,
        ContractReviewAgentOutput,
    )
    
    if not isinstance(output_instance, valid_types):
        raise ValueError(f"Invalid schema type: {type(output_instance)}")
    
    # Convert to dict
    data = output_instance.to_dict()
    
    # MongoDB specific preparations (if needed)
    # For example, ensure all datetime objects are properly formatted
    # This is where you could add any MongoDB-specific transformations
    
    return data


# Agent-specific helper functions

def prepare_lender_output(borrower_id: str, **kwargs) -> LenderAgentOutput:
    """Helper to prepare LenderAgent output with required fields."""
    return LenderAgentOutput(borrower_id=borrower_id, **kwargs)


def prepare_trading_output(loan_id: str, **kwargs) -> AlphaTradingAgentOutput:
    """Helper to prepare AlphaTradingAgent output with required fields."""
    return AlphaTradingAgentOutput(loan_id=loan_id, **kwargs)


def prepare_spending_output(borrower_id: str, **kwargs) -> SpendingGuardAgentOutput:
    """Helper to prepare SpendingGuardAgent output with required fields."""
    return SpendingGuardAgentOutput(borrower_id=borrower_id, **kwargs)


def prepare_budget_output(borrower_id: str, **kwargs) -> BudgetAnalyzerAgentOutput:
    """Helper to prepare BudgetAnalyzerAgent output with required fields."""
    return BudgetAnalyzerAgentOutput(borrower_id=borrower_id, **kwargs)


def prepare_tax_output(borrower_id: str, **kwargs) -> TaxOptimizerAgentOutput:
    """Helper to prepare TaxOptimizerAgent output with required fields."""
    return TaxOptimizerAgentOutput(borrower_id=borrower_id, **kwargs)


def prepare_contract_output(loan_id: str, **kwargs) -> ContractReviewAgentOutput:
    """Helper to prepare ContractReviewAgent output with required fields."""
    return ContractReviewAgentOutput(loan_id=loan_id, **kwargs)
