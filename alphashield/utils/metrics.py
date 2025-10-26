from __future__ import annotations

import contextlib
import time
from typing import Iterator, Optional

# Optional Prometheus import
try:
    from prometheus_client import Gauge, Counter
    _PROM = True
except Exception:
    Gauge = object  # type: ignore
    Counter = object  # type: ignore
    _PROM = False


_duration_gauge = None
_cov_breach_counter = None
_dd_breach_counter = None
_decisions_counter = None


def _ensure_metrics():
    global _duration_gauge, _cov_breach_counter, _dd_breach_counter, _decisions_counter
    if _PROM and _duration_gauge is None:
        _duration_gauge = Gauge("alphashield_duration_ms", "Duration in ms", labelnames=["component"])  # type: ignore
        _cov_breach_counter = Counter("alphashield_coverage_breach_total", "Coverage breaches")  # type: ignore
        _dd_breach_counter = Counter("alphashield_drawdown_breach_total", "Drawdown breaches")  # type: ignore
        _decisions_counter = Counter("alphashield_decisions_total", "Decisions made", labelnames=["template"])  # type: ignore


@contextlib.contextmanager
def time_block(component: str) -> Iterator[float]:
    _ensure_metrics()
    t0 = time.perf_counter()
    try:
        yield 0.0
    finally:
        dt_ms = (time.perf_counter() - t0) * 1000.0
        if _PROM:
            _duration_gauge.labels(component=component).set(dt_ms)  # type: ignore


def coverage_breach_inc():
    _ensure_metrics()
    if _PROM:
        _cov_breach_counter.inc()  # type: ignore


def drawdown_breach_inc():
    _ensure_metrics()
    if _PROM:
        _dd_breach_counter.inc()  # type: ignore


def decisions_inc(template: str):
    _ensure_metrics()
    if _PROM:
        _decisions_counter.labels(template=template).inc()  # type: ignore
