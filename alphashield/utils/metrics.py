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
    """
    Lazily initialize the module-level Prometheus metrics used by this module.
    
    If Prometheus is available and the metrics are not yet created, this function sets the globals
    `_duration_gauge`, `_cov_breach_counter`, `_dd_breach_counter`, and `_decisions_counter` to
    their corresponding Gauge/Counter instances with the configured names and labels. If Prometheus
    is not available or the metrics are already initialized, the function does nothing.
    """
    global _duration_gauge, _cov_breach_counter, _dd_breach_counter, _decisions_counter
    if _PROM and _duration_gauge is None:
        _duration_gauge = Gauge("alphashield_duration_ms", "Duration in ms", labelnames=["component"])  # type: ignore
        _cov_breach_counter = Counter("alphashield_coverage_breach_total", "Coverage breaches")  # type: ignore
        _dd_breach_counter = Counter("alphashield_drawdown_breach_total", "Drawdown breaches")  # type: ignore
        _decisions_counter = Counter("alphashield_decisions_total", "Decisions made", labelnames=["template"])  # type: ignore


@contextlib.contextmanager
def time_block(component: str) -> Iterator[float]:
    """
    Measure elapsed time for a named component and record it to Prometheus when available.
    
    When used as a context manager, this yields a placeholder float to the block and, on exit,
    records the elapsed time in milliseconds to the `alphashield_duration_ms` gauge labeled
    with the provided component if Prometheus is enabled.
    
    Parameters:
        component (str): Label value used for the `alphashield_duration_ms` gauge.
    
    Returns:
        float: A placeholder value (0.0) yielded to the with-block.
    """
    _ensure_metrics()
    t0 = time.perf_counter()
    try:
        yield 0.0
    finally:
        dt_ms = (time.perf_counter() - t0) * 1000.0
        if _PROM:
            _duration_gauge.labels(component=component).set(dt_ms)  # type: ignore


def coverage_breach_inc():
    """
    Increment the coverage breach counter metric.
    
    If Prometheus is available, increments the internal coverage breach counter (alphashield_coverage_breach_total); otherwise this function is a no-op.
    """
    _ensure_metrics()
    if _PROM:
        _cov_breach_counter.inc()  # type: ignore


def drawdown_breach_inc():
    """
    Increment the recorded drawdown breach metric.
    
    If the Prometheus client is available, increments the internal drawdown breach Counter; otherwise this function is a no-op.
    """
    _ensure_metrics()
    if _PROM:
        _dd_breach_counter.inc()  # type: ignore


def decisions_inc(template: str):
    """
    Increment the decisions counter for a specific template label.
    
    Parameters:
        template (str): Template identifier used as the `template` label when recording the decision metric.
    """
    _ensure_metrics()
    if _PROM:
        _decisions_counter.labels(template=template).inc()  # type: ignore