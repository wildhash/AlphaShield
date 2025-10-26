"""Orchestrator graph for deterministic DAG execution."""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from alphashield.context.packet import ContextPacket, make_packet
from alphashield.context.capsule import build_financial_capsule


@dataclass
class OriginationBundle:
    """Bundle containing all origination artifacts.
    
    Persisted to storage after orchestration completes.
    """
    trace_id: str
    loan_app_id: str
    user_id: str
    
    # Agent outputs
    loan_app: Dict[str, Any] = field(default_factory=dict)
    underwriting: Dict[str, Any] = field(default_factory=dict)
    coverage: Dict[str, Any] = field(default_factory=dict)
    offer: Dict[str, Any] = field(default_factory=dict)
    compliance: Dict[str, Any] = field(default_factory=dict)
    contract_review: Optional[Dict[str, Any]] = None
    
    # Audit trail
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'trace_id': self.trace_id,
            'loan_app_id': self.loan_app_id,
            'user_id': self.user_id,
            'loan_app': self.loan_app,
            'underwriting': self.underwriting,
            'coverage': self.coverage,
            'offer': self.offer,
            'compliance': self.compliance,
            'contract_review': self.contract_review,
            'audit_trail': self.audit_trail,
            'timestamp': self.timestamp,
        }


class StorageClient:
    """Client for persisting origination bundles."""
    
    def __init__(self, db_client=None):
        """Initialize storage client.
        
        Args:
            db_client: MongoDB client for persistence
        """
        self.db = db_client
    
    def store_bundle(self, bundle: OriginationBundle) -> str:
        """Store origination bundle.
        
        Args:
            bundle: OriginationBundle to persist
            
        Returns:
            Bundle ID
        """
        if not self.db:
            return bundle.trace_id
        
        bundles = self.db.get_collection('origination_bundles')
        result = bundles.insert_one(bundle.to_dict())
        return str(result.inserted_id)


def _emit_audit_event(
    bundle: OriginationBundle,
    node_name: str,
    payload_id: str,
    input_hash: str,
    status: str = "success"
) -> None:
    """Emit an audit trail event.
    
    Args:
        bundle: Origination bundle to add event to
        node_name: Name of the DAG node
        payload_id: ID of the payload/output
        input_hash: Hash of the input data
        status: Execution status (success/failure)
    """
    event = {
        'node': node_name,
        'payload_id': payload_id,
        'input_hash': input_hash,
        'status': status,
        'timestamp': datetime.utcnow(),
    }
    bundle.audit_trail.append(event)


def execute(
    trace_id: str,
    user_id: str,
    loan_app_id: str,
    db_client=None,
    embeddings_client=None,
    agents: Optional[Dict[str, Any]] = None,
    short_term_relief: bool = False
) -> OriginationBundle:
    """Execute the orchestration DAG.
    
    DAG structure:
    intake_doc & identity_fraud (parallel) → underwriting → 
    optional contract_review → risk_bridge → offer → compliance
    
    Args:
        trace_id: Unique trace identifier
        user_id: User identifier
        loan_app_id: Loan application identifier
        db_client: MongoDB client for context and storage
        embeddings_client: Embeddings client for vector search
        agents: Dictionary of agent instances (optional)
        short_term_relief: Flag for micro-refi short-term relief mode
        
    Returns:
        OriginationBundle with all agent outputs and audit trail
    """
    # Generate trace_id if not provided
    if not trace_id:
        trace_id = str(uuid.uuid4())
    
    # Build financial capsule for shared context
    capsule = build_financial_capsule(
        user_id=user_id,
        db_client=db_client,
        embeddings_client=embeddings_client
    )
    
    # Create context packet
    ctx = make_packet(trace_id, user_id, loan_app_id)
    ctx.add_context('capsule', capsule.to_dict())
    
    # Initialize origination bundle
    bundle = OriginationBundle(
        trace_id=trace_id,
        user_id=user_id,
        loan_app_id=loan_app_id
    )
    
    # Phase 1: Parallel execution of intake_doc and identity_fraud
    # For now, these are stubs since we don't have these agents yet
    intake_result = {
        'status': 'completed',
        'documents': ['w2', 'paystub', 'bank_statement'],
        'extracted_data': {},
    }
    _emit_audit_event(bundle, 'intake_doc', 'intake_1', ctx._hash_data(intake_result))
    
    identity_result = {
        'status': 'verified',
        'fraud_score': 0.05,
        'checks_passed': ['id_verification', 'address_verification'],
    }
    _emit_audit_event(bundle, 'identity_fraud', 'identity_1', ctx._hash_data(identity_result))
    
    ctx.add_context('intake_doc', intake_result)
    ctx.add_context('identity_fraud', identity_result)
    
    # Phase 2: Underwriting
    underwriting_result = {
        'approved': True,
        'credit_score': capsule.rolling_features.get('credit_score', 700),
        'debt_to_income_ratio': capsule.rolling_features.get('debt_to_income_ratio', 0.35),
        'max_loan_amount': 10000.0,
        'recommended_rate': 8.0,
    }
    bundle.underwriting = underwriting_result
    _emit_audit_event(bundle, 'underwriting', 'uw_1', ctx._hash_data(underwriting_result))
    ctx.add_context('underwriting', underwriting_result)
    
    # Phase 3: Optional contract review (if high-risk or requested)
    if underwriting_result.get('credit_score', 700) < 650 or short_term_relief:
        contract_review_result = {
            'reviewed': True,
            'fair_terms': True,
            'concerns': [],
            'recommendations': ['Standard terms approved'],
        }
        bundle.contract_review = contract_review_result
        _emit_audit_event(bundle, 'contract_review', 'cr_1', ctx._hash_data(contract_review_result))
        ctx.add_context('contract_review', contract_review_result)
    
    # Phase 4: Risk bridge (portfolio optimization)
    risk_bridge_result = {
        'coverage_ratio': 1.35,
        'allocation': {
            'bonds': 0.30,
            'index_funds': 0.40,
            'dividend_stocks': 0.20,
            'growth_stocks': 0.10,
        },
        'risk_level': 'medium',
    }
    bundle.coverage = risk_bridge_result
    _emit_audit_event(bundle, 'risk_bridge', 'rb_1', ctx._hash_data(risk_bridge_result))
    ctx.add_context('risk_bridge', risk_bridge_result)
    
    # Phase 5: Offer generation
    offer_result = {
        'principal': underwriting_result['max_loan_amount'],
        'interest_rate': underwriting_result['recommended_rate'],
        'term_months': 36,
        'monthly_payment': 313.36,
        'total_interest': 1281.03,
    }
    bundle.offer = offer_result
    _emit_audit_event(bundle, 'offer', 'offer_1', ctx._hash_data(offer_result))
    ctx.add_context('offer', offer_result)
    
    # Phase 6: Compliance check
    compliance_result = {
        'compliant': True,
        'checks': {
            'truth_in_lending': True,
            'usury_laws': True,
            'fair_lending': True,
            'disclosures': True,
        },
        'issues': [],
    }
    bundle.compliance = compliance_result
    _emit_audit_event(bundle, 'compliance', 'comp_1', ctx._hash_data(compliance_result))
    ctx.add_context('compliance', compliance_result)
    
    # Store loan application data in bundle
    bundle.loan_app = {
        'loan_app_id': loan_app_id,
        'user_id': user_id,
        'status': 'approved' if compliance_result['compliant'] else 'rejected',
        'short_term_relief': short_term_relief,
    }
    
    # Persist bundle
    storage = StorageClient(db_client)
    storage.store_bundle(bundle)
    
    return bundle
