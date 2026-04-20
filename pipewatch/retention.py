"""Retention policy for metric history: prune old records based on age or count."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from pipewatch.history import MetricHistory, _load_raw, _save_raw


@dataclass
class RetentionPolicy:
    """Defines how long / how many records to keep."""

    max_age_hours: Optional[float] = None  # drop records older than this
    max_records: Optional[int] = None       # keep only the N most recent records

    def is_valid(self) -> bool:
        return self.max_age_hours is not None or self.max_records is not None


@dataclass
class PruneResult:
    metric_name: str
    records_before: int
    records_after: int

    @property
    def pruned(self) -> int:
        return self.records_before - self.records_after

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "records_before": self.records_before,
            "records_after": self.records_after,
            "pruned": self.pruned,
        }


def _apply_policy(records: list, policy: RetentionPolicy) -> list:
    """Return a filtered list of records according to the policy."""
    result = list(records)

    if policy.max_age_hours is not None:
        cutoff = datetime.utcnow() - timedelta(hours=policy.max_age_hours)
        result = [r for r in result if datetime.fromisoformat(r["timestamp"]) >= cutoff]

    if policy.max_records is not None and len(result) > policy.max_records:
        result = result[-policy.max_records :]

    return result


def prune(path: str, policy: RetentionPolicy) -> List[PruneResult]:
    """Apply *policy* to every metric stored at *path*. Returns prune results."""
    if not policy.is_valid():
        return []

    raw = _load_raw(path)  # dict[str, list[dict]]
    results: List[PruneResult] = []

    for name, records in raw.items():
        before = len(records)
        kept = _apply_policy(records, policy)
        raw[name] = kept
        results.append(PruneResult(metric_name=name, records_before=before, records_after=len(kept)))

    _save_raw(path, raw)
    return results
