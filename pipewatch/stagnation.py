"""Stagnation detection: identifies metrics that have not changed meaningfully over time."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.metrics import Metric


@dataclass
class StagnationResult:
    metric_name: str
    window: int          # number of recent records examined
    unique_values: int   # distinct values seen in the window
    min_value: float
    max_value: float
    spread: float        # max - min
    is_stagnant: bool
    tolerance: float     # spread must exceed this to be considered non-stagnant

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "window": self.window,
            "unique_values": self.unique_values,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "spread": self.spread,
            "is_stagnant": self.is_stagnant,
            "tolerance": self.tolerance,
        }


def detect_stagnation(
    name: str,
    history,
    window: int = 10,
    tolerance: float = 0.0,
) -> Optional[StagnationResult]:
    """Return a StagnationResult if enough history exists, else None."""
    records: List[Metric] = history.for_name(name)
    if len(records) < 2:
        return None

    recent = records[-window:]
    values = [r.value for r in recent]
    lo, hi = min(values), max(values)
    spread = hi - lo
    unique = len(set(values))

    return StagnationResult(
        metric_name=name,
        window=len(recent),
        unique_values=unique,
        min_value=lo,
        max_value=hi,
        spread=spread,
        is_stagnant=spread <= tolerance,
        tolerance=tolerance,
    )


def scan_stagnations(
    history,
    window: int = 10,
    tolerance: float = 0.0,
) -> List[StagnationResult]:
    """Scan all known metric names for stagnation."""
    results = []
    for name in history.all_names():
        result = detect_stagnation(name, history, window=window, tolerance=tolerance)
        if result is not None:
            results.append(result)
    return results
