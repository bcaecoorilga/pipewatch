"""Momentum detection: measures the acceleration of change in a metric's values."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class MomentumResult:
    name: str
    momentum: float          # second derivative (acceleration) of values
    direction: str           # "accelerating", "decelerating", "steady"
    sample_count: int
    threshold: float
    is_significant: bool

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "momentum": round(self.momentum, 6),
            "direction": self.direction,
            "sample_count": self.sample_count,
            "threshold": self.threshold,
            "is_significant": self.is_significant,
        }


def _classify(momentum: float, threshold: float) -> tuple[str, bool]:
    if abs(momentum) < threshold:
        return "steady", False
    return ("accelerating" if momentum > 0 else "decelerating"), True


def detect_momentum(
    name: str,
    history: MetricHistory,
    min_samples: int = 5,
    threshold: float = 0.01,
) -> Optional[MomentumResult]:
    records = history.for_name(name)
    if len(records) < min_samples:
        return None

    values = [r.value for r in records]
    # First differences
    d1 = [values[i + 1] - values[i] for i in range(len(values) - 1)]
    # Second differences (acceleration)
    d2 = [d1[i + 1] - d1[i] for i in range(len(d1) - 1)]
    if not d2:
        return None

    momentum = sum(d2) / len(d2)
    direction, is_significant = _classify(momentum, threshold)

    return MomentumResult(
        name=name,
        momentum=momentum,
        direction=direction,
        sample_count=len(records),
        threshold=threshold,
        is_significant=is_significant,
    )


def scan_momentums(
    metrics: List[Metric],
    history: MetricHistory,
    min_samples: int = 5,
    threshold: float = 0.01,
) -> List[MomentumResult]:
    results = []
    seen: set = set()
    for m in metrics:
        if m.name in seen:
            continue
        seen.add(m.name)
        result = detect_momentum(m.name, history, min_samples, threshold)
        if result is not None:
            results.append(result)
    return results
