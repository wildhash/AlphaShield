# AlphaShield Scripts

This directory contains utility scripts for the AlphaShield system.

## populate_sample_data.py

Populates MongoDB with sample financial documents for testing and demonstration purposes.

### Sample Documents Created

The script creates three types of financial documents:

1. **Brokerage Account Statement** (Fidelity Investments)
   - Collection: `brokerage_statements`
   - Contains account information, positions (SPY, XYZ), and performance metrics

2. **Credit Card Statement** (Chase Sapphire Preferred)
   - Collection: `credit_card_statements`
   - Includes red flags like over-limit amount, late payments, and spending patterns

3. **Credit Report** (Experian)
   - Collection: `credit_reports`
   - Features low credit score (585), risk indicators, and alerts

### Usage

1. **Set up MongoDB connection:**
   ```bash
   export MONGODB_URI="your_mongodb_connection_string"
   ```

2. **Run the script:**
   ```bash
   python scripts/populate_sample_data.py
   ```

### Expected Output

```
Populating MongoDB with sample data...
✓ Inserted brokerage statement: <ObjectId>
✓ Inserted credit card statement: <ObjectId>
✓ Inserted credit report: <ObjectId>

✅ Sample data population complete!

Collections created:
  - brokerage_statements (1 document)
  - credit_card_statements (1 document)
  - credit_reports (1 document)

Inserted IDs: {'brokerage_id': '...', 'credit_card_id': '...', 'credit_report_id': '...'}
```

### Use Cases

These sample documents are designed to test AlphaShield's financial analysis capabilities:

- **Brokerage Statement**: Investment tracking and portfolio analysis
- **Credit Card Statement**: Spending pattern analysis and red flag detection
- **Credit Report**: Credit risk assessment and borrower evaluation

The data includes realistic financial indicators that demonstrate various risk levels and financial situations that the AlphaShield AI agents can analyze.
