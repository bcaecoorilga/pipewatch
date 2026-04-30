"""Tests for pipewatch.stagnation."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.stagnation import StagnationResult, detect_stagnation, scan_stagnations


def _m(name: str, value: float, offset: int = 0) -> Metric:
    return Metric(
        name=name,
        value=value,
        status=MetricStatus.OK,
        timestamp=datetime(2024, 1, 1, 0, 0, 0) + timedelta(seconds=offset),
    )


class _FakeHistory:
    def __init__(self, records: List[Metric]):
        self._records = records

    def for_name(self, name: str) -> List[Metric]:
        return [r for r in self._records if r.name == name]

    def all_names(self) -> List[str]:
        return list({r.name for r in self._records})


def test_detect_stagnation_returns_none_for_empty_history():
    history = _FakeHistory([])
    assert detect_stagnation("cpu", history) is None


def test_detect_stagnation_returns_none_for_single_record():
    history = _FakeHistory([_m("cpu", 50.0)])
    assert detect_stagnation("cpu", history) is None


def test_detect_stagnation_not_stagnant():
    records = [_m("cpu", float(i * 10), i) for i in range(10)]
    history = _FakeHistory(records)
    result = detect_stagnation("cpu", history, window=10, tolerance=0.0)
    assert result is not None
    assert result.is_stagnant is False
    assert result.spread == pytest.approx(90.0)


def test_detect_stagnation_is_stagnant_constant():
    records = [_m("cpu", 42.0, i) for i in range(10)]
    history = _FakeHistory(records)
    result = detect_stagnation("cpu", history, window=10, tolerance=0.0)
    assert result is not None
    assert result.is_stagnant is True
    assert result.spread == pytest.approx(0.0)
    assert result.unique_values == 1


def test_detect_stagnation_tolerance_respected():
    # values vary by 0.5 — stagnant when tolerance=1.0, not when tolerance=0.0
    records = [_m("cpu", 10.0 + (i % 2) * 0.5, i) for i in range(10)]
    history = _FakeHistory(records)
    result_strict = detect_stagnation("cpu", history, tolerance=0.0)
    result_loose = detect_stagnation("cpu", history, tolerance=1.0)
    assert result_strict is not None and result_strict.is_stagnant is False
    assert result_loose is not None and result_loose.is_stagnant is True


def test_detect_stagnation_window_limits_records():
    records = [_m("cpu", float(i), i) for i in range(20)]
    history = _FakeHistory(records)
    result = detect_stagnation("cpu", history, window=5, tolerance=0.0)
    assert result is not None
    assert result.window == 5
    assert result.min_value == pytest.approx(15.0)
    assert result.max_value == pytest.approx(19.0)


def test_scan_stagnations_returns_results_for_all_names():
    records = [
        _m("cpu", 50.0, 0), _m("cpu", 50.0, 1),
        _m("mem", 1.0, 0), _m("mem", 2.0, 1),
    ]
    history = _FakeHistory(records)
    results = scan_stagnations(history, tolerance=0.0)
    names = {r.metric_name for r in results}
    assert "cpu" in names
    assert "mem" in names


def test_stagnation_to_dict_keys():
    records = [_m("cpu", 1.0, i) for i in range(5)]
    history = _FakeHistory(records)
    result = detect_stagnation("cpu", history)
    assert result is not None
    d = result.to_dict()
    expected_keys = {"metric_name", "window", "unique_values", "min_value", "max_value", "spread", "is_stagnant", "tolerance"}
    assert expected_keys == set(d.keys())
