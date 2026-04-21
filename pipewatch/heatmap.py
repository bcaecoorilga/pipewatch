"""Heatmap: build a time-bucketed status grid for pipeline metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory


@dataclass
class HeatmapCell:
    bucket: str          # ISO-format hour string, e.g. "2024-01-15T14"
    status: MetricStatus
    count: int

    def to_dict(self) -> dict:
        return {"bucket": self.bucket, "status": self.status.value, "count": self.count}


@dataclass
class HeatmapRow:
    name: str
    cells: List[HeatmapCell] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"name": self.name, "cells": [c.to_dict() for c in self.cells]}


@dataclass
class Heatmap:
    rows: List[HeatmapRow] = field(default_factory=list)
    bucket_size_hours: int = 1

    def to_dict(self) -> dict:
        return {
            "bucket_size_hours": self.bucket_size_hours,
            "rows": [r.to_dict() for r in self.rows],
        }


def _bucket_label(ts: datetime, bucket_hours: int) -> str:
    """Round a timestamp down to the nearest bucket boundary."""
    hour = (ts.hour // bucket_hours) * bucket_hours
    return ts.replace(hour=hour, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H")


def build_heatmap(
    history: MetricHistory,
    names: Optional[List[str]] = None,
    bucket_hours: int = 1,
) -> Heatmap:
    """Build a heatmap from metric history.

    Args:
        history: MetricHistory instance to read records from.
        names: Optional list of metric names to include; all if None.
        bucket_hours: Width of each time bucket in hours.
    """
    all_records = history.all()
    if names:
        all_records = [r for r in all_records if r.name in names]

    grouped: Dict[str, Dict[str, List[MetricStatus]]] = {}
    for record in all_records:
        ts = datetime.fromtimestamp(record.timestamp, tz=timezone.utc)
        label = _bucket_label(ts, bucket_hours)
        grouped.setdefault(record.name, {}).setdefault(label, []).append(record.status)

    rows: List[HeatmapRow] = []
    for metric_name in sorted(grouped):
        buckets = grouped[metric_name]
        cells = []
        for bucket_label in sorted(buckets):
            statuses = buckets[bucket_label]
            # Worst status wins
            if MetricStatus.CRITICAL in statuses:
                dominant = MetricStatus.CRITICAL
            elif MetricStatus.WARNING in statuses:
                dominant = MetricStatus.WARNING
            else:
                dominant = MetricStatus.OK
            cells.append(HeatmapCell(bucket=bucket_label, status=dominant, count=len(statuses)))
        rows.append(HeatmapRow(name=metric_name, cells=cells))

    return Heatmap(rows=rows, bucket_size_hours=bucket_hours)
