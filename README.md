# AlphaShield

Self-funding loans that eliminate the poverty tax through AI agents managing investments, spending, and risk for both lenders and borrowers.

## 🎯 Mission

Replace 24% predatory interest rates with 8% self-sustaining loans through AI-powered algorithmic investment and multi-agent coordination.

## 🚀 Key Innovation: The 60/40 Model

When a borrower takes a $10,000 loan:
- **60% ($6,000)** → Investment fund managed by Alpha Trading agent
  - Generates returns algorithmically to cover loan payments
  - Portfolio diversified across bonds, index funds, and stocks
  - Expected returns designed to cover monthly payments
- **40% ($4,000)** → Directly to borrower
  - Available for immediate use
  - No restrictions on spending

## 🤖 Six AI Agents Working Together

### 1. **Lender Agent**
- Originates loans with 8% interest rate (vs 24% predatory)
- Manages portfolio and assesses risk
- Coordinates with other agents for holistic view

### 2. **Alpha Trading Agent**
- Invests 60% of loan algorithmically
- Manages portfolio rebalancing
- Generates returns to cover monthly payments
- Supports conservative, balanced, and aggressive strategies

### 3. **Spending Guard Agent**
- Detects spending anomalies in real-time
- Flags high-risk spending patterns
- Identifies rapid spending after disbursement
- Generates alerts for concerning behavior

### 4. **Budget Analyzer Agent**
- Analyzes borrower income and expenses
- Assesses loan payment affordability
- Generates optimization recommendations
- Forecasts budget sustainability

### 5. **Tax Optimizer Agent**
- Identifies tax optimization opportunities
- Calculates potential savings
- Generates short-term and long-term strategies
- Analyzes deductions and retirement contributions

### 6. **Contract Review Agent**
- Reviews loan terms for fairness
- Compares to market alternatives
- Identifies excessive fees and penalties
- Calculates true APR including fees

## 🔗 Shared Context via MongoDB & Voyage AI

All agents share context through:
- **MongoDB Atlas**: Centralized storage for loan data, transactions, and agent insights
- **Voyage AI Embeddings**: Semantic search across agent contexts
- Real-time coordination without direct agent-to-agent communication

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/wildhash/AlphaShield.git
cd AlphaShield

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials:
# - MONGODB_URI: MongoDB Atlas connection string
# - VOYAGE_API_KEY: Voyage AI API key
```

## 🎮 Quick Start

```python
from alphashield.orchestrator import AlphaShieldOrchestrator

# Initialize AlphaShield with all 6 agents
shield = AlphaShieldOrchestrator()

# Originate a $10,000 loan at 8% for 36 months
result = shield.originate_loan(
    borrower_id="borrower_123",
    principal=10000,
    interest_rate=8.0,
    term_months=36
)

print(f"Loan ID: {result['loan_id']}")
print(f"Investment: ${result['split']['investment']}")
print(f"To Borrower: ${result['split']['borrower']}")

# Monitor loan with borrower data
monitoring = shield.monitor_loan(
    loan_id=result['loan_id'],
    borrower_data={
        'income': 4500,
        'expenses': {'housing': 1200, 'food': 400, ...},
        'transactions': [...],
        'deductions': {'retirement': 500, ...}
    }
)

# Get AI recommendations
recommendations = shield.get_borrower_recommendations(result['loan_id'])
```

## 📊 Example Output

```
✓ Loan originated successfully!
  Loan ID: 507f1f77bcf86cd799439011
  Principal: $10,000.00
  Interest Rate: 8% (vs 24% predatory rate)

  Loan Split (60/40 Model):
    Investment Fund: $6,000.00 (60%)
    To Borrower: $4,000.00 (40%)

  Investment Strategy: Balanced
    Expected Annual Return: 10.0%
    Expected Monthly Return: $50.00
    Monthly Payment Needed: $313.36
    Coverage Ratio: 1.60x

💵 Savings vs Predatory Lender (24% rate):
  AlphaShield Interest (3 years): $2,400.00
  Predatory Interest (3 years): $7,200.00
  💰 TOTAL SAVINGS: $4,800.00
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AlphaShield                          │
│              Self-Funding Loan System                   │
└─────────────────────────────────────────────────────────┘
                          │
            ┌─────────────┴──────────────┐
            │                            │
     ┌──────▼──────┐            ┌───────▼───────┐
     │   MongoDB   │            │   Voyage AI   │
     │   Atlas     │            │  Embeddings   │
     │  (Context)  │            │   (Search)    │
     └──────┬──────┘            └───────┬───────┘
            │                            │
────────────┴────────────────────────────┴───────────────
                Shared Context Layer
─────────────────────────────────────────────────────────
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
┌───▼───┐  ┌─────▼─────┐ ┌──▼───┐  ┌──────▼──────┐
│Lender │  │  Alpha    │ │Budget│  │  Spending   │
│Agent  │  │  Trading  │ │Analyz│  │   Guard     │
└───┬───┘  └─────┬─────┘ └──┬───┘  └──────┬──────┘
    │            │           │             │
    └────────────┼───────────┼─────────────┘
                 │           │
          ┌──────▼───┐  ┌───▼──────┐
          │   Tax    │  │ Contract │
          │Optimizer │  │  Review  │
          └──────────┘  └──────────┘
```

## 🧪 Running the Example

```bash
python example.py
```

This demonstrates:
1. Loan origination with contract review
2. 60/40 split and investment allocation
3. Ongoing monitoring with all 6 agents
4. AI-generated recommendations
5. Savings calculation vs predatory lenders

## 💡 Use Cases

### For Borrowers
- Access capital at 8% instead of 24%
- Receive spending and budget guidance
- Get tax optimization strategies
- Build financial literacy through AI coaching

### For Lenders
- Reduced default risk through monitoring
- Algorithmic investment generates returns
- AI-powered risk assessment
- Portfolio management automation

### Social Impact
- **Eliminate poverty tax**: Save borrowers thousands in interest
- **Financial inclusion**: AI-guided financial management
- **Wealth building**: Investment education and returns
- **Sustainable lending**: Self-funding model reduces dependence on high rates

## 📈 Performance Metrics

The system tracks:
- **Investment Performance**: Returns vs. payment obligations
- **Risk Capacity**: Months of payments covered by investment
- **Budget Health**: Income/expense ratio analysis
- **Spending Patterns**: Anomaly detection and alerts
- **Tax Savings**: Optimization opportunities identified
- **Contract Fairness**: APR analysis and market comparison

## 🔧 Development

### Project Structure

```
AlphaShield/
├── alphashield/
│   ├── agents/
│   │   ├── base_agent.py           # Abstract base class
│   │   ├── lender_agent.py         # Loan origination
│   │   ├── alpha_trading_agent.py  # Investment management
│   │   ├── spending_guard_agent.py # Anomaly detection
│   │   ├── budget_analyzer_agent.py # Budget analysis
│   │   ├── tax_optimizer_agent.py  # Tax optimization
│   │   └── contract_review_agent.py # Contract review
│   ├── database/
│   │   ├── mongodb_client.py       # MongoDB interface
│   │   └── embeddings.py           # Voyage AI embeddings
│   ├── models/
│   │   └── loan.py                 # Loan data models
│   ├── schemas/
│   │   ├── agent_schemas.py        # Output schemas for agents
│   │   └── validation.py           # Schema validation helpers
│   └── orchestrator.py             # Multi-agent coordinator
├── docs/
│   └── AGENT_SCHEMAS.md            # Schema documentation
├── example.py                      # Complete demo
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

### Agent Output Schemas

All agents use standardized output schemas before storing data in MongoDB. This ensures:
- ✅ Type safety and validation
- ✅ Consistent data structures across agents
- ✅ Easy cross-agent coordination
- ✅ Self-documenting code

See [docs/AGENT_SCHEMAS.md](docs/AGENT_SCHEMAS.md) for detailed schema specifications.

## 🌟 Future Enhancements

**See [ROADMAP.md](ROADMAP.md) for the comprehensive 16-week implementation plan!**

### Planned Features (In Development)

- [ ] Real-time trading API integrations (Phase 1)
- [ ] Vector database for semantic search (Phase 2)
- [ ] Quantum portfolio optimization (Phase 3)
- [ ] Reinforcement learning training pipeline (Phase 4)
- [ ] Automated payment processing
- [ ] Credit score improvement tracking
- [ ] Mobile app for borrowers
- [ ] Community lending pools
- [ ] Financial education modules

### Implementation Resources

- **[ROADMAP.md](ROADMAP.md)** - Comprehensive 16-week implementation plan
- **[BUILD_PLAN.md](BUILD_PLAN.md)** - Sprint 1-2 detailed tasks and sub-issues
- **[QUICKSTART.md](QUICKSTART.md)** - Quick reference guide for developers
- **[TESTING.md](TESTING.md)** - Testing strategy and guidelines

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## 📞 Support

- GitHub Issues: Report bugs or request features
- Documentation: Full API docs at docs/
- Community: Join our Discord server

---

**AlphaShield**: Eliminating the poverty tax, one loan at a time. 💰🛡️