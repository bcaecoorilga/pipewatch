"""Replay historical metric records through thresholds and collect results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.metrics import Metric, MetricStatus, MetricThreshold, evaluate
from pipewatch.history import MetricHistory


@dataclass
class ReplayEvent:
    """A single replayed metric evaluation."""
    metric: Metric
    status: MetricStatus
    threshold_warn: Optional[float]
    threshold_crit: Optional[float]

    def to_dict(self) -> dict:
        return {
            "name": self.metric.name,
            "value": self.metric.value,
            "timestamp": self.metric.timestamp,
            "status": self.status.value,
            "threshold_warn": self.threshold_warn,
            "threshold_crit": self.threshold_crit,
        }


@dataclass
class ReplayResult:
    """Aggregated result of a replay run."""
    name: str
    events: List[ReplayEvent] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.events)

    @property
    def status_counts(self) -> dict:
        counts: dict = {s.value: 0 for s in MetricStatus}
        for ev in self.events:
            counts[ev.status.value] += 1
        return counts

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "total": self.total,
            "status_counts": self.status_counts,
            "events": [e.to_dict() for e in self.events],
        }


def replay(
    history: MetricHistory,
    name: str,
    warn: Optional[float] = None,
    crit: Optional[float] = None,
    since: Optional[float] = None,
) -> ReplayResult:
    """Replay historical records for *name* against optional thresholds."""
    records = history.for_name(name)
    if since is not None:
        records = [r for r in records if r.timestamp >= since]

    threshold: Optional[MetricThreshold] = None
    if warn is not None or crit is not None:
        threshold = MetricThreshold(name=name, warn=warn, crit=crit)

    result = ReplayResult(name=name)
    for metric in records:
        status = evaluate(metric, threshold) if threshold else MetricStatus.OK
        result.events.append(
            ReplayEvent(
                metric=metric,
                status=status,
                threshold_warn=warn,
                threshold_crit=crit,
            )
        )
    return result
