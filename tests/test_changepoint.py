"""Tests for pipewatch.changepoint."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.changepoint import (
    ChangepointResult,
    _best_split,
    _mean,
    detect_changepoint,
    scan_changepoints,
)
from pipewatch.metrics import Metric, MetricStatus


def _m(name: str = "m") -> Metric:
    return Metric(name=name, value=0.0, status=MetricStatus.OK)


def _fake_history(values: list[float], name: str = "m"):
    """Build a mock MetricHistory whose for_name returns records."""
    now = datetime(2024, 1, 1, 12, 0, 0)
    records = [
        Metric(name=name, value=v, status=MetricStatus.OK,
               timestamp=now + timedelta(minutes=i))
        for i, v in enumerate(values)
    ]
    history = MagicMock()
    history.for_name.return_value = records
    return history


def test_mean_empty():
    assert _mean([]) == 0.0


def test_mean_values():
    assert _mean([1.0, 2.0, 3.0]) == pytest.approx(2.0)


def test_best_split_finds_obvious_break():
    # clear shift at index 4
    values = [1.0, 1.0, 1.0, 1.0, 10.0, 10.0, 10.0, 10.0]
    idx = _best_split(values)
    assert idx == 4


def test_detect_changepoint_returns_none_for_insufficient_history():
    history = _fake_history([1.0, 2.0])  # only 2 records
    result = detect_changepoint("m", history, min_records=6)
    assert result is None


def test_detect_changepoint_returns_none_for_empty_history():
    history = _fake_history([])
    result = detect_changepoint("m", history, min_records=6)
    assert result is None


def test_detect_changepoint_not_detected():
    # flat series — no real shift
    values = [5.0] * 10
    history = _fake_history(values)
    result = detect_changepoint("m", history, min_records=6, threshold_pct=0.15)
    assert result is not None
    assert result.detected is False
    assert result.delta == pytest.approx(0.0, abs=1e-9)


def test_detect_changepoint_detected():
    # obvious step: 1→10
    values = [1.0, 1.0, 1.0, 1.0, 10.0, 10.0, 10.0, 10.0]
    history = _fake_history(values)
    result = detect_changepoint("m", history, min_records=6, threshold_pct=0.15)
    assert result is not None
    assert result.detected is True
    assert result.changepoint_index == 4
    assert result.before_mean == pytest.approx(1.0)
    assert result.after_mean == pytest.approx(10.0)


def test_detect_changepoint_to_dict():
    values = [1.0, 1.0, 1.0, 1.0, 10.0, 10.0, 10.0, 10.0]
    history = _fake_history(values)
    result = detect_changepoint("m", history)
    d = result.to_dict()
    assert d["metric_name"] == "m"
    assert "before_mean" in d
    assert "after_mean" in d
    assert "detected" in d


def test_scan_changepoints_deduplicates_by_name():
    values = [1.0, 1.0, 1.0, 1.0, 10.0, 10.0, 10.0, 10.0]
    history = _fake_history(values, name="dup")
    metrics = [_m("dup"), _m("dup")]  # same name twice
    results = scan_changepoints(metrics, history)
    assert len(results) == 1


def test_scan_changepoints_skips_insufficient():
    history = _fake_history([1.0, 2.0], name="tiny")
    metrics = [_m("tiny")]
    results = scan_changepoints(metrics, history, min_records=6)
    assert results == []
