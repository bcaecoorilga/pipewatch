"""Tests for pipewatch.plateau plateau detection."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.plateau import PlateauResult, detect_plateau, scan_plateaus


def _m(name: str = "cpu", value: float = 1.0) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


def _fake_history(name: str, values: list, base_ts: datetime | None = None):
    """Build a mock MetricHistory whose for_name returns records."""
    if base_ts is None:
        base_ts = datetime(2024, 1, 1, 0, 0, 0)
    records = []
    for i, v in enumerate(values):
        r = MagicMock()
        r.value = v
        r.timestamp = base_ts + timedelta(seconds=i * 10)
        records.append(r)
    history = MagicMock()
    history.for_name.return_value = records
    return history


def test_detect_plateau_returns_none_for_insufficient_history():
    history = _fake_history("cpu", [1.0] * 5)
    result = detect_plateau("cpu", history, window=10)
    assert result is None


def test_detect_plateau_not_a_plateau():
    values = [float(i) for i in range(15)]  # 0..14 — wide range
    history = _fake_history("cpu", values)
    result = detect_plateau("cpu", history, window=10, tolerance=0.01)
    assert result is not None
    assert result.is_plateau is False
    assert result.range_value == pytest.approx(9.0)


def test_detect_plateau_is_plateau():
    values = [42.0] * 15  # perfectly flat
    history = _fake_history("cpu", values)
    result = detect_plateau("cpu", history, window=10, tolerance=0.01)
    assert result is not None
    assert result.is_plateau is True
    assert result.range_value == pytest.approx(0.0)


def test_detect_plateau_within_tolerance():
    values = [10.0, 10.001, 9.999, 10.002, 10.0] * 3  # tiny jitter
    history = _fake_history("cpu", values)
    result = detect_plateau("cpu", history, window=10, tolerance=0.01)
    assert result is not None
    assert result.is_plateau is True


def test_plateau_to_dict_keys():
    values = [5.0] * 12
    history = _fake_history("mem", values)
    result = detect_plateau("mem", history, window=10, tolerance=0.05)
    d = result.to_dict()
    for key in ("name", "window", "min_value", "max_value", "range_value", "threshold", "is_plateau", "duration_seconds"):
        assert key in d


def test_scan_plateaus_deduplicates_by_name():
    metrics = [_m("cpu", 1.0), _m("cpu", 2.0), _m("mem", 3.0)]
    values_flat = [1.0] * 15
    history = MagicMock()
    history.for_name.return_value = [
        MagicMock(value=v, timestamp=datetime(2024, 1, 1) + timedelta(seconds=i * 5))
        for i, v in enumerate(values_flat)
    ]
    results = scan_plateaus(metrics, history, window=10)
    names = [r.name for r in results]
    assert len(names) == len(set(names))  # no duplicates


def test_scan_plateaus_returns_empty_when_insufficient_history():
    metrics = [_m("cpu")]
    history = MagicMock()
    history.for_name.return_value = []  # no records
    results = scan_plateaus(metrics, history, window=10)
    assert results == []
