"""Noise detection: identifies metrics with high signal-to-noise ratio issues."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class NoiseResult:
    name: str
    mean: float
    std_dev: float
    cv: float          # coefficient of variation = std_dev / mean
    noisy: bool
    label: str         # "clean" | "noisy" | "very_noisy"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "mean": round(self.mean, 4),
            "std_dev": round(self.std_dev, 4),
            "cv": round(self.cv, 4),
            "noisy": self.noisy,
            "label": self.label,
        }


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _std_dev(values: List[float], mean: float) -> float:
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5


def _classify(cv: float) -> str:
    if cv < 0.1:
        return "clean"
    if cv < 0.3:
        return "noisy"
    return "very_noisy"


def detect_noise(
    metric: Metric,
    history: MetricHistory,
    min_records: int = 5,
    cv_threshold: float = 0.1,
) -> Optional[NoiseResult]:
    records = history.for_name(metric.name)
    if len(records) < min_records:
        return None

    values = [r.value for r in records]
    mean = _mean(values)
    if mean == 0.0:
        return None

    std = _std_dev(values, mean)
    cv = std / abs(mean)
    label = _classify(cv)
    noisy = cv >= cv_threshold

    return NoiseResult(
        name=metric.name,
        mean=mean,
        std_dev=std,
        cv=cv,
        noisy=noisy,
        label=label,
    )


def scan_noise(
    metrics: List[Metric],
    history: MetricHistory,
    min_records: int = 5,
    cv_threshold: float = 0.1,
) -> List[NoiseResult]:
    results = []
    for m in metrics:
        r = detect_noise(m, history, min_records, cv_threshold)
        if r is not None:
            results.append(r)
    return results
