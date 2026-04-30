"""Breach detection: track consecutive threshold violations for a metric."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus, MetricThreshold


@dataclass
class BreachResult:
    name: str
    consecutive_breaches: int
    min_breaches: int
    threshold: float
    level: str  # "warning" or "critical"
    is_breaching: bool
    recent_values: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "consecutive_breaches": self.consecutive_breaches,
            "min_breaches": self.min_breaches,
            "threshold": self.threshold,
            "level": self.level,
            "is_breaching": self.is_breaching,
            "recent_values": self.recent_values,
        }


def detect_breach(
    name: str,
    history: MetricHistory,
    threshold: MetricThreshold,
    min_breaches: int = 3,
    window: int = 10,
) -> Optional[BreachResult]:
    """Detect if a metric has breached a threshold for at least *min_breaches*
    consecutive records within the last *window* records."""
    if min_breaches < 1:
        raise ValueError("min_breaches must be >= 1")

    records = history.for_name(name)
    if not records:
        return None

    recent = records[-window:]
    if len(recent) < min_breaches:
        return None

    # Determine which level fires first (critical takes priority)
    for level, limit in (("critical", threshold.critical), ("warning", threshold.warning)):
        if limit is None:
            continue
        consecutive = 0
        for rec in reversed(recent):
            if rec.value >= limit:
                consecutive += 1
            else:
                break
        if consecutive >= min_breaches:
            return BreachResult(
                name=name,
                consecutive_breaches=consecutive,
                min_breaches=min_breaches,
                threshold=limit,
                level=level,
                is_breaching=True,
                recent_values=[r.value for r in recent],
            )

    return BreachResult(
        name=name,
        consecutive_breaches=0,
        min_breaches=min_breaches,
        threshold=threshold.warning or threshold.critical or 0.0,
        level="warning",
        is_breaching=False,
        recent_values=[r.value for r in recent],
    )


def scan_breaches(
    names: List[str],
    history: MetricHistory,
    threshold: MetricThreshold,
    min_breaches: int = 3,
    window: int = 10,
) -> List[BreachResult]:
    """Run breach detection across multiple metric names."""
    results = []
    for name in names:
        result = detect_breach(name, history, threshold, min_breaches, window)
        if result is not None:
            results.append(result)
    return results
