"""Spike detection: identify sudden jumps or drops in metric values."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class SpikeResult:
    metric_name: str
    current_value: float
    reference_mean: float
    deviation: float          # absolute difference
    relative_change: float    # fraction: (current - mean) / mean
    is_spike: bool
    direction: str            # "up", "down", or "none"

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "reference_mean": round(self.reference_mean, 6),
            "deviation": round(self.deviation, 6),
            "relative_change": round(self.relative_change, 6),
            "is_spike": self.is_spike,
            "direction": self.direction,
        }


def detect_spike(
    metric: Metric,
    history: MetricHistory,
    *,
    threshold: float = 2.0,
    min_history: int = 3,
) -> Optional[SpikeResult]:
    """Detect whether *metric* is a spike relative to recent history.

    Args:
        metric: The current (latest) metric reading.
        history: Full history store.
        threshold: Relative-change magnitude that constitutes a spike (e.g. 2.0 = 200%).
        min_history: Minimum number of historical records required.

    Returns:
        SpikeResult or None if there is insufficient history.

    Raises:
        ValueError: If *threshold* is negative or *min_history* is less than 1.
    """
    if threshold < 0:
        raise ValueError(f"threshold must be non-negative, got {threshold}")
    if min_history < 1:
        raise ValueError(f"min_history must be at least 1, got {min_history}")

    records: List[Metric] = history.for_name(metric.name)
    # Exclude the current record if it was already appended
    prior = [r for r in records if r.timestamp != metric.timestamp]
    if len(prior) < min_history:
        return None

    values = [r.value for r in prior]
    mean = sum(values) / len(values)

    if mean == 0.0:
        return None

    deviation = metric.value - mean
    relative_change = deviation / abs(mean)
    is_spike = abs(relative_change) >= threshold
    direction = "none"
    if is_spike:
        direction = "up" if relative_change > 0 else "down"

    return SpikeResult(
        metric_name=metric.name,
        current_value=metric.value,
        reference_mean=mean,
        deviation=deviation,
        relative_change=relative_change,
        is_spike=is_spike,
        direction=direction,
    )


def scan_spikes(
    metrics: List[Metric],
    history: MetricHistory,
    *,
    threshold: float = 2.0,
    min_history: int = 3,
) -> List[SpikeResult]:
    """Run spike detection across a list of metrics, returning only detected spikes."""
    results = []
    for m in metrics:
        result = detect_spike(m, history, threshold=threshold, min_history=min_history)
        if result and result.is_spike:
            results.append(result)
    return results
