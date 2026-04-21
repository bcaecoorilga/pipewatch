"""Tests for pipewatch.replay."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.replay import ReplayEvent, ReplayResult, replay


def _metric(name: str, value: float, ts: float) -> Metric:
    return Metric(name=name, value=value, timestamp=ts)


@pytest.fixture()
def history():
    """Return a mock MetricHistory with canned records."""
    now = time.time()
    records = [
        _metric("latency", 10.0, now - 30),
        _metric("latency", 85.0, now - 20),
        _metric("latency", 150.0, now - 10),
    ]
    mock = MagicMock()
    mock.for_name.return_value = records
    return mock, records, now


def test_replay_no_threshold_all_ok(history):
    mock, records, _ = history
    result = replay(mock, name="latency")
    assert result.total == 3
    assert all(ev.status == MetricStatus.OK for ev in result.events)


def test_replay_with_warn_threshold(history):
    mock, records, _ = history
    result = replay(mock, name="latency", warn=80.0)
    statuses = [ev.status for ev in result.events]
    assert statuses[0] == MetricStatus.OK
    assert statuses[1] == MetricStatus.WARNING
    assert statuses[2] == MetricStatus.WARNING


def test_replay_with_crit_threshold(history):
    mock, records, _ = history
    result = replay(mock, name="latency", warn=80.0, crit=120.0)
    statuses = [ev.status for ev in result.events]
    assert statuses[0] == MetricStatus.OK
    assert statuses[1] == MetricStatus.WARNING
    assert statuses[2] == MetricStatus.CRITICAL


def test_replay_since_filters_records(history):
    mock, records, now = history
    # Only last two records are after now-25
    mock.for_name.return_value = records
    result = replay(mock, name="latency", since=now - 25)
    assert result.total == 2


def test_replay_empty_history():
    mock = MagicMock()
    mock.for_name.return_value = []
    result = replay(mock, name="missing")
    assert result.total == 0
    assert result.status_counts == {"ok": 0, "warning": 0, "critical": 0}


def test_replay_to_dict(history):
    mock, _, _ = history
    result = replay(mock, name="latency", warn=80.0, crit=120.0)
    d = result.to_dict()
    assert d["name"] == "latency"
    assert d["total"] == 3
    assert "status_counts" in d
    assert len(d["events"]) == 3
    assert "timestamp" in d["events"][0]
