# MongoDB Data Seeding Instructions

## Prerequisites

1. **MongoDB**: Ensure MongoDB is running on your local machine or update the `MONGODB_URI` in the seed script
2. **Python**: Python 3.7+ with pymongo installed
3. **Data Files**: Place all JSON statement files in the same directory as the seed script

## Installation

Install the required Python package:

```bash
pip install pymongo
```

Or install all project dependencies:

```bash
pip install -r requirements.txt
```

## Directory Structure

```
AlphaShield/
├── scripts/
│   └── seed_chase_statements.py
├── chase_statement_202410.json
├── chase_statement_202411.json
├── chase_statement_202412.json
├── chase_statement_202501.json
└── chase_statement_202502.json
```

## Running the Seed Script

Execute the seed script from the root directory:

```bash
python scripts/seed_chase_statements.py
```

Or with explicit Python 3:

```bash
python3 scripts/seed_chase_statements.py
```

## Configuration

The script uses the MongoDB connection configuration from your environment variables or the MongoDBClient defaults.

Environment variable:
```bash
export MONGODB_URI="mongodb://localhost:27017"
```

Or create a `.env` file in the project root:
```
MONGODB_URI=mongodb://localhost:27017
```

Database and collection names:
- **Database**: `alphashield`
- **Collection**: `credit_card_statements`

## Data Structure

Each statement document contains:
- **Account information**: Account number, cardholder name, credit limit, available credit
- **Statement period**: Start date, end date, days in period
- **Payment information**: Due date, minimum payment, new balance
- **Transactions array**: Detailed list of all transactions with dates, amounts, categories
- **Spending by category**: Aggregated spending statistics by merchant category
- **Spending patterns**: Total purchases, transaction count, averages, largest purchase
- **Interest charges**: Total interest, APRs, balance subject to interest
- **Red flags**: Array of financial warning indicators with severity levels
- **Financial health indicators**: Credit utilization ratio, payment ratios, balance history

## Indexes Created

The script automatically creates indexes on:
- `statement_date` - For quickly finding statements by date
- `account_information.account_number` - For account-specific queries
- `statement_period.start_date` - For date range queries
- `statement_period.end_date` - For date range queries
- `transactions.transaction_date` - For transaction-level queries

## Example Queries

After seeding, you can query the data:

### Python Example

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["alphashield"]
statements = db["credit_card_statements"]

# Get all statements
all_statements = statements.find()

# Get statement for specific month
oct_statement = statements.find_one({"statement_date": "2024-10-31"})

# Get total spending by category
pipeline = [
    {"$unwind": "$transactions"},
    {"$group": {
        "_id": "$transactions.merchant_category",
        "total": {"$sum": "$transactions.amount"}
    }}
]
spending_by_category = statements.aggregate(pipeline)

# Find statements with red flags
flagged = statements.find({"red_flags": {"$ne": []}})

# Get statements with high credit utilization
high_utilization = statements.find({
    "financial_health_indicators.credit_utilization_ratio": {"$gt": 0.9}
})

# Get statements sorted by balance
by_balance = statements.find().sort("account_summary.new_balance", -1)
```

### MongoDB Shell Example

```javascript
// Connect to database
use alphashield

// Find all statements
db.credit_card_statements.find()

// Find statements over credit limit
db.credit_card_statements.find({
  "account_summary.new_balance": {
    $gt: db.credit_card_statements.findOne().account_information.credit_limit
  }
})

// Get average interest charged
db.credit_card_statements.aggregate([
  {
    $group: {
      _id: null,
      avgInterest: { $avg: "$interest_charges.total_interest_charged" }
    }
  }
])

// Find statements with critical red flags
db.credit_card_statements.find({
  "red_flags.severity": "Critical"
})

// Get total spending over time
db.credit_card_statements.aggregate([
  {
    $project: {
      statement_date: 1,
      total_spending: "$spending_patterns.total_new_purchases"
    }
  },
  { $sort: { statement_date: 1 } }
])
```

## Output

The script will display:
- Progress for each file loaded
- Number of statements inserted
- Total transactions across all statements
- Total spending and interest charged
- Date range covered (October 2024 to February 2025)

Example output:
```
============================================================
Chase Credit Card Statement Seeder
============================================================

Clearing existing data from credit_card_statements...
Loading chase_statement_202410.json...
✓ Loaded chase_statement_202410.json
Loading chase_statement_202411.json...
✓ Loaded chase_statement_202411.json
Loading chase_statement_202412.json...
✓ Loaded chase_statement_202412.json
Loading chase_statement_202501.json...
✓ Loaded chase_statement_202501.json
Loading chase_statement_202502.json...
✓ Loaded chase_statement_202502.json

✓ Successfully inserted 5 statements into MongoDB
  Database: alphashield
  Collection: credit_card_statements

Creating indexes...
✓ Indexes created

=== Summary Statistics ===
Total Statements: 5
Total Transactions: 53
Total New Purchases: $8,552.80
Total Interest Charged: $659.20
Date Range: 2024-10-01 to 2025-02-28

✓ Database connection closed

✓ Seeding completed successfully!
```

## Troubleshooting

### Connection Error
**Problem**: `ValueError: MongoDB URI not provided`

**Solution**: Ensure MongoDB URI is set in environment variable or `.env` file:
```bash
export MONGODB_URI="mongodb://localhost:27017"
```

### MongoDB Not Running
**Problem**: `ServerSelectionTimeoutError: localhost:27017: [Errno 111] Connection refused`

**Solution**: Start MongoDB service:
```bash
# On Linux
sudo systemctl start mongod

# On macOS
brew services start mongodb-community

# Or run manually
mongod --dbpath /path/to/data
```

### File Not Found
**Problem**: `✗ File not found: chase_statement_202410.json`

**Solution**: Verify all JSON files are in the root directory of the project, not in the scripts directory.

### Permission Error
**Problem**: `OperationFailure: not authorized`

**Solution**: Check MongoDB user permissions for insert operations. You may need to create a user with appropriate permissions:
```javascript
use alphashield
db.createUser({
  user: "alphashield_user",
  pwd: "password",
  roles: [{ role: "readWrite", db: "alphashield" }]
})
```

### Invalid JSON
**Problem**: `✗ Invalid JSON in file: chase_statement_202410.json`

**Solution**: Validate JSON files using a JSON validator or:
```bash
python -m json.tool chase_statement_202410.json
```

## Data Refresh

To refresh the data:

1. **Full Refresh**: The script clears existing data before inserting. Simply run it again:
   ```bash
   python scripts/seed_chase_statements.py
   ```

2. **Append Only**: Edit the script and comment out the delete line:
   ```python
   # collection.delete_many({})  # Comment this line
   ```

3. **Manual Clear**: Clear the collection manually:
   ```python
   from pymongo import MongoClient
   client = MongoClient("mongodb://localhost:27017")
   db = client["alphashield"]
   db["credit_card_statements"].delete_many({})
   ```

## Notes

- The script uses `datetime.utcnow()` for timestamp fields
- Each document includes metadata fields: `_inserted_at` and `_source_file`
- The script will skip files that don't exist or contain invalid JSON
- All currency values are in USD
- Red flags are prioritized by severity: Critical > High > Medium > Low
