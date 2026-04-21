"""Time-based metric rollup: aggregate metrics into fixed time windows."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pipewatch.metrics import Metric
from pipewatch.aggregator import AggregateResult, aggregate


@dataclass
class RollupWindow:
    label: str          # e.g. "2024-01-15T12:00"
    start: datetime
    end: datetime
    results: Dict[str, AggregateResult] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "results": {name: r.to_dict() for name, r in self.results.items()},
        }


def _window_label(ts: datetime, window_seconds: int) -> str:
    """Return a truncated ISO label for the window bucket containing *ts*."""
    epoch = int(ts.timestamp())
    bucket = (epoch // window_seconds) * window_seconds
    dt = datetime.fromtimestamp(bucket, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M")


def rollup(
    metrics: List[Metric],
    window_seconds: int = 300,
) -> List[RollupWindow]:
    """Group *metrics* into fixed time windows and aggregate each group.

    Args:
        metrics: Flat list of :class:`~pipewatch.metrics.Metric` records.
        window_seconds: Width of each bucket in seconds (default 5 min).

    Returns:
        Ordered list of :class:`RollupWindow` objects, oldest first.
    """
    if not metrics:
        return []

    # Bucket metrics by (window_label, metric_name)
    buckets: Dict[str, Dict[str, List[Metric]]] = {}
    for m in metrics:
        ts = m.timestamp if m.timestamp else datetime.now(tz=timezone.utc)
        label = _window_label(ts, window_seconds)
        buckets.setdefault(label, {}).setdefault(m.name, []).append(m)

    windows: List[RollupWindow] = []
    for label in sorted(buckets.keys()):
        # Reconstruct start/end from label
        start = datetime.fromisoformat(label).replace(tzinfo=timezone.utc)
        from datetime import timedelta
        end = start + timedelta(seconds=window_seconds)
        win = RollupWindow(label=label, start=start, end=end)
        for name, group in buckets[label].items():
            result = aggregate(group)
            if result is not None:
                win.results[name] = result
        windows.append(win)

    return windows


def rollup_by_name(metrics: List[Metric], window_seconds: int = 300) -> Dict[str, List[RollupWindow]]:
    """Return rollup windows keyed by metric name."""
    all_windows = rollup(metrics, window_seconds)
    by_name: Dict[str, List[RollupWindow]] = {}
    for win in all_windows:
        for name in win.results:
            by_name.setdefault(name, []).append(win)
    return by_name
