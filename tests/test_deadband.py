"""Tests for pipewatch.deadband."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.deadband import DeadbandResult, detect_deadband, scan_deadbands
from pipewatch.metrics import Metric, MetricStatus


def _m(name: str = "cpu") -> Metric:
    return Metric(name=name, value=0.0, status=MetricStatus.OK)


def _fake_history(name: str, values: list) -> MagicMock:
    now = datetime.utcnow()
    records = [
        MagicMock(name=name, value=v, timestamp=now + timedelta(seconds=i))
        for i, v in enumerate(values)
    ]
    history = MagicMock()
    history.for_name.return_value = records
    return history


def test_detect_deadband_returns_none_for_empty_history():
    history = _fake_history("cpu", [])
    result = detect_deadband(_m(), history, deadband=1.0)
    assert result is None


def test_detect_deadband_returns_none_for_single_record():
    history = _fake_history("cpu", [42.0])
    result = detect_deadband(_m(), history, deadband=1.0)
    assert result is None


def test_detect_deadband_returns_none_for_zero_deadband():
    history = _fake_history("cpu", [10.0, 12.0])
    result = detect_deadband(_m(), history, deadband=0)
    assert result is None


def test_detect_deadband_within_band():
    history = _fake_history("cpu", [10.0, 10.5])
    result = detect_deadband(_m(), history, deadband=1.0)
    assert result is not None
    assert result.within_deadband is True
    assert result.delta == pytest.approx(0.5)


def test_detect_deadband_outside_band():
    history = _fake_history("cpu", [10.0, 15.0])
    result = detect_deadband(_m(), history, deadband=1.0)
    assert result is not None
    assert result.within_deadband is False
    assert result.delta == pytest.approx(5.0)


def test_detect_deadband_percent_change_computed():
    history = _fake_history("cpu", [100.0, 110.0])
    result = detect_deadband(_m(), history, deadband=5.0)
    assert result is not None
    assert result.percent_change == pytest.approx(10.0)


def test_detect_deadband_percent_change_none_when_previous_zero():
    history = _fake_history("cpu", [0.0, 5.0])
    result = detect_deadband(_m(), history, deadband=1.0)
    assert result is not None
    assert result.percent_change is None


def test_deadband_result_to_dict():
    history = _fake_history("cpu", [50.0, 52.0])
    result = detect_deadband(_m("cpu"), history, deadband=5.0)
    assert result is not None
    d = result.to_dict()
    assert d["metric_name"] == "cpu"
    assert d["within_deadband"] is True
    assert "delta" in d
    assert "percent_change" in d


def test_scan_deadbands_returns_results_for_all_metrics():
    metrics = [_m("cpu"), _m("mem")]
    history = MagicMock()
    now = datetime.utcnow()
    history.for_name.return_value = [
        MagicMock(value=10.0, timestamp=now),
        MagicMock(value=11.0, timestamp=now + timedelta(seconds=1)),
    ]
    results = scan_deadbands(metrics, history, deadband=2.0)
    assert len(results) == 2
    assert all(isinstance(r, DeadbandResult) for r in results)


def test_scan_deadbands_skips_insufficient_history():
    metrics = [_m("cpu")]
    history = MagicMock()
    history.for_name.return_value = [MagicMock(value=5.0)]
    results = scan_deadbands(metrics, history, deadband=1.0)
    assert results == []
