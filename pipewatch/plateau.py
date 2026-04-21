"""Plateau detection: identify metrics that have stopped changing meaningfully."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class PlateauResult:
    name: str
    window: int          # number of records examined
    min_value: float
    max_value: float
    range_value: float   # max - min
    threshold: float     # tolerance used
    is_plateau: bool
    duration_seconds: float  # wall-clock span of the window

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "window": self.window,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "range_value": self.range_value,
            "threshold": self.threshold,
            "is_plateau": self.is_plateau,
            "duration_seconds": self.duration_seconds,
        }


def detect_plateau(
    name: str,
    history: MetricHistory,
    window: int = 10,
    tolerance: float = 0.01,
) -> Optional[PlateauResult]:
    """Return a PlateauResult if enough history exists, else None."""
    records = history.for_name(name)
    if len(records) < window:
        return None

    recent = records[-window:]
    values = [r.value for r in recent]
    lo, hi = min(values), max(values)
    rng = hi - lo
    span = (recent[-1].timestamp - recent[0].timestamp).total_seconds()

    return PlateauResult(
        name=name,
        window=window,
        min_value=lo,
        max_value=hi,
        range_value=rng,
        threshold=tolerance,
        is_plateau=rng <= tolerance,
        duration_seconds=span,
    )


def scan_plateaus(
    metrics: List[Metric],
    history: MetricHistory,
    window: int = 10,
    tolerance: float = 0.01,
) -> List[PlateauResult]:
    """Scan all metrics and return results where plateau was detectable."""
    results = []
    seen: set = set()
    for m in metrics:
        if m.name in seen:
            continue
        seen.add(m.name)
        result = detect_plateau(m.name, history, window=window, tolerance=tolerance)
        if result is not None:
            results.append(result)
    return results
