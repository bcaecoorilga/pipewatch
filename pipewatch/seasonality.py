"""Seasonality detection for pipeline metrics.

Detects whether a metric exhibits repeating periodic patterns
by comparing values at regular intervals (hour-of-day, day-of-week).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
from collections import defaultdict
import math

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class SeasonalityResult:
    name: str
    period: str          # e.g. "hourly", "daily"
    bucket_means: Dict[int, float]
    variance_ratio: float  # between-bucket variance / total variance
    is_seasonal: bool
    strength: str        # "none", "weak", "moderate", "strong"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "period": self.period,
            "bucket_means": self.bucket_means,
            "variance_ratio": round(self.variance_ratio, 4),
            "is_seasonal": self.is_seasonal,
            "strength": self.strength,
        }


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return sum((v - m) ** 2 for v in values) / len(values)


def _classify_strength(ratio: float) -> str:
    if ratio < 0.2:
        return "none"
    if ratio < 0.4:
        return "weak"
    if ratio < 0.65:
        return "moderate"
    return "strong"


def detect_seasonality(
    name: str,
    history: MetricHistory,
    period: str = "hourly",
    min_records: int = 12,
) -> Optional[SeasonalityResult]:
    """Detect seasonality for a single metric.

    Args:
        name: Metric name to analyse.
        history: MetricHistory instance.
        period: ``"hourly"`` (bucket by hour-of-day, 0-23) or
                ``"daily"`` (bucket by day-of-week, 0-6).
        min_records: Minimum records required to attempt detection.
    """
    records = history.for_name(name)
    if len(records) < min_records:
        return None

    buckets: Dict[int, List[float]] = defaultdict(list)
    for rec in records:
        key = rec.timestamp.hour if period == "hourly" else rec.timestamp.weekday()
        buckets[key].append(rec.value)

    if len(buckets) < 2:
        return None

    all_values = [rec.value for rec in records]
    total_var = _variance(all_values)
    if total_var == 0.0:
        return SeasonalityResult(
            name=name,
            period=period,
            bucket_means={k: _mean(v) for k, v in buckets.items()},
            variance_ratio=0.0,
            is_seasonal=False,
            strength="none",
        )

    bucket_means = {k: _mean(v) for k, v in buckets.items()}
    grand_mean = _mean(all_values)
    between_var = _mean([(m - grand_mean) ** 2 for m in bucket_means.values()])
    ratio = min(between_var / total_var, 1.0)
    strength = _classify_strength(ratio)

    return SeasonalityResult(
        name=name,
        period=period,
        bucket_means=bucket_means,
        variance_ratio=ratio,
        is_seasonal=ratio >= 0.2,
        strength=strength,
    )


def scan_seasonality(
    history: MetricHistory,
    period: str = "hourly",
    min_records: int = 12,
) -> List[SeasonalityResult]:
    """Run seasonality detection across all metrics in history."""
    names = {rec.name for rec in history.all()}
    results = []
    for name in sorted(names):
        result = detect_seasonality(name, history, period=period, min_records=min_records)
        if result is not None:
            results.append(result)
    return results
