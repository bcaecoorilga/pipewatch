"""Latency detection: measure and classify per-metric processing latency."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class LatencyResult:
    metric_name: str
    mean_latency: float
    max_latency: float
    min_latency: float
    p95_latency: float
    classification: str  # "low", "moderate", "high"
    sample_count: int

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "mean_latency": round(self.mean_latency, 4),
            "max_latency": round(self.max_latency, 4),
            "min_latency": round(self.min_latency, 4),
            "p95_latency": round(self.p95_latency, 4),
            "classification": self.classification,
            "sample_count": self.sample_count,
        }


def _classify(mean_latency: float, warn_threshold: float, crit_threshold: float) -> str:
    if mean_latency >= crit_threshold:
        return "high"
    if mean_latency >= warn_threshold:
        return "moderate"
    return "low"


def detect_latency(
    metric: Metric,
    history: MetricHistory,
    warn_threshold: float = 1.0,
    crit_threshold: float = 5.0,
    min_samples: int = 2,
) -> Optional[LatencyResult]:
    records = history.for_name(metric.name)
    if len(records) < min_samples:
        return None

    timestamps = sorted(r.timestamp for r in records)
    gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
    if not gaps:
        return None

    sorted_gaps = sorted(gaps)
    mean_l = sum(gaps) / len(gaps)
    p95_idx = max(0, int(len(sorted_gaps) * 0.95) - 1)

    return LatencyResult(
        metric_name=metric.name,
        mean_latency=mean_l,
        max_latency=max(gaps),
        min_latency=min(gaps),
        p95_latency=sorted_gaps[p95_idx],
        classification=_classify(mean_l, warn_threshold, crit_threshold),
        sample_count=len(gaps),
    )


def scan_latencies(
    metrics: List[Metric],
    history: MetricHistory,
    warn_threshold: float = 1.0,
    crit_threshold: float = 5.0,
    min_samples: int = 2,
) -> List[LatencyResult]:
    results = []
    for m in metrics:
        r = detect_latency(m, history, warn_threshold, crit_threshold, min_samples)
        if r is not None:
            results.append(r)
    return results
