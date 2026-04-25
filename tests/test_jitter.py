"""Tests for pipewatch.jitter."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from pipewatch.jitter import JitterResult, detect_jitter, scan_jitter
from pipewatch.metrics import Metric, MetricStatus


def _m(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


def _fake_history(name: str, values: list) -> MagicMock:
    records = [_m(name, v) for v in values]
    h = MagicMock()
    h.for_name.return_value = records
    return h


# --- detect_jitter ---

def test_detect_jitter_returns_none_for_empty_history():
    h = _fake_history("cpu", [])
    assert detect_jitter("cpu", h) is None


def test_detect_jitter_returns_none_for_insufficient_history():
    h = _fake_history("cpu", [1.0, 2.0])
    assert detect_jitter("cpu", h) is None


def test_detect_jitter_returns_none_for_zero_mean():
    h = _fake_history("cpu", [0.0, 0.0, 0.0, 0.0, 0.0])
    assert detect_jitter("cpu", h) is None


def test_detect_jitter_not_jittery():
    # Very stable values → low CV
    values = [10.0, 10.1, 9.9, 10.05, 9.95, 10.0, 10.0, 10.0]
    h = _fake_history("cpu", values)
    result = detect_jitter("cpu", h, threshold_cv=0.3)
    assert result is not None
    assert result.is_jittery is False
    assert result.metric_name == "cpu"


def test_detect_jitter_is_jittery():
    # Wildly varying values → high CV
    values = [1.0, 100.0, 2.0, 90.0, 5.0, 80.0, 3.0, 70.0, 10.0, 60.0]
    h = _fake_history("latency", values)
    result = detect_jitter("latency", h, threshold_cv=0.3)
    assert result is not None
    assert result.is_jittery is True


def test_detect_jitter_respects_window():
    # First values are noisy; last 5 are stable
    noisy = [1.0, 100.0, 2.0, 90.0, 5.0]
    stable = [10.0, 10.1, 9.9, 10.0, 10.05]
    h = _fake_history("cpu", noisy + stable)
    result = detect_jitter("cpu", h, window=5, threshold_cv=0.3)
    assert result is not None
    assert result.window == 5
    assert result.is_jittery is False


def test_detect_jitter_to_dict():
    values = [10.0] * 10
    h = _fake_history("cpu", values)
    result = detect_jitter("cpu", h)
    assert result is not None
    d = result.to_dict()
    assert d["metric_name"] == "cpu"
    assert "mean" in d
    assert "std_dev" in d
    assert "cv" in d
    assert "is_jittery" in d


# --- scan_jitter ---

def test_scan_jitter_returns_results_for_all_metrics():
    values = [10.0, 10.1, 9.9, 10.05, 9.95]
    h = _fake_history("cpu", values)
    metrics = [_m("cpu", 10.0)]
    results = scan_jitter(metrics, h)
    assert len(results) == 1
    assert results[0].metric_name == "cpu"


def test_scan_jitter_deduplicates_metric_names():
    values = [10.0, 10.1, 9.9, 10.05, 9.95]
    h = _fake_history("cpu", values)
    metrics = [_m("cpu", 10.0), _m("cpu", 10.1)]
    results = scan_jitter(metrics, h)
    assert len(results) == 1


def test_scan_jitter_skips_insufficient_history():
    h = _fake_history("cpu", [1.0])
    metrics = [_m("cpu", 1.0)]
    results = scan_jitter(metrics, h)
    assert results == []
