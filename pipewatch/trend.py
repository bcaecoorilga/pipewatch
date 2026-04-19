"""Trend analysis over metric history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TrendResult:
    name: str
    count: int
    mean: float
    min_value: float
    max_value: float
    trend: str  # 'stable', 'rising', 'falling'

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "mean": self.mean,
            "min": self.min_value,
            "max": self.max_value,
            "trend": self.trend,
        }


def _detect_trend(values: List[float], window: int = 3) -> str:
    if len(values) < 2:
        return "stable"
    recent = values[-window:]
    if all(recent[i] < recent[i + 1] for i in range(len(recent) - 1)):
        return "rising"
    if all(recent[i] > recent[i + 1] for i in range(len(recent) - 1)):
        return "falling"
    return "stable"


def analyze(records: List[dict]) -> Optional[TrendResult]:
    if not records:
        return None
    name = records[0].get("name", "unknown")
    values = []
    for r in records:
        try:
            values.append(float(r["value"]))
        except (KeyError, TypeError, ValueError):
            pass
    if not values:
        return None
    return TrendResult(
        name=name,
        count=len(values),
        mean=round(sum(values) / len(values), 4),
        min_value=min(values),
        max_value=max(values),
        trend=_detect_trend(values),
    )
