"""Tests for pipewatch.noise."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.noise import detect_noise, scan_noise, _classify


def _m(name: str = "cpu") -> Metric:
    return Metric(name=name, value=0.0, status=MetricStatus.OK)


class _FakeHistory:
    def __init__(self, values):
        self._values = values

    def for_name(self, name):
        now = datetime.utcnow()
        records = []
        for i, v in enumerate(self._values):
            m = Metric(name=name, value=v, status=MetricStatus.OK)
            m.timestamp = now - timedelta(seconds=len(self._values) - i)
            records.append(m)
        return records


def test_detect_noise_returns_none_for_empty_history():
    history = _FakeHistory([])
    result = detect_noise(_m(), history, min_records=5)
    assert result is None


def test_detect_noise_returns_none_for_insufficient_history():
    history = _FakeHistory([1.0, 2.0, 3.0])
    result = detect_noise(_m(), history, min_records=5)
    assert result is None


def test_detect_noise_returns_none_for_zero_mean():
    history = _FakeHistory([0.0, 0.0, 0.0, 0.0, 0.0])
    result = detect_noise(_m(), history, min_records=5)
    assert result is None


def test_detect_noise_clean_metric():
    history = _FakeHistory([10.0, 10.1, 9.9, 10.0, 10.05])
    result = detect_noise(_m(), history, min_records=5, cv_threshold=0.1)
    assert result is not None
    assert result.noisy is False
    assert result.label == "clean"
    assert result.cv < 0.1


def test_detect_noise_noisy_metric():
    history = _FakeHistory([1.0, 5.0, 1.0, 8.0, 2.0, 9.0])
    result = detect_noise(_m(), history, min_records=5, cv_threshold=0.1)
    assert result is not None
    assert result.noisy is True
    assert result.label in ("noisy", "very_noisy")


def test_classify_clean():
    assert _classify(0.05) == "clean"


def test_classify_noisy():
    assert _classify(0.2) == "noisy"


def test_classify_very_noisy():
    assert _classify(0.5) == "very_noisy"


def test_to_dict_keys():
    history = _FakeHistory([1.0, 2.0, 3.0, 4.0, 5.0])
    result = detect_noise(_m(), history, min_records=5)
    assert result is not None
    d = result.to_dict()
    assert set(d.keys()) == {"name", "mean", "std_dev", "cv", "noisy", "label"}


def test_scan_noise_returns_results_for_all_metrics():
    history = _FakeHistory([1.0, 2.0, 3.0, 4.0, 5.0])
    metrics = [_m("a"), _m("b")]
    results = scan_noise(metrics, history, min_records=5)
    assert len(results) == 2
    assert {r.name for r in results} == {"a", "b"}


def test_scan_noise_skips_insufficient_history():
    history = _FakeHistory([1.0, 2.0])
    metrics = [_m("x")]
    results = scan_noise(metrics, history, min_records=5)
    assert results == []
