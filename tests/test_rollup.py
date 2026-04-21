"""Tests for pipewatch.rollup."""
from datetime import datetime, timezone, timedelta

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.rollup import rollup, rollup_by_name, _window_label


def _m(name: str, value: float, ts: datetime) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, timestamp=ts)


BASE = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# _window_label
# ---------------------------------------------------------------------------

def test_window_label_aligns_to_bucket():
    ts = BASE + timedelta(seconds=42)
    label = _window_label(ts, window_seconds=300)
    assert label == "2024-01-15T12:00"


def test_window_label_next_bucket():
    ts = BASE + timedelta(seconds=300)
    label = _window_label(ts, window_seconds=300)
    assert label == "2024-01-15T12:05"


# ---------------------------------------------------------------------------
# rollup
# ---------------------------------------------------------------------------

def test_rollup_empty_returns_empty():
    assert rollup([]) == []


def test_rollup_single_metric():
    metrics = [_m("cpu", 0.5, BASE)]
    windows = rollup(metrics, window_seconds=300)
    assert len(windows) == 1
    assert "cpu" in windows[0].results
    assert windows[0].results["cpu"].count == 1


def test_rollup_groups_into_windows():
    m1 = _m("cpu", 0.3, BASE + timedelta(seconds=10))
    m2 = _m("cpu", 0.5, BASE + timedelta(seconds=60))
    m3 = _m("cpu", 0.9, BASE + timedelta(seconds=400))  # next window
    windows = rollup([m1, m2, m3], window_seconds=300)
    assert len(windows) == 2
    assert windows[0].results["cpu"].count == 2
    assert windows[1].results["cpu"].count == 1


def test_rollup_computes_mean():
    m1 = _m("mem", 100.0, BASE)
    m2 = _m("mem", 200.0, BASE + timedelta(seconds=10))
    windows = rollup([m1, m2], window_seconds=300)
    assert windows[0].results["mem"].mean == pytest.approx(150.0)


def test_rollup_multiple_metrics_in_same_window():
    m1 = _m("cpu", 0.4, BASE)
    m2 = _m("mem", 512.0, BASE + timedelta(seconds=5))
    windows = rollup([m1, m2], window_seconds=300)
    assert len(windows) == 1
    assert "cpu" in windows[0].results
    assert "mem" in windows[0].results


def test_rollup_window_to_dict_keys():
    windows = rollup([_m("x", 1.0, BASE)], window_seconds=300)
    d = windows[0].to_dict()
    assert {"label", "start", "end", "results"} == set(d.keys())


# ---------------------------------------------------------------------------
# rollup_by_name
# ---------------------------------------------------------------------------

def test_rollup_by_name_groups_correctly():
    m1 = _m("cpu", 0.2, BASE)
    m2 = _m("mem", 256.0, BASE + timedelta(seconds=1))
    m3 = _m("cpu", 0.8, BASE + timedelta(seconds=400))
    by_name = rollup_by_name([m1, m2, m3], window_seconds=300)
    assert "cpu" in by_name
    assert "mem" in by_name
    assert len(by_name["cpu"]) == 2
    assert len(by_name["mem"]) == 1


def test_rollup_by_name_empty():
    assert rollup_by_name([]) == {}
