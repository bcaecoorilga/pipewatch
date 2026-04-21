"""SLA (Service Level Agreement) tracking for pipeline metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus


@dataclass
class SLARule:
    name: str
    metric_name: str
    max_critical_ratio: float  # 0.0 – 1.0: max fraction of readings allowed to be CRITICAL
    window_seconds: float = 3600.0

    def is_valid(self) -> bool:
        return (
            bool(self.name)
            and bool(self.metric_name)
            and 0.0 <= self.max_critical_ratio <= 1.0
            and self.window_seconds > 0
        )


@dataclass
class SLAResult:
    rule: SLARule
    total: int
    critical_count: int
    critical_ratio: float
    breached: bool

    def to_dict(self) -> dict:
        return {
            "rule": self.rule.name,
            "metric": self.rule.metric_name,
            "total": self.total,
            "critical_count": self.critical_count,
            "critical_ratio": round(self.critical_ratio, 4),
            "breached": self.breached,
        }


def check_sla(rule: SLARule, history: MetricHistory) -> Optional[SLAResult]:
    """Evaluate an SLA rule against recent history. Returns None if rule is invalid."""
    if not rule.is_valid():
        return None

    import time
    cutoff = time.time() - rule.window_seconds
    records = [
        r for r in history.for_name(rule.metric_name)
        if r.timestamp >= cutoff
    ]

    total = len(records)
    if total == 0:
        return SLAResult(
            rule=rule,
            total=0,
            critical_count=0,
            critical_ratio=0.0,
            breached=False,
        )

    critical_count = sum(
        1 for r in records if r.status == MetricStatus.CRITICAL
    )
    ratio = critical_count / total
    return SLAResult(
        rule=rule,
        total=total,
        critical_count=critical_count,
        critical_ratio=ratio,
        breached=ratio > rule.max_critical_ratio,
    )


def scan_sla(rules: List[SLARule], history: MetricHistory) -> List[SLAResult]:
    """Evaluate all SLA rules and return results (skipping invalid rules)."""
    results = []
    for rule in rules:
        result = check_sla(rule, history)
        if result is not None:
            results.append(result)
    return results
