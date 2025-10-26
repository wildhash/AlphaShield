from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CoverageRatioMonitor:
    target_min: float = 1.3
    emergency_min: float = 1.2

    def status(self, coverage_ratio: float) -> str:
        if coverage_ratio < self.emergency_min:
            return "emergency"
        if coverage_ratio < self.target_min:
            return "defensive"
        return "normal"
