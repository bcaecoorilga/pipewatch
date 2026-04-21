"""Velocity tracking: measures how fast a metric's value is changing over time."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class VelocityResult:
    name: str
    samples: int
    velocity_per_second: float  # units/second (can be negative)
    velocity_per_minute: float
    direction: str  # "accelerating", "decelerating", "stable"
    latest_value: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "samples": self.samples,
            "velocity_per_second": round(self.velocity_per_second, 6),
            "velocity_per_minute": round(self.velocity_per_minute, 6),
            "direction": self.direction,
            "latest_value": self.latest_value,
        }


def _classify_direction(velocity: float, threshold: float = 0.001) -> str:
    if velocity > threshold:
        return "accelerating"
    if velocity < -threshold:
        return "decelerating"
    return "stable"


def compute_velocity(
    name: str,
    history: MetricHistory,
    window_seconds: float = 300.0,
) -> Optional[VelocityResult]:
    """Compute the rate of change (velocity) for a metric over a time window."""
    if window_seconds <= 0:
        return None

    from datetime import datetime, timezone

    now = datetime.now(tz=timezone.utc)
    cutoff = now.timestamp() - window_seconds
    records: List[Metric] = [
        r for r in history.all(name) if r.timestamp >= cutoff
    ]

    if len(records) < 2:
        return None

    records_sorted = sorted(records, key=lambda r: r.timestamp)
    earliest = records_sorted[0]
    latest = records_sorted[-1]

    dt = latest.timestamp - earliest.timestamp
    if dt == 0:
        return None

    dv = latest.value - earliest.value
    vel_per_sec = dv / dt
    vel_per_min = vel_per_sec * 60.0

    return VelocityResult(
        name=name,
        samples=len(records_sorted),
        velocity_per_second=vel_per_sec,
        velocity_per_minute=vel_per_min,
        direction=_classify_direction(vel_per_sec),
        latest_value=latest.value,
    )


def scan_velocities(
    history: MetricHistory,
    window_seconds: float = 300.0,
) -> List[VelocityResult]:
    """Compute velocity for every metric name found in history."""
    names = {r.name for r in history.all()}
    results = []
    for name in sorted(names):
        result = compute_velocity(name, history, window_seconds)
        if result is not None:
            results.append(result)
    return results
