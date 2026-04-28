"""Tests for pipewatch.ewma."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.ewma import EWMAResult, _compute_ewma, detect_ewma, scan_ewma


def _m(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, timestamp=datetime.utcnow())


def _fake_history(name: str, values: list[float]) -> MagicMock:
    base = datetime.utcnow() - timedelta(seconds=len(values) * 10)
    records = [_m(name, v) for v in values]
    for i, r in enumerate(records):
        r.timestamp = base + timedelta(seconds=i * 10)
    mock = MagicMock()
    mock.for_name.return_value = records
    return mock


# --- _compute_ewma ---

def test_compute_ewma_single_value():
    assert _compute_ewma([5.0], alpha=0.3) == 5.0


def test_compute_ewma_constant_series():
    result = _compute_ewma([4.0, 4.0, 4.0, 4.0], alpha=0.5)
    assert result == pytest.approx(4.0)


def test_compute_ewma_rising_series():
    result = _compute_ewma([1.0, 2.0, 3.0, 4.0, 5.0], alpha=0.5)
    assert result > 1.0
    assert result < 5.0


def test_compute_ewma_empty_raises():
    with pytest.raises(ValueError):
        _compute_ewma([], alpha=0.3)


# --- detect_ewma ---

def test_detect_ewma_returns_none_for_insufficient_history():
    history = _fake_history("cpu", [1.0, 2.0, 3.0])  # only 3 records
    metric = _m("cpu", 3.0)
    result = detect_ewma(metric, history, min_records=5)
    assert result is None


def test_detect_ewma_returns_none_for_empty_history():
    history = _fake_history("cpu", [])
    metric = _m("cpu", 10.0)
    result = detect_ewma(metric, history, min_records=5)
    assert result is None


def test_detect_ewma_not_anomalous():
    values = [10.0, 10.1, 9.9, 10.0, 10.05, 10.0]
    history = _fake_history("cpu", values)
    metric = _m("cpu", values[-1])
    result = detect_ewma(metric, history, alpha=0.3, threshold=0.2, min_records=5)
    assert result is not None
    assert not result.is_anomalous
    assert result.name == "cpu"


def test_detect_ewma_is_anomalous():
    values = [10.0, 10.0, 10.0, 10.0, 10.0, 100.0]  # huge spike at end
    history = _fake_history("cpu", values)
    metric = _m("cpu", 100.0)
    result = detect_ewma(metric, history, alpha=0.3, threshold=0.2, min_records=5)
    assert result is not None
    assert result.is_anomalous
    assert result.relative_deviation > 0.2


def test_detect_ewma_invalid_alpha_raises():
    history = _fake_history("cpu", [1.0] * 6)
    metric = _m("cpu", 1.0)
    with pytest.raises(ValueError):
        detect_ewma(metric, history, alpha=0.0)


def test_detect_ewma_invalid_threshold_raises():
    history = _fake_history("cpu", [1.0] * 6)
    metric = _m("cpu", 1.0)
    with pytest.raises(ValueError):
        detect_ewma(metric, history, threshold=-0.1)


def test_detect_ewma_to_dict_keys():
    values = [5.0, 5.1, 4.9, 5.0, 5.05, 5.0]
    history = _fake_history("mem", values)
    metric = _m("mem", 5.0)
    result = detect_ewma(metric, history, alpha=0.3, threshold=0.2, min_records=5)
    assert result is not None
    d = result.to_dict()
    for key in ("name", "current_value", "ewma", "deviation", "relative_deviation", "is_anomalous", "alpha", "threshold"):
        assert key in d


# --- scan_ewma ---

def test_scan_ewma_skips_insufficient_history():
    history = _fake_history("cpu", [1.0, 2.0])  # too few
    metrics = [_m("cpu", 2.0)]
    results = scan_ewma(metrics, history, min_records=5)
    assert results == []


def test_scan_ewma_returns_results_for_sufficient_history():
    values = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
    history = _fake_history("cpu", values)
    metrics = [_m("cpu", 10.0)]
    results = scan_ewma(metrics, history, min_records=5)
    assert len(results) == 1
    assert isinstance(results[0], EWMAResult)
