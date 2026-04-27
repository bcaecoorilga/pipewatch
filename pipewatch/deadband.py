"""Deadband detection: suppress changes smaller than a configured threshold."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class DeadbandResult:
    metric_name: str
    current_value: float
    previous_value: float
    delta: float
    deadband: float
    within_deadband: bool
    percent_change: Optional[float]

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "delta": self.delta,
            "deadband": self.deadband,
            "within_deadband": self.within_deadband,
            "percent_change": self.percent_change,
        }


def detect_deadband(
    metric: Metric,
    history: MetricHistory,
    deadband: float,
    min_records: int = 2,
) -> Optional[DeadbandResult]:
    """Return a DeadbandResult if there are enough records, else None."""
    if deadband <= 0:
        return None

    records = history.for_name(metric.name)
    if len(records) < min_records:
        return None

    current = records[-1].value
    previous = records[-2].value
    delta = abs(current - previous)
    within = delta <= deadband

    percent_change: Optional[float] = None
    if previous != 0:
        percent_change = round((current - previous) / abs(previous) * 100, 4)

    return DeadbandResult(
        metric_name=metric.name,
        current_value=current,
        previous_value=previous,
        delta=round(delta, 6),
        deadband=deadband,
        within_deadband=within,
        percent_change=percent_change,
    )


def scan_deadbands(
    metrics: List[Metric],
    history: MetricHistory,
    deadband: float,
) -> List[DeadbandResult]:
    """Scan all metrics and return deadband results for those with enough history."""
    results = []
    for metric in metrics:
        result = detect_deadband(metric, history, deadband)
        if result is not None:
            results.append(result)
    return results
