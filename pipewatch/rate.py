"""Rate-of-change analysis for pipeline metrics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.metrics import Metric


@dataclass
class RateResult:
    name: str
    period_seconds: float
    start_value: float
    end_value: float
    absolute_change: float
    rate_per_second: float
    rate_per_minute: float
    pct_change: Optional[float]  # None when start_value == 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "period_seconds": round(self.period_seconds, 3),
            "start_value": self.start_value,
            "end_value": self.end_value,
            "absolute_change": round(self.absolute_change, 6),
            "rate_per_second": round(self.rate_per_second, 6),
            "rate_per_minute": round(self.rate_per_minute, 6),
            "pct_change": round(self.pct_change, 4) if self.pct_change is not None else None,
        }


def compute_rate(records: List[Metric]) -> Optional[RateResult]:
    """Compute rate of change between the oldest and newest record.

    Returns None if fewer than 2 records are provided or the time
    span between them is zero.
    """
    if len(records) < 2:
        return None

    ordered = sorted(records, key=lambda m: m.timestamp)
    first, last = ordered[0], ordered[-1]

    period = (last.timestamp - first.timestamp).total_seconds()
    if period == 0:
        return None

    absolute_change = last.value - first.value
    rate_per_second = absolute_change / period
    rate_per_minute = rate_per_second * 60
    pct_change = (absolute_change / first.value * 100) if first.value != 0 else None

    return RateResult(
        name=last.name,
        period_seconds=period,
        start_value=first.value,
        end_value=last.value,
        absolute_change=absolute_change,
        rate_per_second=rate_per_second,
        rate_per_minute=rate_per_minute,
        pct_change=pct_change,
    )


def scan_rates(records_by_name: dict[str, List[Metric]]) -> List[RateResult]:
    """Compute rate results for every metric name present."""
    results = []
    for records in records_by_name.values():
        result = compute_rate(records)
        if result is not None:
            results.append(result)
    return results
