"""Exponentially Weighted Moving Average (EWMA) smoothing and anomaly detection."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.metrics import Metric
from pipewatch.history import MetricHistory


@dataclass
class EWMAResult:
    name: str
    current_value: float
    ewma: float
    deviation: float          # abs(current - ewma)
    relative_deviation: float # deviation / ewma if ewma != 0 else 0
    is_anomalous: bool
    alpha: float
    threshold: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "current_value": self.current_value,
            "ewma": round(self.ewma, 6),
            "deviation": round(self.deviation, 6),
            "relative_deviation": round(self.relative_deviation, 6),
            "is_anomalous": self.is_anomalous,
            "alpha": self.alpha,
            "threshold": self.threshold,
        }


def _compute_ewma(values: List[float], alpha: float) -> float:
    """Compute EWMA over a list of values, returning the final smoothed value."""
    if not values:
        raise ValueError("values must not be empty")
    ewma = values[0]
    for v in values[1:]:
        ewma = alpha * v + (1.0 - alpha) * ewma
    return ewma


def detect_ewma(
    metric: Metric,
    history: MetricHistory,
    alpha: float = 0.3,
    threshold: float = 0.2,
    min_records: int = 5,
) -> Optional[EWMAResult]:
    """Detect whether the latest value deviates significantly from its EWMA.

    Args:
        metric:      The most recent metric reading.
        history:     MetricHistory instance to pull historical values from.
        alpha:       Smoothing factor in (0, 1]. Higher = more weight on recent values.
        threshold:   Relative deviation threshold above which a value is anomalous.
        min_records: Minimum historical records required.
    """
    if not (0 < alpha <= 1.0):
        raise ValueError("alpha must be in (0, 1]")
    if threshold <= 0:
        raise ValueError("threshold must be positive")

    records = history.for_name(metric.name)
    if len(records) < min_records:
        return None

    values = [r.value for r in records]
    ewma = _compute_ewma(values[:-1], alpha)  # exclude current for baseline
    current = values[-1]
    deviation = abs(current - ewma)
    relative = deviation / abs(ewma) if ewma != 0 else 0.0
    is_anomalous = relative > threshold

    return EWMAResult(
        name=metric.name,
        current_value=current,
        ewma=ewma,
        deviation=deviation,
        relative_deviation=relative,
        is_anomalous=is_anomalous,
        alpha=alpha,
        threshold=threshold,
    )


def scan_ewma(
    metrics: List[Metric],
    history: MetricHistory,
    alpha: float = 0.3,
    threshold: float = 0.2,
    min_records: int = 5,
) -> List[EWMAResult]:
    """Run EWMA detection across a list of metrics, returning only non-None results."""
    results = []
    for m in metrics:
        r = detect_ewma(m, history, alpha=alpha, threshold=threshold, min_records=min_records)
        if r is not None:
            results.append(r)
    return results
