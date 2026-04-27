"""Cooldown tracker: detects when a metric has been in a non-OK state
for longer than a configured duration and flags it for escalation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewatch.metrics import Metric, MetricStatus


@dataclass
class CooldownResult:
    name: str
    status: MetricStatus
    bad_since: datetime
    duration_seconds: float
    threshold_seconds: float
    escalated: bool

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "bad_since": self.bad_since.isoformat(),
            "duration_seconds": round(self.duration_seconds, 3),
            "threshold_seconds": self.threshold_seconds,
            "escalated": self.escalated,
        }


class CooldownTracker:
    """Tracks how long each metric has been in a non-OK state."""

    def __init__(self, threshold_seconds: float = 300.0) -> None:
        if threshold_seconds <= 0:
            raise ValueError("threshold_seconds must be positive")
        self.threshold_seconds = threshold_seconds
        # name -> datetime when the metric first went non-OK
        self._bad_since: Dict[str, datetime] = {}

    def update(self, metric: Metric) -> Optional[CooldownResult]:
        """Update tracker state and return a CooldownResult if escalated."""
        name = metric.name
        now = metric.timestamp

        if metric.status == MetricStatus.OK:
            self._bad_since.pop(name, None)
            return None

        if name not in self._bad_since:
            self._bad_since[name] = now
            return None

        bad_since = self._bad_since[name]
        duration = (now - bad_since).total_seconds()
        escalated = duration >= self.threshold_seconds

        return CooldownResult(
            name=name,
            status=metric.status,
            bad_since=bad_since,
            duration_seconds=duration,
            threshold_seconds=self.threshold_seconds,
            escalated=escalated,
        )

    def scan(self, metrics: List[Metric]) -> List[CooldownResult]:
        """Update all metrics and return only escalated results."""
        results = []
        for m in metrics:
            result = self.update(m)
            if result and result.escalated:
                results.append(result)
        return results

    def reset(self, name: str) -> None:
        """Manually clear the bad-since timer for a metric."""
        self._bad_since.pop(name, None)
