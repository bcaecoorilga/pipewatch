"""Burndown detection: tracks how quickly a metric is decreasing toward a target."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class BurndownResult:
    metric_name: str
    current_value: float
    target: float
    initial_value: float
    rate_per_second: float          # negative means burning down
    eta_seconds: Optional[float]    # None if not converging
    percent_remaining: float
    on_track: bool

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "target": self.target,
            "initial_value": self.initial_value,
            "rate_per_second": self.rate_per_second,
            "eta_seconds": self.eta_seconds,
            "percent_remaining": self.percent_remaining,
            "on_track": self.on_track,
        }


def detect_burndown(
    metric: Metric,
    history: MetricHistory,
    target: float,
    deadline_seconds: Optional[float] = None,
) -> Optional[BurndownResult]:
    """Detect burndown progress for a metric toward a target value."""
    records: List = history.for_name(metric.name)
    if len(records) < 2:
        return None

    records = sorted(records, key=lambda r: r.timestamp)
    first = records[0]
    last = records[-1]

    time_delta = (last.timestamp - first.timestamp).total_seconds()
    if time_delta <= 0:
        return None

    value_delta = last.metric.value - first.metric.value
    rate_per_second = value_delta / time_delta

    gap = last.metric.value - target
    total_gap = first.metric.value - target
    percent_remaining = (gap / total_gap * 100.0) if total_gap != 0 else 0.0

    eta_seconds: Optional[float] = None
    if rate_per_second < 0 and gap > 0:
        eta_seconds = gap / abs(rate_per_second)
    elif rate_per_second > 0 and gap < 0:
        eta_seconds = abs(gap) / rate_per_second

    on_track = False
    if eta_seconds is not None and deadline_seconds is not None:
        on_track = eta_seconds <= deadline_seconds
    elif eta_seconds is not None:
        on_track = True

    return BurndownResult(
        metric_name=metric.name,
        current_value=last.metric.value,
        target=target,
        initial_value=first.metric.value,
        rate_per_second=rate_per_second,
        eta_seconds=eta_seconds,
        percent_remaining=max(0.0, percent_remaining),
        on_track=on_track,
    )


def scan_burndowns(
    metrics: List[Metric],
    history: MetricHistory,
    targets: dict,
    deadline_seconds: Optional[float] = None,
) -> List[BurndownResult]:
    """Scan multiple metrics for burndown progress. `targets` maps metric name -> target value."""
    results = []
    for metric in metrics:
        target = targets.get(metric.name)
        if target is None:
            continue
        result = detect_burndown(metric, history, target, deadline_seconds)
        if result is not None:
            results.append(result)
    return results
