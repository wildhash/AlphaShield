from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class StrategyProfile:
    name: str
    momentum_weight: float
    trend_weight: float
    mean_reversion_weight: float


DEFAULT_PROFILES: Dict[str, StrategyProfile] = {
    "low_vol": StrategyProfile("low_vol", momentum_weight=0.6, trend_weight=0.2, mean_reversion_weight=0.2),
    "balanced": StrategyProfile("balanced", momentum_weight=0.4, trend_weight=0.3, mean_reversion_weight=0.3),
    "high_vol": StrategyProfile("high_vol", momentum_weight=0.2, trend_weight=0.2, mean_reversion_weight=0.6),
}
