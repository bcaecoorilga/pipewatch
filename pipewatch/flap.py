"""Flap detection: identifies metrics that oscillate rapidly between statuses."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus


@dataclass
class FlapResult:
    name: str
    transitions: int
    window: int
    flapping: bool
    statuses: List[str]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "transitions": self.transitions,
            "window": self.window,
            "flapping": self.flapping,
            "statuses": self.statuses,
        }


def detect_flap(
    name: str,
    history: MetricHistory,
    window: int = 10,
    min_transitions: int = 4,
) -> Optional[FlapResult]:
    """Detect flapping for a single metric over the last *window* records."""
    records = history.for_name(name)
    if len(records) < 2:
        return None

    recent = records[-window:]
    statuses = [r.status.value for r in recent]

    transitions = sum(
        1 for i in range(1, len(statuses)) if statuses[i] != statuses[i - 1]
    )

    return FlapResult(
        name=name,
        transitions=transitions,
        window=len(recent),
        flapping=transitions >= min_transitions,
        statuses=statuses,
    )


def scan_flaps(
    names: List[str],
    history: MetricHistory,
    window: int = 10,
    min_transitions: int = 4,
) -> List[FlapResult]:
    """Scan multiple metrics for flapping behaviour."""
    results = []
    for name in names:
        result = detect_flap(name, history, window=window, min_transitions=min_transitions)
        if result is not None:
            results.append(result)
    return results
