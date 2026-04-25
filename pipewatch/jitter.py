"""Jitter detection: measures variability/instability in metric values over a window."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class JitterResult:
    metric_name: str
    mean: float
    std_dev: float
    cv: float          # coefficient of variation = std_dev / mean
    is_jittery: bool
    threshold_cv: float
    window: int

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "mean": round(self.mean, 4),
            "std_dev": round(self.std_dev, 4),
            "cv": round(self.cv, 4),
            "is_jittery": self.is_jittery,
            "threshold_cv": self.threshold_cv,
            "window": self.window,
        }


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _std_dev(values: List[float], mean: float) -> float:
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5


def detect_jitter(
    name: str,
    history: MetricHistory,
    window: int = 20,
    threshold_cv: float = 0.3,
) -> Optional[JitterResult]:
    """Detect jitter for a single metric using coefficient of variation."""
    records = history.for_name(name)
    if len(records) < 3:
        return None

    recent = records[-window:]
    values = [r.value for r in recent]

    mean = _mean(values)
    if mean == 0.0:
        return None

    std = _std_dev(values, mean)
    cv = std / abs(mean)

    return JitterResult(
        metric_name=name,
        mean=mean,
        std_dev=std,
        cv=cv,
        is_jittery=cv > threshold_cv,
        threshold_cv=threshold_cv,
        window=len(recent),
    )


def scan_jitter(
    metrics: List[Metric],
    history: MetricHistory,
    window: int = 20,
    threshold_cv: float = 0.3,
) -> List[JitterResult]:
    """Scan all metrics for jitter and return results."""
    results = []
    seen: set = set()
    for m in metrics:
        if m.name in seen:
            continue
        seen.add(m.name)
        result = detect_jitter(m.name, history, window=window, threshold_cv=threshold_cv)
        if result is not None:
            results.append(result)
    return results
