"""Envelope detection: checks if a metric stays within a dynamic band
based on historical mean ± tolerance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.metrics import Metric
from pipewatch.history import MetricHistory


@dataclass
class EnvelopeResult:
    name: str
    current_value: float
    mean: float
    lower_bound: float
    upper_bound: float
    tolerance: float
    inside: bool
    deviation: float  # signed distance from nearest bound (negative = inside)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "current_value": self.current_value,
            "mean": self.mean,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "tolerance": self.tolerance,
            "inside": self.inside,
            "deviation": round(self.deviation, 6),
        }


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def detect_envelope(
    metric: Metric,
    history: MetricHistory,
    tolerance: float = 0.2,
    min_history: int = 5,
) -> Optional[EnvelopeResult]:
    """Return an EnvelopeResult if enough history exists, else None.

    tolerance: fractional band around the mean (e.g. 0.2 = ±20%).
    """
    if tolerance <= 0:
        return None

    records = history.for_name(metric.name)
    if len(records) < min_history:
        return None

    values = [r.value for r in records]
    mu = _mean(values)
    band = abs(mu) * tolerance if mu != 0 else tolerance
    lower = mu - band
    upper = mu + band
    current = metric.value
    inside = lower <= current <= upper

    if current < lower:
        deviation = current - lower
    elif current > upper:
        deviation = current - upper
    else:
        deviation = -min(current - lower, upper - current)

    return EnvelopeResult(
        name=metric.name,
        current_value=current,
        mean=round(mu, 6),
        lower_bound=round(lower, 6),
        upper_bound=round(upper, 6),
        tolerance=tolerance,
        inside=inside,
        deviation=deviation,
    )


def scan_envelopes(
    metrics: List[Metric],
    history: MetricHistory,
    tolerance: float = 0.2,
    min_history: int = 5,
) -> List[EnvelopeResult]:
    results = []
    for m in metrics:
        r = detect_envelope(m, history, tolerance=tolerance, min_history=min_history)
        if r is not None:
            results.append(r)
    return results
