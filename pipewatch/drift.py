"""Metric drift detection: tracks how far current values have moved from a reference window."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class DriftResult:
    name: str
    reference_mean: float
    current_mean: float
    drift_abs: float
    drift_pct: float
    drifted: bool
    threshold_pct: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "reference_mean": round(self.reference_mean, 4),
            "current_mean": round(self.current_mean, 4),
            "drift_abs": round(self.drift_abs, 4),
            "drift_pct": round(self.drift_pct, 4),
            "drifted": self.drifted,
            "threshold_pct": self.threshold_pct,
        }


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def detect_drift(
    history: MetricHistory,
    name: str,
    reference_window: int = 10,
    current_window: int = 5,
    threshold_pct: float = 20.0,
) -> Optional[DriftResult]:
    """Compare the mean of the most recent *current_window* records against
    the *reference_window* records that precede them."""
    records = history.for_name(name)
    required = reference_window + current_window
    if len(records) < required:
        return None

    ref_records = records[-(required): -current_window]
    cur_records = records[-current_window:]

    ref_mean = _mean([r.value for r in ref_records])
    cur_mean = _mean([r.value for r in cur_records])

    drift_abs = abs(cur_mean - ref_mean)
    drift_pct = (drift_abs / abs(ref_mean) * 100.0) if ref_mean != 0.0 else 0.0
    drifted = drift_pct >= threshold_pct

    return DriftResult(
        name=name,
        reference_mean=ref_mean,
        current_mean=cur_mean,
        drift_abs=drift_abs,
        drift_pct=drift_pct,
        drifted=drifted,
        threshold_pct=threshold_pct,
    )


def scan_drifts(
    history: MetricHistory,
    metrics: List[Metric],
    reference_window: int = 10,
    current_window: int = 5,
    threshold_pct: float = 20.0,
) -> List[DriftResult]:
    results = []
    seen: set = set()
    for m in metrics:
        if m.name in seen:
            continue
        seen.add(m.name)
        result = detect_drift(history, m.name, reference_window, current_window, threshold_pct)
        if result is not None:
            results.append(result)
    return results
