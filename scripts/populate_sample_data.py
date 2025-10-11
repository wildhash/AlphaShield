"""Script to populate MongoDB with sample financial documents."""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alphashield.database.mongodb_client import MongoDBClient


def populate_sample_data():
    """Populate MongoDB with sample financial documents."""
    
    # Initialize MongoDB client
    mongo_client = MongoDBClient()
    
    # Sample Brokerage Account Statement
    brokerage_statement = {
        "document_type": "Brokerage_Account_Statement",
        "financial_institution": "Fidelity Investments",
        "institution_address": {
            "street": "245 Summer Street",
            "city": "Boston",
            "state": "MA",
            "zip_code": "02210",
            "phone": "1-800-343-3548",
            "website": "www.fidelity.com"
        },
        "statement_period": {
            "start_date": "2025-09-01",
            "end_date": "2025-09-30",
            "statement_date": "2025-09-30",
            "days_in_period": 30
        },
        "account_information": {
            "account_number": "Z12345678",
            "account_type": "Individual Taxable Brokerage Account",
            "account_registration": "Individual",
            "account_holder": {
                "name": "John M. Doe",
                "ssn_last_four": "6789",
                "address": {
                    "street": "789 Valencia Street, Apt 4B",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip_code": "94110"
                },
                "email": "john.doe@email.com",
                "phone": "(415) 555-0123"
            },
            "account_opened_date": "2020-05-15",
            "account_status": "Active",
            "tax_id": "***-**-6789"
        },
        "account_summary": {
            "beginning_balance": "2025-09-01",
            "beginning_total_value": 24150.00,
            "ending_balance": "2025-09-30",
            "ending_total_value": 25000.00,
            "net_change": 850.00,
            "net_change_percentage": 0.0352
        },
        "positions": [
            {
                "symbol": "SPY",
                "security_name": "SPDR S&P 500 ETF Trust",
                "quantity": 50.000,
                "price_per_share": 450.00,
                "market_value": 22500.00,
                "cost_basis": 21000.00,
                "unrealized_gain_loss": 1500.00
            },
            {
                "symbol": "XYZ",
                "security_name": "XYZ Technology Corp",
                "quantity": 10.000,
                "price_per_share": 50.00,
                "market_value": 500.00,
                "cost_basis": 550.00,
                "unrealized_gain_loss": -50.00
            }
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Sample Credit Card Statement
    credit_card_statement = {
        "document_type": "Credit_Card_Statement",
        "issuer": "JPMorgan Chase Bank, N.A.",
        "card_product": "Chase Sapphire Preferred",
        "statement_period": {
            "start_date": "2025-09-01",
            "end_date": "2025-09-30",
            "days_in_period": 30
        },
        "statement_date": "2025-09-30",
        "payment_due_date": "2025-10-25",
        "account_information": {
            "account_number": "****5678",
            "cardholder_name": "John M. Doe",
            "card_type": "Visa Signature",
            "member_since": "2018-03-15",
            "credit_limit": 5000.00,
            "available_credit": 150.00
        },
        "account_summary": {
            "previous_balance": 4200.00,
            "payments_and_credits": 150.00,
            "purchases": 1850.00,
            "cash_advances": 200.00,
            "fees_charged": 90.00,
            "interest_charged": 115.00,
            "new_balance": 6305.00,
            "over_limit_amount": 1305.00
        },
        "red_flags": [
            {
                "flag_type": "Over Credit Limit",
                "severity": "Critical",
                "description": "Account balance exceeds credit limit by $1,305",
                "date_identified": "2025-09-28"
            },
            {
                "flag_type": "Minimum Payment Only",
                "severity": "High",
                "description": "Paying only minimum for 4 consecutive months",
                "impact": "High interest charges accumulating"
            },
            {
                "flag_type": "Late Payment",
                "severity": "High",
                "description": "Missed payment in May 2025, incurred $40 late fee",
                "credit_impact": "Negative impact on credit score"
            }
        ],
        "spending_by_category": {
            "dining": {
                "transaction_count": 8,
                "total_amount": 495.62,
                "percentage_of_total": 26.8
            },
            "shopping": {
                "transaction_count": 5,
                "total_amount": 1679.98,
                "percentage_of_total": 90.8
            },
            "entertainment": {
                "transaction_count": 4,
                "total_amount": 636.98,
                "percentage_of_total": 34.4
            }
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Sample Experian Credit Report
    credit_report = {
        "document_type": "Credit_Report",
        "bureau": "Experian",
        "report_date": "2025-10-01",
        "report_number": "EXP-2025-10-001234567",
        "consumer_information": {
            "name": {
                "first_name": "John",
                "middle_initial": "M",
                "last_name": "Doe"
            },
            "ssn": "123-45-6789",
            "date_of_birth": "1990-01-15",
            "current_address": {
                "street": "789 Valencia Street",
                "apartment": "Apt 4B",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94110"
            }
        },
        "credit_score": {
            "score": 585,
            "score_model": "FICO Score 8",
            "score_range": "300-850",
            "score_date": "2025-10-01",
            "rating": "Poor",
            "percentile_rank": 15
        },
        "credit_summary": {
            "total_accounts": 12,
            "open_accounts": 8,
            "closed_accounts": 4,
            "delinquent_accounts": 3,
            "derogatory_marks": 2,
            "collections_accounts": 1,
            "total_balances": 38500,
            "total_credit_limit": 25000,
            "hard_inquiries_6mo": 8,
            "hard_inquiries_12mo": 12
        },
        "risk_indicators": {
            "charge_offs": 1,
            "collections": 1,
            "public_records": 1,
            "late_payments_12mo": 6,
            "accounts_90_plus_days_delinquent": 1,
            "high_utilization_accounts": 3,
            "recent_credit_seeking_behavior": "High - 8 inquiries in 6 months"
        },
        "alerts_and_warnings": [
            {
                "alert_type": "Charge Off",
                "severity": "High",
                "description": "Capital One account charged off in December 2024",
                "date": "2024-12-15"
            },
            {
                "alert_type": "Public Record",
                "severity": "High",
                "description": "Civil judgment filed in San Francisco County",
                "date": "2024-06-20"
            },
            {
                "alert_type": "Collection Account",
                "severity": "High",
                "description": "Collection account from ABC Collections",
                "date": "2024-08-15"
            }
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert documents into respective collections
    print("Populating MongoDB with sample data...")
    
    # Store brokerage statement
    brokerage_collection = mongo_client.get_collection('brokerage_statements')
    brokerage_id = brokerage_collection.insert_one(brokerage_statement).inserted_id
    print(f"✓ Inserted brokerage statement: {brokerage_id}")
    
    # Store credit card statement
    credit_card_collection = mongo_client.get_collection('credit_card_statements')
    credit_card_id = credit_card_collection.insert_one(credit_card_statement).inserted_id
    print(f"✓ Inserted credit card statement: {credit_card_id}")
    
    # Store credit report
    credit_report_collection = mongo_client.get_collection('credit_reports')
    credit_report_id = credit_report_collection.insert_one(credit_report).inserted_id
    print(f"✓ Inserted credit report: {credit_report_id}")
    
    print("\n✅ Sample data population complete!")
    print(f"\nCollections created:")
    print(f"  - brokerage_statements (1 document)")
    print(f"  - credit_card_statements (1 document)")
    print(f"  - credit_reports (1 document)")
    
    return {
        'brokerage_id': str(brokerage_id),
        'credit_card_id': str(credit_card_id),
        'credit_report_id': str(credit_report_id)
    }


if __name__ == "__main__":
    try:
        result = populate_sample_data()
        print(f"\nInserted IDs: {result}")
    except Exception as e:
        print(f"❌ Error populating data: {e}")
        sys.exit(1)
