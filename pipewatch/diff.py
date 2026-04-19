"""Snapshot diff: compare two snapshots and report metric changes."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pipewatch.snapshot import Snapshot


@dataclass
class MetricDiff:
    name: str
    old_value: Optional[float]
    new_value: Optional[float]
    old_status: Optional[str]
    new_status: Optional[str]

    @property
    def value_delta(self) -> Optional[float]:
        if self.old_value is not None and self.new_value is not None:
            return self.new_value - self.old_value
        return None

    @property
    def status_changed(self) -> bool:
        return self.old_status != self.new_status

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "value_delta": self.value_delta,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "status_changed": self.status_changed,
        }


@dataclass
class SnapshotDiff:
    snapshot_a_label: str
    snapshot_b_label: str
    diffs: List[MetricDiff] = field(default_factory=list)

    @property
    def changed(self) -> List[MetricDiff]:
        return [d for d in self.diffs if d.value_delta != 0 or d.status_changed]

    @property
    def status_changes(self) -> List[MetricDiff]:
        return [d for d in self.diffs if d.status_changed]

    def to_dict(self) -> dict:
        return {
            "snapshot_a": self.snapshot_a_label,
            "snapshot_b": self.snapshot_b_label,
            "diffs": [d.to_dict() for d in self.diffs],
            "total_changed": len(self.changed),
            "status_changes": len(self.status_changes),
        }


def diff_snapshots(a: Snapshot, b: Snapshot) -> SnapshotDiff:
    """Compare two snapshots and return a SnapshotDiff."""
    a_metrics: Dict[str, dict] = {m["name"]: m for m in a.to_dict()["metrics"]}
    b_metrics: Dict[str, dict] = {m["name"]: m for m in b.to_dict()["metrics"]}
    all_names = set(a_metrics) | set(b_metrics)

    diffs = []
    for name in sorted(all_names):
        ma = a_metrics.get(name)
        mb = b_metrics.get(name)
        diffs.append(MetricDiff(
            name=name,
            old_value=ma["value"] if ma else None,
            new_value=mb["value"] if mb else None,
            old_status=ma["status"] if ma else None,
            new_status=mb["status"] if mb else None,
        ))

    return SnapshotDiff(
        snapshot_a_label=a.label or str(a.timestamp),
        snapshot_b_label=b.label or str(b.timestamp),
        diffs=diffs,
    )
