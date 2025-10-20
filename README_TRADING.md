# AlphaShield Trading Core (v1)

This module adds a **loan-aware, no-blow-up** trading skeleton:
- Coverage Ratio gating (CR floor)
- Risk guardrails (pos caps, min cash, turnover budget)
- Classical QP allocator (CVXPY) with shrinkage + L1 turnover penalty
- Simple signals (trend + mean-reversion) with regime-aware mix
- Minimal event-driven backtest with costs

## Quick Start

```bash
pip install -U numpy pandas cvxpy scipy pytest pyyaml
pytest -q
```

## Backtest (example)

Create a small CSV of daily prices (columns = symbols) or use your loader, then:

```python
import pandas as pd
from backtest.engine import BacktestEngine
from finance.coverage import LoanTerms

prices = pd.read_csv("prices.csv", parse_dates=[0], index_col=0)
terms = LoanTerms(principal=10000, annual_rate=0.12, months=36)
bt = BacktestEngine(data=prices, loan_terms=terms, initial_nav=5000.0)
report = bt.run()
print("Final NAV:", report["final_nav"])
```

## Next Steps

* Swap CVXPY for GPU-QP (qpth) behind a flag
* Add Alpaca/Coinbase adapters
* Add VaR/ES checks to risk loop
* Add CR and DD plots to the report
