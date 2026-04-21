"""Tests for pipewatch.spike."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.spike import SpikeResult, detect_spike, scan_spikes


def _m(name: str, value: float, ts: float | None = None) -> Metric:
    return Metric(
        name=name,
        value=value,
        timestamp=ts or time.time(),
        status=MetricStatus.OK,
        tags={},
    )


def _fake_history(records: list[Metric]):
    """Return a mock MetricHistory that returns *records* for any name."""
    h = MagicMock()
    h.for_name.side_effect = lambda name: [r for r in records if r.name == name]
    return h


# --- detect_spike ---

def test_detect_spike_returns_none_for_empty_history():
    history = _fake_history([])
    result = detect_spike(_m("cpu", 90.0), history)
    assert result is None


def test_detect_spike_returns_none_for_insufficient_history():
    records = [_m("cpu", 10.0), _m("cpu", 12.0)]
    history = _fake_history(records)
    result = detect_spike(_m("cpu", 90.0), history, min_history=3)
    assert result is None


def test_detect_spike_not_a_spike():
    base = [_m("cpu", v) for v in [10.0, 11.0, 10.5, 10.8]]
    history = _fake_history(base)
    current = _m("cpu", 11.2)
    result = detect_spike(current, history, threshold=2.0)
    assert result is not None
    assert result.is_spike is False
    assert result.direction == "none"


def test_detect_spike_upward():
    base = [_m("cpu", v) for v in [10.0, 10.0, 10.0, 10.0]]
    history = _fake_history(base)
    current = _m("cpu", 50.0)  # 400% jump
    result = detect_spike(current, history, threshold=2.0)
    assert result is not None
    assert result.is_spike is True
    assert result.direction == "up"
    assert result.relative_change == pytest.approx(4.0)


def test_detect_spike_downward():
    base = [_m("cpu", v) for v in [100.0, 100.0, 100.0, 100.0]]
    history = _fake_history(base)
    current = _m("cpu", 5.0)  # -95% drop
    result = detect_spike(current, history, threshold=0.5)
    assert result is not None
    assert result.is_spike is True
    assert result.direction == "down"


def test_detect_spike_zero_mean_returns_none():
    base = [_m("cpu", 0.0) for _ in range(5)]
    history = _fake_history(base)
    result = detect_spike(_m("cpu", 10.0), history)
    assert result is None


# --- to_dict ---

def test_spike_result_to_dict():
    r = SpikeResult(
        metric_name="cpu",
        current_value=50.0,
        reference_mean=10.0,
        deviation=40.0,
        relative_change=4.0,
        is_spike=True,
        direction="up",
    )
    d = r.to_dict()
    assert d["metric_name"] == "cpu"
    assert d["is_spike"] is True
    assert d["direction"] == "up"
    assert "relative_change" in d


# --- scan_spikes ---

def test_scan_spikes_returns_only_spikes():
    base_cpu = [_m("cpu", 10.0) for _ in range(5)]
    base_mem = [_m("mem", 50.0) for _ in range(5)]
    history = _fake_history(base_cpu + base_mem)

    metrics = [_m("cpu", 80.0), _m("mem", 52.0)]
    results = scan_spikes(metrics, history, threshold=2.0)
    names = [r.metric_name for r in results]
    assert "cpu" in names
    assert "mem" not in names


def test_scan_spikes_empty_metrics():
    history = _fake_history([])
    assert scan_spikes([], history) == []
