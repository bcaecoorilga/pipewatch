"""Pipeline health scoring: compute an overall health score from metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.metrics import Metric, MetricStatus


# Weight per status used in score calculation
_STATUS_WEIGHT: dict[MetricStatus, float] = {
    MetricStatus.OK: 1.0,
    MetricStatus.WARNING: 0.5,
    MetricStatus.CRITICAL: 0.0,
}


@dataclass
class HealthScore:
    score: float  # 0.0 – 1.0
    total: int
    ok_count: int
    warning_count: int
    critical_count: int
    grade: str = field(init=False)

    def __post_init__(self) -> None:
        self.grade = _grade(self.score)

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 4),
            "grade": self.grade,
            "total": self.total,
            "ok_count": self.ok_count,
            "warning_count": self.warning_count,
            "critical_count": self.critical_count,
        }


def _grade(score: float) -> str:
    if score >= 0.9:
        return "A"
    if score >= 0.75:
        return "B"
    if score >= 0.5:
        return "C"
    if score >= 0.25:
        return "D"
    return "F"


def compute_health(metrics: List[Metric]) -> Optional[HealthScore]:
    """Return a HealthScore for a list of Metric objects, or None if empty."""
    if not metrics:
        return None

    ok = sum(1 for m in metrics if m.status == MetricStatus.OK)
    warning = sum(1 for m in metrics if m.status == MetricStatus.WARNING)
    critical = sum(1 for m in metrics if m.status == MetricStatus.CRITICAL)
    total = len(metrics)

    raw = sum(_STATUS_WEIGHT.get(m.status, 0.0) for m in metrics)
    score = raw / total

    return HealthScore(
        score=score,
        total=total,
        ok_count=ok,
        warning_count=warning,
        critical_count=critical,
    )
