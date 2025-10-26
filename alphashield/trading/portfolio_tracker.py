from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np


@dataclass
class PortfolioTracker:
    positions: Dict[str, float] = field(default_factory=dict)
    prices: Dict[str, float] = field(default_factory=dict)
    _peak_value: float = 0.0

    def update_price(self, ticker: str, price: float) -> None:
        self.prices[ticker] = float(price)

    def get_total_value(self) -> float:
        total = 0.0
        for ticker, qty in self.positions.items():
            price = float(self.prices.get(ticker, 0.0))
            total += float(qty) * price
        self._peak_value = max(self._peak_value, total)
        return total

    def get_drawdown(self) -> float:
        total = self.get_total_value()
        if self._peak_value <= 0:
            return 0.0
        return (self._peak_value - total) / self._peak_value

    def get_weights(self) -> Dict[str, float]:
        total = self.get_total_value()
        if total <= 0:
            return {t: 0.0 for t in self.positions}
        return {t: (self.prices.get(t, 0.0) * q) / total for t, q in self.positions.items()}
