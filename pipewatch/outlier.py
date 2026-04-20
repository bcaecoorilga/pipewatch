"""Outlier detection for pipeline metrics using IQR-based method."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class OutlierResult:
    name: str
    value: float
    q1: float
    q3: float
    iqr: float
    lower_fence: float
    upper_fence: float
    is_outlier: bool
    direction: Optional[str]  # "high", "low", or None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "q1": self.q1,
            "q3": self.q3,
            "iqr": self.iqr,
            "lower_fence": self.lower_fence,
            "upper_fence": self.upper_fence,
            "is_outlier": self.is_outlier,
            "direction": self.direction,
        }


def _quartiles(values: List[float]):
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    lower = sorted_vals[:mid]
    upper = sorted_vals[mid:] if n % 2 == 0 else sorted_vals[mid + 1 :]
    q1 = sorted_vals[len(lower) // 2] if lower else sorted_vals[0]
    q3 = upper[len(upper) // 2] if upper else sorted_vals[-1]
    return q1, q3


def detect_outlier(
    metric: Metric, history: MetricHistory, multiplier: float = 1.5
) -> Optional[OutlierResult]:
    records = history.for_name(metric.name)
    values = [r.value for r in records]
    if len(values) < 4:
        return None

    q1, q3 = _quartiles(values)
    iqr = q3 - q1
    lower_fence = q1 - multiplier * iqr
    upper_fence = q3 + multiplier * iqr

    v = metric.value
    is_outlier = v < lower_fence or v > upper_fence
    direction: Optional[str] = None
    if is_outlier:
        direction = "high" if v > upper_fence else "low"

    return OutlierResult(
        name=metric.name,
        value=v,
        q1=q1,
        q3=q3,
        iqr=iqr,
        lower_fence=lower_fence,
        upper_fence=upper_fence,
        is_outlier=is_outlier,
        direction=direction,
    )


def scan_outliers(
    metrics: List[Metric], history: MetricHistory, multiplier: float = 1.5
) -> List[OutlierResult]:
    results = []
    for m in metrics:
        r = detect_outlier(m, history, multiplier)
        if r is not None:
            results.append(r)
    return results
