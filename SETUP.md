# AlphaShield Setup Guide

This guide will help you set up and run the AlphaShield multi-agent financial system.

## Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account (free tier available)
- Voyage AI API key (for embeddings)

## Quick Start (Demo Mode)

To see the system architecture and core concepts without API keys:

```bash
# Clone the repository
git clone https://github.com/wildhash/AlphaShield.git
cd AlphaShield

# Install dependencies
pip install -r requirements.txt

# Run the demo (works without API keys)
python demo.py
```

This will show:
- The 60/40 loan split model
- Savings calculation (8% vs 24%)
- Investment strategy breakdown
- Overview of the 6 AI agents
- Social impact metrics

## Full Setup (With API Access)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `pymongo[srv]` - MongoDB Atlas connection
- `voyageai` - Voyage AI embeddings
- `python-dotenv` - Environment variable management
- `anthropic` - Claude API (optional, for advanced AI features)
- `openai` - OpenAI API (optional, for advanced AI features)
- `numpy` - Numerical computations
- `pandas` - Data analysis

### 2. Set Up MongoDB Atlas

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster (free M0 tier is sufficient for testing)
3. Create a database user with read/write permissions
4. Whitelist your IP address or allow access from anywhere (0.0.0.0/0)
5. Get your connection string (should look like `mongodb+srv://username:password@cluster.mongodb.net/`)

### 3. Get Voyage AI API Key

1. Sign up at [Voyage AI](https://www.voyageai.com/)
2. Generate an API key from your dashboard
3. Keep this key secure - you'll add it to your `.env` file

### 4. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Add your credentials:
```
MONGODB_URI=mongodb+srv://your-username:your-password@cluster.mongodb.net/
VOYAGE_API_KEY=your_voyage_api_key_here
```

### 5. Run the Full Example

```bash
python example.py
```

This will:
1. Initialize all 6 AI agents
2. Originate a sample loan with contract review
3. Invest 60% of funds algorithmically
4. Monitor the loan with all agents
5. Generate AI recommendations
6. Show savings vs predatory lenders

## Running Tests

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_loan_model -v
```

Test coverage includes:
- Loan model and 60/40 split calculations
- Monthly payment computations
- Savings calculations (8% vs 24%)
- Agent functionality with mocked databases

## Project Structure

```
AlphaShield/
├── alphashield/              # Main package
│   ├── agents/              # 6 AI agents
│   │   ├── base_agent.py           # Abstract base class
│   │   ├── lender_agent.py         # Loan origination & portfolio
│   │   ├── alpha_trading_agent.py  # 60% investment management
│   │   ├── spending_guard_agent.py # Spending anomaly detection
│   │   ├── budget_analyzer_agent.py # Budget analysis
│   │   ├── tax_optimizer_agent.py  # Tax optimization
│   │   └── contract_review_agent.py # Contract review
│   ├── database/            # Data layer
│   │   ├── mongodb_client.py       # MongoDB interface
│   │   └── embeddings.py           # Voyage AI embeddings
│   ├── models/              # Data models
│   │   └── loan.py                 # Loan and split models
│   └── orchestrator.py      # Multi-agent coordinator
├── tests/                   # Test suite
├── demo.py                  # Simple demo (no API required)
├── example.py              # Full system example
└── requirements.txt        # Python dependencies
```

## Usage Examples

### Basic Loan Origination

```python
from alphashield.orchestrator import AlphaShieldOrchestrator

# Initialize system
shield = AlphaShieldOrchestrator()

# Originate a loan
result = shield.originate_loan(
    borrower_id="borrower_123",
    principal=10000,
    interest_rate=8.0,
    term_months=36
)

print(f"Loan ID: {result['loan_id']}")
print(f"Investment: ${result['split']['investment']}")
print(f"To Borrower: ${result['split']['borrower']}")
```

### Monitoring a Loan

```python
# Provide borrower data for comprehensive monitoring
borrower_data = {
    'income': 4500,
    'expenses': {
        'housing': 1200,
        'utilities': 200,
        'food': 400,
        'transportation': 300,
        'insurance': 250,
    },
    'transactions': [
        {'amount': 150, 'category': 'food', 'timestamp': '2024-01-15'},
        {'amount': 1200, 'category': 'housing', 'timestamp': '2024-01-01'},
    ],
    'deductions': {
        'retirement': 500,
        'charitable': 100,
    },
    'filing_status': 'single'
}

# Monitor with all 6 agents
monitoring = shield.monitor_loan(loan_id, borrower_data)

# Access agent insights
print(monitoring['portfolio_metrics'])
print(monitoring['investment']['performance'])
print(monitoring['budget_analysis'])
print(monitoring['spending_analysis'])
print(monitoring['tax_optimization'])
print(monitoring['risk_assessment'])
```

### Getting Recommendations

```python
# Get AI-generated recommendations
recommendations = shield.get_borrower_recommendations(loan_id)

print("Spending Recommendations:", recommendations['spending_recommendations'])
print("Budget Recommendations:", recommendations['budget_recommendations'])
print("Tax Recommendations:", recommendations['tax_recommendations'])
print("Investment Recommendations:", recommendations['investment_recommendations'])
```

## Understanding the System

### The 60/40 Model

For every loan:
- **60%** goes to an investment fund
  - Managed by Alpha Trading agent
  - Diversified portfolio (bonds, index funds, stocks)
  - Generates returns to help cover payments
- **40%** goes directly to borrower
  - Available for immediate use
  - No restrictions

### The 6 AI Agents

1. **Lender Agent** - Portfolio management and risk assessment
2. **Alpha Trading Agent** - Algorithmic investment of 60% allocation
3. **Spending Guard Agent** - Real-time anomaly detection
4. **Budget Analyzer Agent** - Income/expense optimization
5. **Tax Optimizer Agent** - Tax strategy and savings
6. **Contract Review Agent** - Fair lending practices

All agents share context through MongoDB and Voyage AI embeddings, enabling coordinated decision-making without direct communication.

### Key Metrics

- **Interest Rate**: 8% (vs 24% predatory)
- **Coverage Ratio**: Investment returns / Monthly payment
- **Risk Score**: 0-1 scale based on multiple factors
- **Budget Health**: healthy, concerning, or critical
- **Savings**: Total saved vs predatory lenders

## Troubleshooting

### MongoDB Connection Issues

If you see `MongoDBClient` errors:
1. Check your connection string format
2. Ensure your IP is whitelisted in MongoDB Atlas
3. Verify username/password are correct
4. Test connection string in MongoDB Compass

### Voyage AI Errors

If embeddings fail:
1. Verify your API key is correct
2. Check you have remaining API credits
3. Ensure you're using supported model names

### Import Errors

If you see module import errors:
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or install specific package
pip install pymongo[srv]
```

## Next Steps

1. **Explore the Code**: Start with `demo.py` and `alphashield/models/loan.py`
2. **Run Tests**: Verify everything works with `python -m unittest discover tests`
3. **Try Examples**: Run `python example.py` (with API keys)
4. **Customize**: Modify investment strategies, add new agents, or adjust parameters
5. **Contribute**: Check CONTRIBUTING.md for guidelines

## Support

- **Issues**: Report bugs at https://github.com/wildhash/AlphaShield/issues
- **Documentation**: Full API docs coming soon
- **Examples**: See `example.py` for comprehensive usage

## Security Notes

- Never commit `.env` file to version control
- Keep API keys secure and rotate regularly
- Use environment variables for all credentials
- MongoDB: Use least-privilege access controls
- Validate all borrower data inputs

---

**AlphaShield** - Eliminating the poverty tax through AI-powered finance 💰🛡️
