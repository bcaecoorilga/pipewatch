"""Quota enforcement: track metric emission counts over a rolling window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewatch.metrics import Metric


@dataclass
class QuotaRule:
    name: str
    max_records: int
    window_seconds: int

    def is_valid(self) -> bool:
        return self.max_records > 0 and self.window_seconds > 0


@dataclass
class QuotaResult:
    metric_name: str
    rule: QuotaRule
    count_in_window: int
    limit: int
    exceeded: bool
    window_start: datetime
    window_end: datetime

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "rule": self.rule.name,
            "count_in_window": self.count_in_window,
            "limit": self.limit,
            "exceeded": self.exceeded,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
        }


def check_quota(
    rule: QuotaRule,
    records: List[Metric],
    now: Optional[datetime] = None,
) -> Optional[QuotaResult]:
    """Return a QuotaResult for *rule* given a list of Metric records."""
    if not rule.is_valid():
        return None
    if not records:
        return None

    now = now or datetime.utcnow()
    window_start = now - timedelta(seconds=rule.window_seconds)
    in_window = [r for r in records if r.timestamp >= window_start]
    count = len(in_window)
    return QuotaResult(
        metric_name=records[0].name,
        rule=rule,
        count_in_window=count,
        limit=rule.max_records,
        exceeded=count > rule.max_records,
        window_start=window_start,
        window_end=now,
    )


def scan_quotas(
    rules: List[QuotaRule],
    records_by_name: Dict[str, List[Metric]],
    now: Optional[datetime] = None,
) -> List[QuotaResult]:
    """Run quota checks for every rule against the supplied metric buckets."""
    results: List[QuotaResult] = []
    for rule in rules:
        records = records_by_name.get(rule.name, [])
        result = check_quota(rule, records, now=now)
        if result is not None:
            results.append(result)
    return results
