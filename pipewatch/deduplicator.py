"""Metric event deduplication — suppress repeated identical metric values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from pipewatch.metrics import Metric


@dataclass
class DeduplicationEntry:
    value: float
    status: str
    count: int = 1

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "status": self.status,
            "count": self.count,
        }


@dataclass
class DeduplicationResult:
    metric_name: str
    is_duplicate: bool
    previous_value: Optional[float]
    current_value: float
    suppressed_count: int

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "is_duplicate": self.is_duplicate,
            "previous_value": self.previous_value,
            "current_value": self.current_value,
            "suppressed_count": self.suppressed_count,
        }


class Deduplicator:
    """Tracks last-seen metric values and detects duplicates."""

    def __init__(self, tolerance: float = 0.0) -> None:
        """Args:
            tolerance: Absolute difference below which values are considered equal.
        """
        self.tolerance = tolerance
        self._cache: Dict[str, DeduplicationEntry] = {}

    def check(self, metric: Metric) -> DeduplicationResult:
        """Check whether *metric* is a duplicate of the previously seen value.

        Returns a DeduplicationResult indicating whether this event should be
        suppressed.  The internal counter is incremented for duplicate runs.
        """
        name = metric.name
        current = metric.value
        status = metric.status.value if hasattr(metric.status, "value") else str(metric.status)

        entry = self._cache.get(name)

        if entry is None:
            self._cache[name] = DeduplicationEntry(value=current, status=status, count=1)
            return DeduplicationResult(
                metric_name=name,
                is_duplicate=False,
                previous_value=None,
                current_value=current,
                suppressed_count=0,
            )

        is_dup = abs(current - entry.value) <= self.tolerance and status == entry.status

        if is_dup:
            entry.count += 1
        else:
            prev = entry.value
            self._cache[name] = DeduplicationEntry(value=current, status=status, count=1)
            return DeduplicationResult(
                metric_name=name,
                is_duplicate=False,
                previous_value=prev,
                current_value=current,
                suppressed_count=0,
            )

        return DeduplicationResult(
            metric_name=name,
            is_duplicate=True,
            previous_value=entry.value,
            current_value=current,
            suppressed_count=entry.count - 1,
        )

    def reset(self, metric_name: str) -> None:
        """Clear cached state for a single metric."""
        self._cache.pop(metric_name, None)

    def reset_all(self) -> None:
        """Clear all cached state."""
        self._cache.clear()
