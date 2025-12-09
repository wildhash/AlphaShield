# AlphaShield Quick Reference Guide

## 🎯 Key Features

- **Live Trading**: Alpaca Markets integration for paper and live trading
- **Automated RL Training**: Nightly policy optimization for all 6 agents
- **Real-time Monitoring**: Streamlit dashboard for training metrics
- **Production Ready**: CI/CD, testing, and deployment automation

---

## 🚀 Quick Commands

### Installation
```bash
git clone https://github.com/wildhash/AlphaShield.git
cd AlphaShield
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Testing
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=alphashield --cov-report=html

# Integration only
pytest tests/integration/ -v

# Specific test
pytest tests/trading/test_broker_adapters.py -v
```

### Trading
```python
# Paper trading setup
from alphashield.trading.broker_adapters import AlpacaAdapter
from alphashield.trading.execution_engine import ExecutionEngine

broker = AlpacaAdapter(paper=True)
engine = ExecutionEngine(broker=broker)

# Execute rebalance
confirmations = engine.execute_rebalance(
    target_weights={"SPY": 0.5, "AGG": 0.5}
)
```

### RL Training
```bash
# Manual training run
python jobs/train_nightly.py

# Dry run (no deployment)
python jobs/train_nightly.py --dry-run

# Custom window
python jobs/train_nightly.py --window-days 90

# Specific agents
python jobs/train_nightly.py --agents Lender,AlphaTrading
```

### Dashboard
```bash
# Launch training dashboard
streamlit run dashboard/rl_training_dashboard.py

# Visit http://localhost:8501
```

---

## 📁 Important Files

### Core Trading
- `alphashield/trading/broker_adapters/` - Broker integrations
- `alphashield/trading/execution_engine.py` - Order execution
- `alphashield/trading/portfolio_optimizer.py` - Portfolio optimization

### RL & Agents
- `alphashield/agents/` - All 6 AI agents
- `alphashield/rl/` - RL infrastructure
- `alphashield/orchestrator/` - Agent coordination
- `jobs/train_nightly.py` - Training pipeline

### Configuration
- `.env` - Environment variables (API keys)
- `config/trading.yaml` - Trading settings
- `config/rl.yaml` - RL hyperparameters

### Documentation
- `docs/PRODUCTION_DEPLOYMENT.md` - Full deployment guide
- `docs/ARCHITECTURE.md` - System architecture
- `alphashield/trading/broker_adapters/README.md` - Broker usage
- `IMPLEMENTATION_COMPLETE.md` - This sprint summary

---

## 🔑 Environment Variables

```bash
# MongoDB
MONGODB_URI=mongodb+srv://...

# Alpaca Trading
ALPACA_API_KEY=PK...
ALPACA_SECRET_KEY=...
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# AI Services
VOYAGE_API_KEY=pa-...
OPENAI_API_KEY=sk-...

# Optional
DWAVE_API_TOKEN=...  # Quantum optimization
```

---

## 🎛️ Broker Adapters

### Alpaca (Live/Paper)
```python
from alphashield.trading.broker_adapters import AlpacaAdapter, OrderSide, OrderType

# Paper trading
broker = AlpacaAdapter(paper=True)

# Get account
account = broker.get_account()
print(f"Cash: ${account.cash:,.2f}")

# Submit order
order = broker.submit_order(
    ticker="AAPL",
    qty=100,
    side=OrderSide.BUY,
    type=OrderType.LIMIT,
    limit_price=150.50
)

# Check status
status = broker.get_order(order.id)
```

### Paper Simulator
```python
from alphashield.trading.broker_adapters import PaperTradingAdapter

broker = PaperTradingAdapter(initial_cash=100_000)
broker.set_prices({"AAPL": 150.0, "GOOGL": 2800.0})

order = broker.submit_order("AAPL", 100, OrderSide.BUY, OrderType.MARKET)
```

---

## 🧪 Testing Checklist

- [ ] Unit tests pass: `pytest tests/test_*.py`
- [ ] Integration tests pass: `pytest tests/integration/`
- [ ] Coverage above 70%: `pytest --cov`
- [ ] Linting passes: `ruff check .`
- [ ] Type checking: `mypy alphashield/`
- [ ] Paper trading tested for 2+ weeks
- [ ] RL training runs nightly without errors
- [ ] Dashboard accessible and showing data

---

## 📊 Monitoring

### Logs
```bash
tail -f logs/alphashield.log
tail -f logs/trading.log
tail -f logs/training_*.log
```

### Metrics (Prometheus)
- `http://localhost:9090/metrics`
- Key metrics: `alphashield_trades_total`, `alphashield_pnl_total`

### Dashboard
- Training: `http://localhost:8501`
- Grafana: `http://localhost:3000`

---

## 🆘 Troubleshooting

### Cannot connect to MongoDB
```bash
# Test connection
mongosh "$MONGODB_URI"

# Check IP whitelist in Atlas
# Verify firewall rules
```

### Alpaca authentication failed
```bash
# Verify keys
echo $ALPACA_API_KEY
echo $ALPACA_SECRET_KEY

# Test API
curl -H "APCA-API-KEY-ID: $ALPACA_API_KEY" \
     -H "APCA-API-SECRET-KEY: $ALPACA_SECRET_KEY" \
     https://paper-api.alpaca.markets/v2/account
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.11+
```

### Tests failing
```bash
# Update test dependencies
pip install -r requirements-dev.txt

# Run with verbose output
pytest -vv --tb=long

# Run specific test
pytest tests/path/to/test.py::test_name -vv
```

---

## 📋 Deployment Checklist

### Pre-Production
- [ ] All tests passing
- [ ] Code review completed
- [ ] API keys in secret manager
- [ ] MongoDB backups configured
- [ ] Monitoring alerts set up
- [ ] Documentation updated

### Production
- [ ] Deploy to staging first
- [ ] Run smoke tests
- [ ] Monitor for 24 hours
- [ ] Start with paper trading
- [ ] Gradually increase capital
- [ ] Monitor logs and metrics

---

## 🔗 Useful Links

- **GitHub**: https://github.com/wildhash/AlphaShield
- **Issues**: https://github.com/wildhash/AlphaShield/issues
- **Alpaca Docs**: https://alpaca.markets/docs/
- **MongoDB Atlas**: https://www.mongodb.com/cloud/atlas

---

## 📞 Support

For issues or questions:
1. Check documentation in `/docs`
2. Search existing GitHub issues
3. Create new issue with logs and context
4. Email: support@alphashield.ai (placeholder)

---

*Last updated: 2024-12-09*
