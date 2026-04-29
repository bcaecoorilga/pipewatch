"""Heartbeat monitor: detects missing or late metric submissions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from pipewatch.collector import MetricCollector


@dataclass
class HeartbeatResult:
    name: str
    expected_interval_s: float
    last_seen: Optional[datetime]
    seconds_since: Optional[float]
    is_alive: bool
    message: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "expected_interval_s": self.expected_interval_s,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "seconds_since": round(self.seconds_since, 3) if self.seconds_since is not None else None,
            "is_alive": self.is_alive,
            "message": self.message,
        }


@dataclass
class HeartbeatMonitor:
    rules: Dict[str, float] = field(default_factory=dict)  # name -> interval_s

    def register(self, name: str, expected_interval_s: float) -> None:
        if expected_interval_s <= 0:
            raise ValueError("expected_interval_s must be positive")
        self.rules[name] = expected_interval_s

    def check(self, name: str, collector: MetricCollector, now: Optional[datetime] = None) -> Optional[HeartbeatResult]:
        if name not in self.rules:
            return None
        interval = self.rules[name]
        now = now or datetime.utcnow()
        latest = collector.latest(name)
        if latest is None:
            return HeartbeatResult(
                name=name,
                expected_interval_s=interval,
                last_seen=None,
                seconds_since=None,
                is_alive=False,
                message=f"{name!r} has never been recorded",
            )
        delta = (now - latest.timestamp).total_seconds()
        alive = delta <= interval
        msg = (
            f"{name!r} last seen {delta:.1f}s ago (limit {interval}s)"
        )
        return HeartbeatResult(
            name=name,
            expected_interval_s=interval,
            last_seen=latest.timestamp,
            seconds_since=delta,
            is_alive=alive,
            message=msg,
        )

    def scan(self, collector: MetricCollector, now: Optional[datetime] = None) -> List[HeartbeatResult]:
        return [
            r
            for name in self.rules
            if (r := self.check(name, collector, now)) is not None
        ]
