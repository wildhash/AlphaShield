from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Asset:
    ticker: str
    sector: str | None = None


DEFAULT_UNIVERSE: List[Asset] = [
    Asset("SPY", sector="Equity"),
    Asset("QQQ", sector="Equity"),
    Asset("IWM", sector="Equity"),
    Asset("EFA", sector="Equity"),
    Asset("EEM", sector="Equity"),
    Asset("TLT", sector="Bond"),
    Asset("IEF", sector="Bond"),
    Asset("LQD", sector="Bond"),
    Asset("HYG", sector="Bond"),
    Asset("GLD", sector="Commodity"),
    Asset("AGG", sector="Bond"),
    Asset("SHY", sector="Bond"),
]
