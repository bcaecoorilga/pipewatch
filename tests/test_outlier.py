"""Tests for pipewatch.outlier module."""
from unittest.mock import MagicMock
from datetime import datetime, timedelta

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.outlier import OutlierResult, detect_outlier, scan_outliers


def _m(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


def _make_history(name: str, values):
    """Return a mocked MetricHistory whose for_name returns records."""
    history = MagicMock()
    base = datetime(2024, 1, 1, 12, 0, 0)
    records = [
        MagicMock(name=name, value=v, timestamp=base + timedelta(minutes=i))
        for i, v in enumerate(values)
    ]
    history.for_name.return_value = records
    return history


def test_detect_outlier_returns_none_for_empty_history():
    history = _make_history("cpu", [])
    result = detect_outlier(_m("cpu", 50.0), history)
    assert result is None


def test_detect_outlier_returns_none_for_insufficient_history():
    history = _make_history("cpu", [10, 20, 30])
    result = detect_outlier(_m("cpu", 50.0), history)
    assert result is None


def test_detect_outlier_not_outlier():
    values = [10, 20, 30, 40, 50, 60, 70, 80]
    history = _make_history("cpu", values)
    result = detect_outlier(_m("cpu", 45.0), history)
    assert result is not None
    assert isinstance(result, OutlierResult)
    assert result.is_outlier is False
    assert result.direction is None


def test_detect_outlier_high():
    values = [10, 11, 12, 13, 14, 15, 16, 17]
    history = _make_history("cpu", values)
    result = detect_outlier(_m("cpu", 999.0), history)
    assert result is not None
    assert result.is_outlier is True
    assert result.direction == "high"


def test_detect_outlier_low():
    values = [100, 101, 102, 103, 104, 105, 106, 107]
    history = _make_history("mem", values)
    result = detect_outlier(_m("mem", -500.0), history)
    assert result is not None
    assert result.is_outlier is True
    assert result.direction == "low"


def test_outlier_result_to_dict():
    values = [10, 20, 30, 40, 50, 60, 70, 80]
    history = _make_history("latency", values)
    result = detect_outlier(_m("latency", 45.0), history)
    d = result.to_dict()
    assert "name" in d
    assert "is_outlier" in d
    assert "direction" in d
    assert "iqr" in d


def test_scan_outliers_returns_list():
    values = [10, 11, 12, 13, 14, 15, 16, 17]
    history = MagicMock()
    base = datetime(2024, 1, 1)
    history.for_name.return_value = [
        MagicMock(value=v, timestamp=base + timedelta(minutes=i))
        for i, v in enumerate(values)
    ]
    metrics = [_m("cpu", 999.0), _m("mem", 12.0)]
    results = scan_outliers(metrics, history)
    assert len(results) == 2
    outlier_names = [r.name for r in results if r.is_outlier]
    assert "cpu" in outlier_names
