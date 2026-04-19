"""Simple linear forecast for metric values based on history."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric
import statistics


@dataclass
class ForecastResult:
    name: str
    steps: int
    predicted_values: List[float]
    slope: float
    intercept: float
    confidence: str  # 'low' | 'medium' | 'high'

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "steps": self.steps,
            "predicted_values": self.predicted_values,
            "slope": self.slope,
            "intercept": self.intercept,
            "confidence": self.confidence,
        }


def _linear_fit(values: List[float]):
    n = len(values)
    xs = list(range(n))
    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(values)
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return 0.0, mean_y
    slope = sum((xs[i] - mean_x) * (values[i] - mean_y) for i in range(n)) / denom
    intercept = mean_y - slope * mean_x
    return slope, intercept


def _confidence(n: int) -> str:
    if n >= 20:
        return "high"
    if n >= 8:
        return "medium"
    return "low"


def forecast(history: MetricHistory, name: str, steps: int = 3) -> Optional[ForecastResult]:
    records = history.for_name(name)
    values = [r.value for r in records]
    if len(values) < 2:
        return None
    slope, intercept = _linear_fit(values)
    n = len(values)
    predicted = [round(intercept + slope * (n + i), 6) for i in range(steps)]
    return ForecastResult(
        name=name,
        steps=steps,
        predicted_values=predicted,
        slope=round(slope, 6),
        intercept=round(intercept, 6),
        confidence=_confidence(n),
    )
