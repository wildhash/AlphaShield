# Broker Adapters

Production-ready broker API adapters for live trading integration.

## Overview

The broker adapter system provides a unified interface for executing trades across different brokers and trading environments. This enables AlphaShield to support multiple brokers with minimal code changes.

## Supported Brokers

### 1. Alpaca Markets (`AlpacaAdapter`)

Full-featured integration with Alpaca Markets API for US equities trading.

**Features:**
- Paper trading and live trading modes
- Real-time quotes and market data
- Order management (market, limit, stop, stop-limit)
- Position tracking and portfolio monitoring
- Account information access

**Setup:**

```bash
pip install alpaca-py
```

```python
from alphashield.trading.broker_adapters import AlpacaAdapter

# Paper trading (recommended for testing)
broker = AlpacaAdapter(
    api_key="YOUR_API_KEY",
    secret_key="YOUR_SECRET_KEY",
    paper=True
)

# Live trading (use with caution!)
broker = AlpacaAdapter(
    api_key="YOUR_API_KEY",
    secret_key="YOUR_SECRET_KEY",
    paper=False
)
```

Or use environment variables:

```bash
export ALPACA_API_KEY="PK..."
export ALPACA_SECRET_KEY="..."
export ALPACA_BASE_URL="https://paper-api.alpaca.markets"
```

```python
broker = AlpacaAdapter()  # Reads from environment
```

### 2. Paper Trading (`PaperTradingAdapter`)

Simulation environment for testing strategies without real money.

**Features:**
- Zero-cost testing and development
- Configurable slippage and fill rates
- Instant order execution
- Portfolio tracking and P&L calculation

**Setup:**

```python
from alphashield.trading.broker_adapters import PaperTradingAdapter

broker = PaperTradingAdapter(
    initial_cash=100_000.0,
    slippage_bps=10.0,  # 10 basis points
    fill_probability=1.0  # 100% fill rate
)

# Set prices for simulation
broker.set_prices({
    "AAPL": 150.0,
    "GOOGL": 2800.0,
    "MSFT": 370.0,
})
```

## Common Interface

All adapters implement the `BrokerAdapter` interface:

```python
from alphashield.trading.broker_adapters import OrderSide, OrderType

# Submit an order
order = broker.submit_order(
    ticker="AAPL",
    qty=100,
    side=OrderSide.BUY,
    type=OrderType.LIMIT,
    limit_price=150.50
)

# Check order status
status = broker.get_order(order.id)
print(f"Order {order.id}: {status.status}")

# Get account info
account = broker.get_account()
print(f"Portfolio value: ${account.portfolio_value:,.2f}")
print(f"Cash: ${account.cash:,.2f}")

# Get positions
positions = broker.get_positions()
for pos in positions:
    print(f"{pos.ticker}: {pos.quantity} shares @ ${pos.current_price:.2f}")

# Close a position
close_order = broker.close_position("AAPL")
print(f"Closed position: {close_order.id}")
```

## Integration with Execution Engine

The execution engine uses broker adapters for portfolio rebalancing:

```python
from alphashield.trading.execution_engine import ExecutionEngine
from alphashield.trading.broker_adapters import AlpacaAdapter

# Initialize with broker
broker = AlpacaAdapter(paper=True)
engine = ExecutionEngine(broker=broker)

# Execute rebalance
target_weights = {
    "SPY": 0.40,   # 40% S&P 500
    "QQQ": 0.30,   # 30% Nasdaq
    "IWM": 0.20,   # 20% Russell 2000
    "AGG": 0.10,   # 10% Bonds
}

confirmations = engine.execute_rebalance(
    target_weights=target_weights
)

# Monitor order execution
order_ids = [conf["order_id"] for conf in confirmations.values() if "order_id" in conf]
statuses = engine.monitor_orders(order_ids, timeout_seconds=60)

for order_id, status in statuses.items():
    print(f"Order {order_id}: {status['status']}")
```

## Error Handling

All adapters handle errors gracefully and return error information:

```python
order = broker.submit_order(
    ticker="AAPL",
    qty=1000000,  # Insufficient funds
    side=OrderSide.BUY,
    type=OrderType.MARKET
)

if order.status == OrderStatus.REJECTED:
    print(f"Order rejected: {order.error_message}")
```

## Best Practices

### 1. Always Test with Paper Trading First

```python
# Test strategy thoroughly in paper trading
paper_broker = PaperTradingAdapter(initial_cash=100_000)
# ... run strategy ...

# Only after extensive testing, switch to live
# live_broker = AlpacaAdapter(paper=False)
```

### 2. Implement Position Sizing and Risk Limits

```python
# Check account before large trades
account = broker.get_account()
max_position_size = account.portfolio_value * 0.10  # 10% max per position

if order_value > max_position_size:
    print("Position size exceeds risk limit")
    # Adjust or reject order
```

### 3. Monitor Order Execution

```python
# Don't assume orders fill immediately
order = broker.submit_order(...)

# Poll for status
import time
for _ in range(10):
    status = broker.get_order(order.id)
    if status.status in [OrderStatus.FILLED, OrderStatus.REJECTED]:
        break
    time.sleep(1)
```

### 4. Handle Partial Fills

```python
order = broker.get_order(order_id)

if order.status == OrderStatus.PARTIALLY_FILLED:
    print(f"Filled {order.filled_quantity}/{order.quantity} shares")
    
    # Decide: wait for full fill or cancel remaining?
    if order.filled_quantity / order.quantity > 0.8:
        broker.cancel_order(order_id)
```

### 5. Use Limit Orders for Large Trades

```python
# For large trades, use limit orders to control slippage
quote = broker.get_quote("AAPL")

# Set limit price 0.1% above midpoint for buys
limit_price = quote["last"] * 1.001

order = broker.submit_order(
    ticker="AAPL",
    qty=1000,
    side=OrderSide.BUY,
    type=OrderType.LIMIT,
    limit_price=limit_price
)
```

## Testing

Run the broker adapter tests:

```bash
pytest tests/trading/test_broker_adapters.py -v
```

## Adding New Brokers

To add support for a new broker:

1. Create adapter class inheriting from `BrokerAdapter`
2. Implement all required methods
3. Add tests
4. Update this documentation

Example structure:

```python
from alphashield.trading.broker_adapters.base import BrokerAdapter

class InteractiveBrokersAdapter(BrokerAdapter):
    def __init__(self, host="127.0.0.1", port=7497):
        # Initialize IB client
        pass
    
    def submit_order(self, ticker, qty, side, type, **kwargs):
        # Implement order submission
        pass
    
    # ... implement other methods ...
```

## Troubleshooting

### Alpaca Authentication Failed

```
Error: Alpaca API credentials required
```

**Solution**: Set environment variables:
```bash
export ALPACA_API_KEY="your_key"
export ALPACA_SECRET_KEY="your_secret"
```

### Order Rejected: Insufficient Buying Power

```
Error: Insufficient funds (need $15,000, have $10,000)
```

**Solution**: Check account cash before submitting orders:
```python
account = broker.get_account()
print(f"Available cash: ${account.cash:,.2f}")
```

### Connection Timeout

```
Error: Request timed out
```

**Solution**: Check network connectivity and API status:
- Alpaca status: https://status.alpaca.markets/
- Verify firewall rules allow outbound connections

## Security Notes

- **Never commit API keys** to version control
- Use environment variables or secret managers
- Rotate keys regularly (every 90 days)
- Use read-only keys for monitoring, separate keys for trading
- Enable IP whitelisting when available
- Start with paper trading, move to live only when confident

## Performance Considerations

- **Rate Limits**: Alpaca has rate limits (200 req/min for free tier)
- **Quote Delays**: Free market data may be delayed 15 minutes
- **Batch Orders**: Submit multiple orders together when possible
- **Connection Pooling**: Reuse adapter instances to avoid reconnection overhead

## Support

- Alpaca API Docs: https://alpaca.markets/docs/
- AlphaShield Issues: https://github.com/wildhash/AlphaShield/issues
