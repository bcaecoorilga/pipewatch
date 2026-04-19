"""Metric aggregation utilities for summarizing metric collections."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pipewatch.metrics import Metric, MetricStatus


@dataclass
class AggregateResult:
    name: str
    count: int
    mean: float
    min: float
    max: float
    latest: float
    status_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "mean": round(self.mean, 4),
            "min": self.min,
            "max": self.max,
            "latest": self.latest,
            "status_counts": self.status_counts,
        }


def aggregate(metrics: List[Metric]) -> Optional[AggregateResult]:
    """Aggregate a list of metrics with the same name."""
    if not metrics:
        return None

    values = [m.value for m in metrics]
    status_counts: Dict[str, int] = {}
    for m in metrics:
        key = m.status.value if m.status else "unknown"
        status_counts[key] = status_counts.get(key, 0) + 1

    return AggregateResult(
        name=metrics[0].name,
        count=len(values),
        mean=sum(values) / len(values),
        min=min(values),
        max=max(values),
        latest=values[-1],
        status_counts=status_counts,
    )


def aggregate_by_name(metrics: List[Metric]) -> Dict[str, AggregateResult]:
    """Group metrics by name and aggregate each group."""
    groups: Dict[str, List[Metric]] = {}
    for m in metrics:
        groups.setdefault(m.name, []).append(m)
    return {name: aggregate(group) for name, group in groups.items()}
