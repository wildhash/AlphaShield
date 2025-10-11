"""Base agent class for AlphaShield multi-agent system."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from alphashield.database.mongodb_client import MongoDBClient
from alphashield.database.embeddings import EmbeddingsClient


# Import schema validation utilities
try:
    from alphashield.schemas.validation import validate_and_prepare_for_mongo
    SCHEMAS_AVAILABLE = True
except ImportError:
    SCHEMAS_AVAILABLE = False


class BaseAgent(ABC):
    """Abstract base class for all AlphaShield agents."""
    
    def __init__(self, name: str, db_client: MongoDBClient, 
                 embeddings_client: Optional[EmbeddingsClient] = None):
        """Initialize base agent.
        
        Args:
            name: Agent name
            db_client: MongoDB client for context storage
            embeddings_client: Optional embeddings client for semantic search
        """
        self.name = name
        self.db = db_client
        self.embeddings = embeddings_client
        
    def store_context(self, context_type: str, data: Dict[str, Any], 
                     generate_embedding: bool = False) -> str:
        """Store agent context with optional semantic embedding.
        
        Args:
            context_type: Type of context being stored
            data: Context data (can be dict or schema instance)
            generate_embedding: Whether to generate embedding for semantic search
            
        Returns:
            Context ID as string.
        """
        # Convert schema instance to dict if needed
        if SCHEMAS_AVAILABLE and hasattr(data, 'to_dict'):
            # This is a schema instance, validate and convert
            data = validate_and_prepare_for_mongo(data)
        
        embedding = None
        if generate_embedding and self.embeddings:
            # Create text representation for embedding
            text = f"{context_type}: {str(data)}"
            embedding = self.embeddings.embed_text(text)
        
        return self.db.store_context(
            agent_name=self.name,
            context_type=context_type,
            data=data,
            embedding=embedding
        )
    
    def get_shared_context(self, agent_name: Optional[str] = None,
                          context_type: Optional[str] = None,
                          limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve shared context from other agents.
        
        Args:
            agent_name: Filter by specific agent
            context_type: Filter by context type
            limit: Maximum number of results
            
        Returns:
            List of context documents.
        """
        return self.db.get_contexts(
            agent_name=agent_name,
            context_type=context_type,
            limit=limit
        )
    
    def store_structured_output(self, context_type: str, output_schema, 
                               generate_embedding: bool = False) -> str:
        """Store structured output using a schema.
        
        This is the recommended method for storing agent outputs with
        validated schemas before MongoDB upload.
        
        Args:
            context_type: Type of context being stored
            output_schema: Instance of an agent output schema
            generate_embedding: Whether to generate embedding for semantic search
            
        Returns:
            Context ID as string.
            
        Example:
            >>> from alphashield.schemas import LenderAgentOutput
            >>> output = LenderAgentOutput(borrower_id="123", approved=True)
            >>> agent.store_structured_output('lender_assessment', output)
        """
        return self.store_context(context_type, output_schema, generate_embedding)
    
    def log_action(self, action: str, details: Dict[str, Any]):
        """Log agent action for audit trail."""
        log_data = {
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow(),
        }
        self.store_context('action_log', log_data)
    
    @abstractmethod
    def process(self, loan_id: str, **kwargs) -> Dict[str, Any]:
        """Process agent-specific logic for a loan.
        
        Args:
            loan_id: Loan to process
            **kwargs: Additional agent-specific parameters
            
        Returns:
            Processing results.
        """
        pass
    
    def get_loan(self, loan_id: str):
        """Helper to retrieve loan data."""
        return self.db.get_loan(loan_id)
