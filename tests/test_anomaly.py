"""Tests for pipewatch.anomaly module."""
import pytest
from pipewatch.anomaly import detect_anomaly, scan_anomalies, AnomalyResult
from pipewatch.metrics import Metric, MetricStatus
from datetime import datetime


def _m(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, timestamp=datetime.utcnow())


def test_detect_anomaly_returns_none_for_single_history():
    current = _m("latency", 100.0)
    history = [_m("latency", 95.0)]
    result = detect_anomaly(current, history)
    assert result is None


def test_detect_anomaly_returns_none_for_empty_history():
    current = _m("latency", 100.0)
    result = detect_anomaly(current, [])
    assert result is None


def test_detect_anomaly_not_anomalous():
    history = [_m("latency", v) for v in [100, 102, 98, 101, 99]]
    current = _m("latency", 100.5)
    result = detect_anomaly(current, history)
    assert result is not None
    assert result.is_anomaly is False
    assert result.name == "latency"


def test_detect_anomaly_is_anomalous():
    history = [_m("latency", v) for v in [100, 102, 98, 101, 99]]
    current = _m("latency", 999.0)
    result = detect_anomaly(current, history, z_threshold=2.5)
    assert result is not None
    assert result.is_anomaly is True
    assert result.z_score > 2.5


def test_detect_anomaly_zero_stddev():
    history = [_m("cpu", 50.0), _m("cpu", 50.0), _m("cpu", 50.0)]
    current = _m("cpu", 50.0)
    result = detect_anomaly(current, history)
    assert result is not None
    assert result.z_score == 0.0
    assert result.is_anomaly is False


def test_anomaly_result_to_dict():
    history = [_m("rps", v) for v in [200, 210, 190, 205]]
    current = _m("rps", 800.0)
    result = detect_anomaly(current, history)
    d = result.to_dict()
    assert d["name"] == "rps"
    assert "z_score" in d
    assert "is_anomaly" in d
    assert d["is_anomaly"] is True


def test_scan_anomalies_filters_by_name():
    history = [
        _m("latency", 100), _m("latency", 102), _m("latency", 98),
        _m("rps", 200), _m("rps", 210), _m("rps", 195),
    ]
    current = [_m("latency", 500.0), _m("rps", 205.0)]
    results = scan_anomalies(current, history)
    names = [r.name for r in results]
    assert "latency" in names
    assert "rps" in names
    latency_result = next(r for r in results if r.name == "latency")
    assert latency_result.is_anomaly is True
    rps_result = next(r for r in results if r.name == "rps")
    assert rps_result.is_anomaly is False
