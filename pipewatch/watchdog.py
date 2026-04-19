"""Watchdog: detect metrics that have gone stale (no updates within a threshold)."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewatch.collector import MetricCollector
from pipewatch.metrics import Metric


@dataclass
class StalenessRule:
    metric_name: str
    max_age_seconds: float


@dataclass
class StalenessResult:
    metric_name: str
    last_seen: Optional[datetime]
    max_age_seconds: float
    is_stale: bool
    age_seconds: Optional[float]

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "max_age_seconds": self.max_age_seconds,
            "is_stale": self.is_stale,
            "age_seconds": self.age_seconds,
        }


class Watchdog:
    def __init__(self, collector: MetricCollector):
        self._collector = collector
        self._rules: Dict[str, StalenessRule] = {}

    def register_rule(self, metric_name: str, max_age_seconds: float) -> None:
        self._rules[metric_name] = StalenessRule(
            metric_name=metric_name,
            max_age_seconds=max_age_seconds,
        )

    def check(self, now: Optional[datetime] = None) -> List[StalenessResult]:
        now = now or datetime.utcnow()
        results = []
        for name, rule in self._rules.items():
            latest: Optional[Metric] = self._collector.latest(name)
            if latest is None:
                results.append(StalenessResult(
                    metric_name=name,
                    last_seen=None,
                    max_age_seconds=rule.max_age_seconds,
                    is_stale=True,
                    age_seconds=None,
                ))
            else:
                age = (now - latest.timestamp).total_seconds()
                results.append(StalenessResult(
                    metric_name=name,
                    last_seen=latest.timestamp,
                    max_age_seconds=rule.max_age_seconds,
                    is_stale=age > rule.max_age_seconds,
                    age_seconds=age,
                ))
        return results

    def stale(self, now: Optional[datetime] = None) -> List[StalenessResult]:
        return [r for r in self.check(now=now) if r.is_stale]
