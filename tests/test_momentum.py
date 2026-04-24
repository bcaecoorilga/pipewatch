"""Tests for pipewatch.momentum."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.momentum import MomentumResult, detect_momentum, scan_momentums


def _m(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


def _fake_history(name: str, values: list[float]) -> MetricHistory:
    h = MetricHistory()
    base = datetime(2024, 1, 1, 12, 0, 0)
    records = []
    for i, v in enumerate(values):
        m = _m(name, v)
        m.timestamp = base + timedelta(seconds=i * 10)
        records.append(m)

    with patch.object(h, "for_name", return_value=records):
        yield h


@pytest.fixture()
def steady_history():
    yield from _fake_history("cpu", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])


@pytest.fixture()
def accelerating_history():
    # values grow by increasing amounts -> positive second derivative
    yield from _fake_history("cpu", [0.0, 1.0, 3.0, 6.0, 10.0, 15.0])


@pytest.fixture()
def decelerating_history():
    yield from _fake_history("cpu", [15.0, 10.0, 6.0, 3.0, 1.0, 0.0])


def test_detect_momentum_returns_none_for_insufficient_history():
    h = MetricHistory()
    with patch.object(h, "for_name", return_value=[]):
        result = detect_momentum("cpu", h)
    assert result is None


def test_detect_momentum_steady(steady_history):
    result = detect_momentum("cpu", steady_history, threshold=0.5)
    assert result is not None
    assert result.direction == "steady"
    assert result.is_significant is False


def test_detect_momentum_accelerating(accelerating_history):
    result = detect_momentum("cpu", accelerating_history, threshold=0.01)
    assert result is not None
    assert result.direction == "accelerating"
    assert result.is_significant is True
    assert result.momentum > 0


def test_detect_momentum_decelerating(decelerating_history):
    result = detect_momentum("cpu", decelerating_history, threshold=0.01)
    assert result is not None
    assert result.direction == "decelerating"
    assert result.is_significant is True
    assert result.momentum < 0


def test_to_dict_keys(accelerating_history):
    result = detect_momentum("cpu", accelerating_history)
    assert result is not None
    d = result.to_dict()
    assert set(d.keys()) == {"name", "momentum", "direction", "sample_count", "threshold", "is_significant"}


def test_scan_momentums_deduplicates(accelerating_history):
    metrics = [_m("cpu", 1.0), _m("cpu", 2.0)]  # duplicate name
    results = scan_momentums(metrics, accelerating_history, threshold=0.01)
    names = [r.name for r in results]
    assert names.count("cpu") == 1
