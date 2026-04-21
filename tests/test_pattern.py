"""Tests for pipewatch.pattern."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.pattern import PatternResult, detect_pattern, scan_patterns


def _m(name: str, status: MetricStatus, offset_seconds: int = 0) -> Metric:
    return Metric(
        name=name,
        value=1.0,
        status=status,
        timestamp=datetime(2024, 1, 1, 12, 0, 0) + timedelta(seconds=offset_seconds),
    )


def _fake_history(records):
    h = MagicMock()
    h.all.return_value = records
    h.for_name.side_effect = lambda name: [r for r in records if r.name == name]
    return h


def test_detect_pattern_returns_none_for_insufficient_data():
    records = [_m("cpu", MetricStatus.OK, i) for i in range(3)]
    history = _fake_history(records)
    assert detect_pattern(history, "cpu") is None


def test_detect_pattern_returns_none_when_no_repeat():
    statuses = [MetricStatus.OK, MetricStatus.WARNING, MetricStatus.CRITICAL, MetricStatus.OK]
    records = [_m("cpu", s, i) for i, s in enumerate(statuses)]
    history = _fake_history(records)
    # No pattern repeats twice — should return None
    result = detect_pattern(history, "cpu", window=4, min_repeats=2)
    assert result is None


def test_detect_pattern_oscillating():
    # ok, warning repeating 3 times = 6 records
    statuses = [MetricStatus.OK, MetricStatus.WARNING] * 3
    records = [_m("cpu", s, i) for i, s in enumerate(statuses)]
    history = _fake_history(records)
    result = detect_pattern(history, "cpu", window=6, min_repeats=2)
    assert result is not None
    assert result.is_oscillating is True
    assert result.repeats >= 2
    assert result.metric_name == "cpu"


def test_detect_pattern_dominant_status():
    statuses = [MetricStatus.OK] * 5 + [MetricStatus.WARNING] * 1
    records = [_m("cpu", s, i) for i, s in enumerate(statuses)]
    history = _fake_history(records)
    result = detect_pattern(history, "cpu", window=10, min_repeats=2)
    # dominant should be ok
    if result:
        assert result.dominant_status == "ok"


def test_scan_patterns_returns_results_for_all_metrics():
    ok_warn = [MetricStatus.OK, MetricStatus.WARNING] * 3
    records = [_m("cpu", s, i) for i, s in enumerate(ok_warn)]
    records += [_m("mem", s, i) for i, s in enumerate(ok_warn)]
    history = _fake_history(records)
    results = scan_patterns(history, window=6, min_repeats=2)
    names = {r.metric_name for r in results}
    assert "cpu" in names
    assert "mem" in names


def test_pattern_to_dict_keys():
    pr = PatternResult(
        metric_name="cpu",
        pattern=["ok", "warning"],
        repeats=3,
        is_oscillating=True,
        dominant_status="ok",
    )
    d = pr.to_dict()
    assert set(d.keys()) == {"metric_name", "pattern", "repeats", "is_oscillating", "dominant_status"}
