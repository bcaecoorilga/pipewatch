"""Pipeline summary: aggregates health, anomalies, and trend signals into a single overview."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.pipeline_health import HealthScore, compute_health
from pipewatch.anomaly import AnomalyResult, scan_anomalies
from pipewatch.trend import TrendResult, analyze
from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory


@dataclass
class PipelineSummary:
    health: Optional[HealthScore]
    anomalies: List[AnomalyResult] = field(default_factory=list)
    trends: dict = field(default_factory=dict)  # metric_name -> TrendResult

    def to_dict(self) -> dict:
        return {
            "health": self.health.to_dict() if self.health else None,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "trends": {
                name: tr.to_dict() for name, tr in self.trends.items() if tr is not None
            },
        }

    @property
    def has_anomalies(self) -> bool:
        return any(a.is_anomaly for a in self.anomalies)

    @property
    def anomaly_count(self) -> int:
        return sum(1 for a in self.anomalies if a.is_anomaly)


def build_summary(
    collector: MetricCollector,
    history: MetricHistory,
    z_threshold: float = 2.5,
) -> PipelineSummary:
    """Build a full pipeline summary from a collector and history store."""
    metrics = list(collector.all())

    health = compute_health(metrics)
    anomalies = scan_anomalies(history, z_threshold=z_threshold)

    trends: dict = {}
    for metric in metrics:
        records = history.for_name(metric.name)
        result = analyze(records)
        if result is not None:
            trends[metric.name] = result

    return PipelineSummary(health=health, anomalies=anomalies, trends=trends)
