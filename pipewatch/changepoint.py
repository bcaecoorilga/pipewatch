"""Change-point detection: identify when a metric's mean shifts significantly."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class ChangepointResult:
    metric_name: str
    changepoint_index: int          # index in the value series where shift occurred
    before_mean: float
    after_mean: float
    delta: float                    # after_mean - before_mean
    relative_change: float          # delta / before_mean (0.0 if before_mean == 0)
    detected: bool

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "changepoint_index": self.changepoint_index,
            "before_mean": round(self.before_mean, 4),
            "after_mean": round(self.after_mean, 4),
            "delta": round(self.delta, 4),
            "relative_change": round(self.relative_change, 4),
            "detected": self.detected,
        }


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _best_split(values: List[float]) -> int:
    """Return the index i that maximises |mean(left) - mean(right)|."""
    best_idx = 1
    best_diff = 0.0
    for i in range(1, len(values)):
        left = values[:i]
        right = values[i:]
        diff = abs(_mean(left) - _mean(right))
        if diff > best_diff:
            best_diff = diff
            best_idx = i
    return best_idx


def detect_changepoint(
    name: str,
    history: MetricHistory,
    min_records: int = 6,
    threshold_pct: float = 0.15,
) -> Optional[ChangepointResult]:
    """Detect a single change-point in *name*'s history.

    Returns None when there is insufficient data.  A result is flagged as
    *detected* when the relative shift across the best split exceeds
    *threshold_pct* (default 15 %).
    """
    records = history.for_name(name)
    if len(records) < min_records:
        return None

    values = [r.value for r in records]
    idx = _best_split(values)
    before = _mean(values[:idx])
    after = _mean(values[idx:])
    delta = after - before
    relative = delta / before if before != 0.0 else 0.0
    detected = abs(relative) >= threshold_pct

    return ChangepointResult(
        metric_name=name,
        changepoint_index=idx,
        before_mean=before,
        after_mean=after,
        delta=delta,
        relative_change=relative,
        detected=detected,
    )


def scan_changepoints(
    metrics: List[Metric],
    history: MetricHistory,
    min_records: int = 6,
    threshold_pct: float = 0.15,
) -> List[ChangepointResult]:
    """Run change-point detection for every metric in *metrics*."""
    results: List[ChangepointResult] = []
    seen: set = set()
    for m in metrics:
        if m.name in seen:
            continue
        seen.add(m.name)
        result = detect_changepoint(m.name, history, min_records, threshold_pct)
        if result is not None:
            results.append(result)
    return results
