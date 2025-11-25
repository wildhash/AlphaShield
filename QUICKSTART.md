# AlphaShield Implementation Quick Start

This guide helps you get started with implementing the AlphaShield roadmap.

## 📋 Prerequisites

- Python 3.11+
- MongoDB Atlas account
- Git and GitHub access
- Development environment (VS Code recommended)

## 🚀 Getting Started

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/wildhash/AlphaShield.git
cd AlphaShield

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 2. Environment Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Database
MONGODB_URI=mongodb+srv://your-cluster.mongodb.net/alphashield
VOYAGE_API_KEY=pa-your-voyage-api-key

# Trading (for Q1 milestones)
ALPACA_API_KEY=your-alpaca-key
ALPACA_SECRET_KEY=your-alpaca-secret
ALPACA_PAPER=true

# Vector DB (for Q1 milestones)
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=your-environment

# Quantum (optional, for Q1 milestones)
DWAVE_API_TOKEN=your-dwave-token
QUANTUM_ENABLED=false

# Monitoring (for Q3 milestones)
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_PORT=9090
```

### 3. Verify Setup

Run the test suite to ensure everything is working:

```bash
pytest tests/ -v
```

### 4. Create Your Feature Branch

```bash
# For Trading Engine work
git checkout -b feature/trading-engine-week1

# For Vector DB work
git checkout -b feature/vector-db-integration

# etc.
```

## 📚 Project Structure Overview

```
AlphaShield/
├── alphashield/          # Core package
│   ├── agents/          # 6 AI agents
│   ├── database/        # MongoDB & embeddings
│   ├── orchestrator/    # Multi-agent coordination
│   ├── rl/             # Reinforcement learning
│   └── context/        # Shared context system
├── trading_core/        # Trading engine (Q1 work here)
│   ├── api/            # Broker integrations (NEW)
│   ├── execution/      # Order management (NEW)
│   ├── portfolio/      # Portfolio optimization
│   ├── signals/        # Trading signals
│   └── risk/           # Risk management
├── backtest/           # Backtesting framework
├── tests/              # Test suite
├── docs/               # Documentation
└── examples/           # Usage examples
```

## 🎯 Current Sprint: Q1 Week 1-2 (Broker Integration)

### Your Tasks This Week

Check the [GITHUB_ISSUES.md](GITHUB_ISSUES.md) for detailed task breakdown.

**Week 1 Priority Tasks:**
1. Issue #1.1: Design Unified Broker Interface (2 days)
2. Issue #1.2: Implement Alpaca Integration (3 days)
3. Issue #1.3: Implement IBKR Integration (3 days)

**Week 2 Priority Tasks:**
4. Issue #1.4: Broker Factory & Documentation (1 day)
5. Issue #1.5: Order Management System (3 days)

### Development Workflow

1. **Pick an Issue**
   - Go to GitHub Projects board
   - Assign yourself to an issue
   - Move it to "In Progress"

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/issue-number-short-description
   ```

3. **Implement**
   - Write code following the acceptance criteria
   - Add type hints and docstrings
   - Follow Black/Ruff style guide

4. **Test**
   ```bash
   # Run tests
   pytest tests/trading/ -v
   
   # Check coverage
   pytest tests/trading/ --cov=trading_core --cov-report=html
   
   # Format code
   black .
   ruff check . --fix
   ```

5. **Create Pull Request**
   - Use the PR template
   - Reference the issue number
   - Request review

6. **Merge & Close**
   - After approval, merge PR
   - Close the issue
   - Move to "Done" on board

## 🔧 Key Services Setup

### MongoDB Atlas
1. Create free cluster at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create database user
3. Whitelist your IP (or use 0.0.0.0/0 for development)
4. Get connection string and add to `.env`

### Voyage AI
1. Sign up at [voyageai.com](https://www.voyageai.com/)
2. Get API key
3. Add to `.env`

### Alpaca (Paper Trading)
1. Sign up at [alpaca.markets](https://alpaca.markets/)
2. Create paper trading account (free)
3. Get API key and secret
4. Add to `.env`

### Pinecone (Vector DB)
1. Sign up at [pinecone.io](https://www.pinecone.io/)
2. Create free index
3. Get API key
4. Add to `.env`

### D-Wave (Quantum - Optional)
1. Sign up at [cloud.dwavesys.com](https://cloud.dwavesys.com/)
2. Get 1 minute/month free tier
3. Get API token
4. Add to `.env`

## 📝 Coding Standards

### Style Guide
- **Formatter:** Black (line length: 100)
- **Linter:** Ruff
- **Type Checking:** MyPy
- **Docstrings:** Google style

```python
def example_function(param1: str, param2: int) -> Dict[str, Any]:
    """Brief description of function.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something is wrong
    """
    pass
```

### Testing
- **Target:** >90% coverage
- **Unit Tests:** Test individual functions/classes
- **Integration Tests:** Test component interactions
- **Naming:** `test_<what>_<when>_<expected>`

```python
def test_alpaca_broker_places_order_successfully():
    """Test that AlpacaBroker can place a market order."""
    broker = AlpacaBroker(api_key="test", secret="test", paper=True)
    order = broker.place_order("AAPL", qty=10, side="buy", order_type="market")
    assert order.status == "submitted"
```

### Git Commit Messages
Follow conventional commits:

```
type(scope): brief description

Longer description if needed

Closes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(trading): add Alpaca broker integration

Implements AlpacaBroker class with order placement,
position tracking, and error handling.

Closes #1.2
```

## 🐛 Debugging Tips

### Run Single Test
```bash
pytest tests/trading/test_alpaca_broker.py::test_place_order -v
```

### Debug with pdb
```python
import pdb; pdb.set_trace()
```

### Check Logs
```bash
tail -f logs/alphashield.log
```

### MongoDB Data Inspection
```python
from alphashield.database.mongodb_client import get_mongo_client

client = get_mongo_client()
loans = client.get_collection('loans')
print(list(loans.find().limit(5)))
```

## 📊 Progress Tracking

### Daily
- Update issue status on GitHub
- Commit code frequently
- Update PR with progress

### Weekly
- Monday: Sprint planning
- Wednesday: Mid-week check-in
- Friday: Demo & retrospective

### Report Blockers
If you're blocked:
1. Comment on the issue
2. Mention @wildhash
3. Post in #alphashield-dev Slack

## 🆘 Getting Help

### Resources
- **Roadmap:** [ROADMAP.md](ROADMAP.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **API Docs:** `docs/api/`
- **Examples:** `examples/`

### Communication
- **Slack:** #alphashield-dev (technical), #alphashield-general (updates)
- **GitHub Issues:** For bugs and features
- **PR Comments:** For code review discussions

### Key Contacts
- **@wildhash:** Project lead, technical questions
- **Team:** Check ROADMAP.md for milestone owners

## ✅ Checklist for First PR

Before submitting your first PR, ensure:

- [ ] Code follows style guide (Black + Ruff)
- [ ] Type hints added
- [ ] Docstrings complete
- [ ] Unit tests added
- [ ] Tests passing locally
- [ ] Documentation updated
- [ ] PR template filled out
- [ ] Issue linked

## 🎉 Next Steps

1. **Read the Roadmap:** [ROADMAP.md](ROADMAP.md)
2. **Pick Your First Issue:** [GITHUB_ISSUES.md](GITHUB_ISSUES.md)
3. **Join Team Meeting:** Monday 10am
4. **Start Coding!** 🚀

---

**Welcome to AlphaShield! Let's build something amazing together.**

For questions: @wildhash or #alphashield-dev
