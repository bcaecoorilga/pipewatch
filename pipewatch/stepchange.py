"""Step-change detection: identifies sudden, sustained shifts in metric values."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class StepChangeResult:
    metric_name: str
    detected: bool
    pre_mean: float
    post_mean: float
    shift_magnitude: float
    shift_pct: float
    split_index: int
    record_count: int

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "detected": self.detected,
            "pre_mean": round(self.pre_mean, 6),
            "post_mean": round(self.post_mean, 6),
            "shift_magnitude": round(self.shift_magnitude, 6),
            "shift_pct": round(self.shift_pct, 4),
            "split_index": self.split_index,
            "record_count": self.record_count,
        }


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def detect_step_change(
    metric: Metric,
    history: MetricHistory,
    min_records: int = 6,
    threshold_pct: float = 0.20,
) -> Optional[StepChangeResult]:
    """Detect a step change in *metric* using its full history.

    The history is split at the midpoint; if the relative shift between the
    two halves exceeds *threshold_pct* a step change is reported.
    """
    records = history.for_name(metric.name)
    n = len(records)
    if n < min_records:
        return None

    split = n // 2
    pre_values = [r.value for r in records[:split]]
    post_values = [r.value for r in records[split:]]

    pre_mean = _mean(pre_values)
    post_mean = _mean(post_values)

    shift = post_mean - pre_mean
    shift_pct = abs(shift) / abs(pre_mean) if pre_mean != 0.0 else 0.0
    detected = shift_pct >= threshold_pct

    return StepChangeResult(
        metric_name=metric.name,
        detected=detected,
        pre_mean=pre_mean,
        post_mean=post_mean,
        shift_magnitude=shift,
        shift_pct=shift_pct,
        split_index=split,
        record_count=n,
    )


def scan_step_changes(
    metrics: List[Metric],
    history: MetricHistory,
    min_records: int = 6,
    threshold_pct: float = 0.20,
) -> List[StepChangeResult]:
    """Run step-change detection across all *metrics*, returning only hits."""
    results = []
    for m in metrics:
        r = detect_step_change(m, history, min_records=min_records, threshold_pct=threshold_pct)
        if r is not None:
            results.append(r)
    return results
