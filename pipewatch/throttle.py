"""Throttle detection: identify metrics whose rate of change exceeds a defined ceiling."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class ThrottleResult:
    name: str
    current_rate: float  # units per second
    ceiling: float
    throttled: bool
    ratio: float  # current_rate / ceiling
    message: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "current_rate": round(self.current_rate, 6),
            "ceiling": self.ceiling,
            "throttled": self.throttled,
            "ratio": round(self.ratio, 4),
            "message": self.message,
        }


def detect_throttle(
    name: str,
    history: MetricHistory,
    ceiling: float,
    window_seconds: float = 60.0,
) -> Optional[ThrottleResult]:
    """Compute the average rate of change over *window_seconds* and compare to *ceiling*."""
    if ceiling <= 0:
        return None

    records = history.all()
    if len(records) < 2:
        return None

    cutoff = records[-1].timestamp - window_seconds
    window = [r for r in records if r.timestamp >= cutoff]
    if len(window) < 2:
        return None

    span = window[-1].timestamp - window[0].timestamp
    if span <= 0:
        return None

    total_change = sum(
        abs(window[i].value - window[i - 1].value) for i in range(1, len(window))
    )
    rate = total_change / span
    ratio = rate / ceiling
    throttled = rate > ceiling
    message = (
        f"{name} rate {rate:.4f}/s exceeds ceiling {ceiling}/s (ratio={ratio:.2f})"
        if throttled
        else f"{name} rate {rate:.4f}/s is within ceiling {ceiling}/s (ratio={ratio:.2f})"
    )
    return ThrottleResult(
        name=name,
        current_rate=rate,
        ceiling=ceiling,
        throttled=throttled,
        ratio=ratio,
        message=message,
    )


def scan_throttles(
    metrics: List[Metric],
    history: MetricHistory,
    ceiling: float,
    window_seconds: float = 60.0,
) -> List[ThrottleResult]:
    """Run throttle detection across all supplied metrics."""
    results = []
    for m in metrics:
        r = detect_throttle(m.name, history, ceiling, window_seconds)
        if r is not None:
            results.append(r)
    return results
