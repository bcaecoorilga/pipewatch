"""Tests for pipewatch.heatmap."""
from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.heatmap import (
    HeatmapCell,
    HeatmapRow,
    Heatmap,
    _bucket_label,
    build_heatmap,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _ts(hour: int, minute: int = 0) -> float:
    """Return a UTC timestamp for today at the given hour:minute."""
    now = datetime.now(tz=timezone.utc)
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0).timestamp()


def _metric(name: str, value: float, status: MetricStatus, hour: int) -> Metric:
    return Metric(name=name, value=value, status=status, timestamp=_ts(hour))


def _fake_history(records: list) -> MagicMock:
    h = MagicMock()
    h.all.return_value = records
    return h


# ── unit tests ────────────────────────────────────────────────────────────────

def test_bucket_label_rounds_down():
    ts = datetime(2024, 6, 1, 14, 35, 0, tzinfo=timezone.utc)
    assert _bucket_label(ts, 1) == "2024-06-01T14"


def test_bucket_label_2h_bucket():
    ts = datetime(2024, 6, 1, 15, 10, 0, tzinfo=timezone.utc)
    assert _bucket_label(ts, 2) == "2024-06-01T14"


def test_build_heatmap_empty_history():
    hm = build_heatmap(_fake_history([]))
    assert hm.rows == []


def test_build_heatmap_single_ok_record():
    records = [_metric("cpu", 10.0, MetricStatus.OK, hour=8)]
    hm = build_heatmap(_fake_history(records))
    assert len(hm.rows) == 1
    assert hm.rows[0].name == "cpu"
    assert hm.rows[0].cells[0].status == MetricStatus.OK
    assert hm.rows[0].cells[0].count == 1


def test_build_heatmap_critical_dominates():
    records = [
        _metric("cpu", 10.0, MetricStatus.OK, hour=9),
        _metric("cpu", 90.0, MetricStatus.CRITICAL, hour=9),
        _metric("cpu", 50.0, MetricStatus.WARNING, hour=9),
    ]
    hm = build_heatmap(_fake_history(records))
    assert hm.rows[0].cells[0].status == MetricStatus.CRITICAL
    assert hm.rows[0].cells[0].count == 3


def test_build_heatmap_warning_dominates_ok():
    records = [
        _metric("mem", 20.0, MetricStatus.OK, hour=10),
        _metric("mem", 70.0, MetricStatus.WARNING, hour=10),
    ]
    hm = build_heatmap(_fake_history(records))
    assert hm.rows[0].cells[0].status == MetricStatus.WARNING


def test_build_heatmap_name_filter():
    records = [
        _metric("cpu", 10.0, MetricStatus.OK, hour=8),
        _metric("mem", 20.0, MetricStatus.WARNING, hour=8),
    ]
    hm = build_heatmap(_fake_history(records), names=["cpu"])
    assert len(hm.rows) == 1
    assert hm.rows[0].name == "cpu"


def test_heatmap_to_dict_structure():
    records = [_metric("cpu", 5.0, MetricStatus.OK, hour=7)]
    hm = build_heatmap(_fake_history(records))
    d = hm.to_dict()
    assert "rows" in d
    assert "bucket_size_hours" in d
    assert d["rows"][0]["name"] == "cpu"
    assert d["rows"][0]["cells"][0]["status"] == "ok"
