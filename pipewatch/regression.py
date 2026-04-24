"""Regression detection: flags metrics whose recent values deviate
significantly from a fitted linear baseline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class RegressionResult:
    name: str
    mean_baseline: float
    recent_mean: float
    deviation_pct: float  # signed, positive = above baseline
    regressed: bool
    threshold_pct: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "mean_baseline": round(self.mean_baseline, 4),
            "recent_mean": round(self.recent_mean, 4),
            "deviation_pct": round(self.deviation_pct, 4),
            "regressed": self.regressed,
            "threshold_pct": self.threshold_pct,
        }


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def detect_regression(
    history: MetricHistory,
    name: str,
    baseline_window: int = 20,
    recent_window: int = 5,
    threshold_pct: float = 15.0,
) -> Optional[RegressionResult]:
    """Compare the mean of the most recent *recent_window* records against
    the mean of the previous *baseline_window* records.  Returns None when
    there is insufficient data."""
    records = history.for_name(name)
    required = baseline_window + recent_window
    if len(records) < required:
        return None

    baseline_records = records[-(baseline_window + recent_window):-recent_window]
    recent_records = records[-recent_window:]

    baseline_values = [r.value for r in baseline_records]
    recent_values = [r.value for r in recent_records]

    baseline_mean = _mean(baseline_values)
    recent_mean = _mean(recent_values)

    if baseline_mean == 0.0:
        deviation_pct = 0.0
    else:
        deviation_pct = ((recent_mean - baseline_mean) / abs(baseline_mean)) * 100.0

    regressed = abs(deviation_pct) >= threshold_pct

    return RegressionResult(
        name=name,
        mean_baseline=baseline_mean,
        recent_mean=recent_mean,
        deviation_pct=deviation_pct,
        regressed=regressed,
        threshold_pct=threshold_pct,
    )


def scan_regressions(
    history: MetricHistory,
    metrics: List[Metric],
    baseline_window: int = 20,
    recent_window: int = 5,
    threshold_pct: float = 15.0,
) -> List[RegressionResult]:
    """Run regression detection for every metric that has sufficient history."""
    results: List[RegressionResult] = []
    seen: set = set()
    for m in metrics:
        if m.name in seen:
            continue
        seen.add(m.name)
        result = detect_regression(
            history, m.name, baseline_window, recent_window, threshold_pct
        )
        if result is not None:
            results.append(result)
    return results
