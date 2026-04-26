"""Tests for pipewatch.throttle."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.throttle import ThrottleResult, detect_throttle, scan_throttles


def _m(name: str = "m") -> Metric:
    return Metric(name=name, value=1.0, status=MetricStatus.OK)


def _fake_history(values: list, base_ts: float = 1_000_000.0, step: float = 10.0):
    records = []
    for i, v in enumerate(values):
        r = MagicMock()
        r.value = v
        r.timestamp = base_ts + i * step
        records.append(r)
    h = MagicMock()
    h.all.return_value = records
    return h


def test_detect_throttle_returns_none_for_empty_history():
    h = _fake_history([])
    assert detect_throttle("cpu", h, ceiling=1.0) is None


def test_detect_throttle_returns_none_for_single_record():
    h = _fake_history([5.0])
    assert detect_throttle("cpu", h, ceiling=1.0) is None


def test_detect_throttle_returns_none_for_zero_ceiling():
    h = _fake_history([1.0, 2.0, 3.0])
    assert detect_throttle("cpu", h, ceiling=0.0) is None


def test_detect_throttle_not_throttled():
    # 3 records, each 10 s apart, values change by 0.1 each step → rate = 0.01/s
    h = _fake_history([10.0, 10.1, 10.2], step=10.0)
    result = detect_throttle("cpu", h, ceiling=1.0, window_seconds=60.0)
    assert isinstance(result, ThrottleResult)
    assert result.throttled is False
    assert result.current_rate == pytest.approx(0.01, rel=1e-3)
    assert result.ratio < 1.0


def test_detect_throttle_is_throttled():
    # values jump by 100 each 10 s → rate = 10/s, ceiling = 1/s
    h = _fake_history([0.0, 100.0, 200.0], step=10.0)
    result = detect_throttle("cpu", h, ceiling=1.0, window_seconds=60.0)
    assert result is not None
    assert result.throttled is True
    assert result.current_rate == pytest.approx(10.0, rel=1e-3)
    assert result.ratio == pytest.approx(10.0, rel=1e-3)
    assert "exceeds" in result.message


def test_detect_throttle_to_dict_keys():
    h = _fake_history([0.0, 50.0, 100.0], step=10.0)
    result = detect_throttle("x", h, ceiling=1.0)
    d = result.to_dict()
    assert set(d.keys()) == {"name", "current_rate", "ceiling", "throttled", "ratio", "message"}


def test_scan_throttles_returns_list():
    metrics = [_m("a"), _m("b")]
    h = _fake_history([0.0, 50.0, 100.0], step=10.0)
    results = scan_throttles(metrics, h, ceiling=1.0)
    assert len(results) == 2
    assert all(isinstance(r, ThrottleResult) for r in results)


def test_scan_throttles_empty_metrics():
    h = _fake_history([0.0, 50.0, 100.0], step=10.0)
    assert scan_throttles([], h, ceiling=1.0) == []
