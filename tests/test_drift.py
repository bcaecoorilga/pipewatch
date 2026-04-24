"""Tests for pipewatch.drift."""
from __future__ import annotations

import time
from typing import List

import pytest

from pipewatch.drift import DriftResult, detect_drift, scan_drifts
from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus


def _m(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


def _fake_history(name: str, values: List[float]) -> MetricHistory:
    h = MetricHistory()
    for i, v in enumerate(values):
        m = _m(name, v)
        m.timestamp = time.time() - (len(values) - i) * 10
        h.append(m)
    return h


def test_detect_drift_returns_none_for_insufficient_history():
    h = _fake_history("cpu", [1.0, 2.0, 3.0])
    result = detect_drift(h, "cpu", reference_window=10, current_window=5)
    assert result is None


def test_detect_drift_returns_none_for_empty_history():
    h = MetricHistory()
    result = detect_drift(h, "cpu")
    assert result is None


def test_detect_drift_not_drifted():
    values = [10.0] * 15  # flat signal
    h = _fake_history("cpu", values)
    result = detect_drift(h, "cpu", reference_window=10, current_window=5, threshold_pct=20.0)
    assert result is not None
    assert result.drifted is False
    assert result.drift_pct == pytest.approx(0.0, abs=1e-6)


def test_detect_drift_is_drifted():
    ref = [10.0] * 10
    cur = [20.0] * 5  # 100% drift
    h = _fake_history("cpu", ref + cur)
    result = detect_drift(h, "cpu", reference_window=10, current_window=5, threshold_pct=20.0)
    assert result is not None
    assert result.drifted is True
    assert result.drift_pct == pytest.approx(100.0, abs=1e-4)


def test_detect_drift_to_dict_keys():
    ref = [5.0] * 10
    cur = [6.0] * 5
    h = _fake_history("mem", ref + cur)
    result = detect_drift(h, "mem", reference_window=10, current_window=5)
    d = result.to_dict()
    for key in ("name", "reference_mean", "current_mean", "drift_abs", "drift_pct", "drifted", "threshold_pct"):
        assert key in d


def test_scan_drifts_deduplicates_names():
    values = [10.0] * 10 + [20.0] * 5
    h = _fake_history("cpu", values)
    metrics = [_m("cpu", 20.0), _m("cpu", 20.0)]  # duplicate
    results = scan_drifts(h, metrics, reference_window=10, current_window=5)
    names = [r.name for r in results]
    assert names.count("cpu") == 1


def test_scan_drifts_skips_insufficient_history():
    h = _fake_history("new_metric", [1.0, 2.0])
    metrics = [_m("new_metric", 2.0)]
    results = scan_drifts(h, metrics)
    assert results == []
