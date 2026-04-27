"""Tests for pipewatch.stepchange."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.stepchange import StepChangeResult, detect_step_change, scan_step_changes


def _m(name: str = "pipe.rows") -> Metric:
    return Metric(name=name, value=1.0, status=MetricStatus.OK)


def _fake_history(name: str, values: list) -> MagicMock:
    base = datetime(2024, 1, 1, 12, 0, 0)
    records = [
        MagicMock(name=name, value=v, timestamp=base + timedelta(minutes=i))
        for i, v in enumerate(values)
    ]
    h = MagicMock()
    h.for_name.return_value = records
    return h


def test_detect_step_change_returns_none_for_insufficient_history():
    h = _fake_history("pipe.rows", [1.0, 2.0, 3.0])  # only 3 records
    result = detect_step_change(_m(), h, min_records=6)
    assert result is None


def test_detect_step_change_returns_none_for_empty_history():
    h = _fake_history("pipe.rows", [])
    result = detect_step_change(_m(), h, min_records=6)
    assert result is None


def test_detect_step_change_not_a_step():
    # Stable values — no step change
    values = [10.0] * 12
    h = _fake_history("pipe.rows", values)
    result = detect_step_change(_m(), h, threshold_pct=0.20)
    assert result is not None
    assert result.detected is False
    assert abs(result.shift_magnitude) < 1e-9


def test_detect_step_change_is_detected():
    # Clear upward step: pre ~10, post ~20
    pre = [10.0] * 6
    post = [20.0] * 6
    h = _fake_history("pipe.rows", pre + post)
    result = detect_step_change(_m(), h, threshold_pct=0.20)
    assert result is not None
    assert result.detected is True
    assert result.pre_mean == pytest.approx(10.0)
    assert result.post_mean == pytest.approx(20.0)
    assert result.shift_magnitude == pytest.approx(10.0)
    assert result.shift_pct == pytest.approx(1.0)


def test_detect_step_change_downward():
    pre = [50.0] * 6
    post = [30.0] * 6
    h = _fake_history("pipe.rows", pre + post)
    result = detect_step_change(_m(), h, threshold_pct=0.20)
    assert result is not None
    assert result.detected is True
    assert result.shift_magnitude == pytest.approx(-20.0)


def test_step_change_to_dict_keys():
    pre = [10.0] * 6
    post = [20.0] * 6
    h = _fake_history("pipe.rows", pre + post)
    result = detect_step_change(_m(), h)
    d = result.to_dict()
    for key in ("metric_name", "detected", "pre_mean", "post_mean", "shift_magnitude", "shift_pct", "split_index", "record_count"):
        assert key in d


def test_scan_step_changes_returns_only_results_with_data():
    h = _fake_history("a", [10.0] * 6 + [20.0] * 6)
    h2 = MagicMock()
    h2.for_name.return_value = []  # no history for second metric

    combined = MagicMock()
    def _for_name(name):
        if name == "a":
            return h.for_name(name)
        return []
    combined.for_name.side_effect = _for_name

    metrics = [_m("a"), _m("b")]
    results = scan_step_changes(metrics, combined, min_records=6)
    # "b" returns None (no history), so only "a" is included
    assert len(results) == 1
    assert results[0].metric_name == "a"
