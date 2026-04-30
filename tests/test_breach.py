"""Tests for pipewatch.breach."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from pipewatch.breach import BreachResult, detect_breach, scan_breaches
from pipewatch.metrics import Metric, MetricStatus, MetricThreshold


def _m(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


def _fake_history(name: str, values: list) -> MagicMock:
    now = time.time()
    records = [_m(name, v) for v in values]
    history = MagicMock()
    history.for_name.return_value = records
    return history


@pytest.fixture
def threshold() -> MetricThreshold:
    return MetricThreshold(warning=80.0, critical=95.0)


def test_detect_breach_returns_none_for_empty_history(threshold):
    history = _fake_history("cpu", [])
    result = detect_breach("cpu", history, threshold, min_breaches=3)
    assert result is None


def test_detect_breach_returns_none_for_insufficient_history(threshold):
    history = _fake_history("cpu", [90.0, 91.0])  # only 2 records, min=3
    result = detect_breach("cpu", history, threshold, min_breaches=3)
    assert result is None


def test_detect_breach_not_breaching(threshold):
    history = _fake_history("cpu", [10.0, 20.0, 30.0, 40.0])
    result = detect_breach("cpu", history, threshold, min_breaches=3)
    assert result is not None
    assert result.is_breaching is False
    assert result.consecutive_breaches == 0


def test_detect_breach_warning_level(threshold):
    # Last 3 values all above warning (80) but below critical (95)
    history = _fake_history("cpu", [10.0, 82.0, 83.0, 84.0])
    result = detect_breach("cpu", history, threshold, min_breaches=3)
    assert result is not None
    assert result.is_breaching is True
    assert result.level == "warning"
    assert result.consecutive_breaches == 3


def test_detect_breach_critical_level(threshold):
    # Last 3 values all above critical (95)
    history = _fake_history("cpu", [10.0, 96.0, 97.0, 98.0])
    result = detect_breach("cpu", history, threshold, min_breaches=3)
    assert result is not None
    assert result.is_breaching is True
    assert result.level == "critical"
    assert result.threshold == 95.0


def test_detect_breach_interrupted_streak(threshold):
    # Streak broken by a low value at the end
    history = _fake_history("cpu", [90.0, 91.0, 92.0, 10.0])
    result = detect_breach("cpu", history, threshold, min_breaches=3)
    assert result is not None
    assert result.is_breaching is False


def test_detect_breach_invalid_min_raises(threshold):
    history = _fake_history("cpu", [90.0, 91.0, 92.0])
    with pytest.raises(ValueError):
        detect_breach("cpu", history, threshold, min_breaches=0)


def test_breach_result_to_dict(threshold):
    history = _fake_history("cpu", [96.0, 97.0, 98.0])
    result = detect_breach("cpu", history, threshold, min_breaches=3)
    d = result.to_dict()
    assert d["name"] == "cpu"
    assert d["is_breaching"] is True
    assert "recent_values" in d
    assert "consecutive_breaches" in d


def test_scan_breaches_returns_all_results(threshold):
    history = MagicMock()
    history.for_name.side_effect = lambda name: [
        _m(name, 97.0), _m(name, 98.0), _m(name, 99.0)
    ]
    results = scan_breaches(["cpu", "mem"], history, threshold, min_breaches=3)
    assert len(results) == 2
    assert all(r.is_breaching for r in results)
