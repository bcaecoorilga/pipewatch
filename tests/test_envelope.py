"""Tests for pipewatch.envelope."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.envelope import EnvelopeResult, detect_envelope, scan_envelopes


def _m(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, timestamp=datetime.now(timezone.utc))


class _FakeHistory:
    def __init__(self, records: list):
        self._records = records

    def for_name(self, name: str):
        return [r for r in self._records if r.name == name]


def _rec(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, timestamp=datetime.now(timezone.utc))


# --- detect_envelope ---

def test_detect_envelope_returns_none_for_empty_history():
    history = _FakeHistory([])
    result = detect_envelope(_m("cpu", 50.0), history, min_history=5)
    assert result is None


def test_detect_envelope_returns_none_for_insufficient_history():
    records = [_rec("cpu", 50.0)] * 3
    history = _FakeHistory(records)
    result = detect_envelope(_m("cpu", 50.0), history, min_history=5)
    assert result is None


def test_detect_envelope_returns_none_for_zero_tolerance():
    records = [_rec("cpu", 50.0)] * 6
    history = _FakeHistory(records)
    result = detect_envelope(_m("cpu", 50.0), history, tolerance=0.0)
    assert result is None


def test_detect_envelope_inside():
    records = [_rec("cpu", 100.0)] * 6
    history = _FakeHistory(records)
    result = detect_envelope(_m("cpu", 105.0), history, tolerance=0.2, min_history=5)
    assert result is not None
    assert result.inside is True
    assert result.deviation < 0  # negative means inside


def test_detect_envelope_outside_above():
    records = [_rec("cpu", 100.0)] * 6
    history = _FakeHistory(records)
    # 100 ± 20% => [80, 120]; value 150 is outside
    result = detect_envelope(_m("cpu", 150.0), history, tolerance=0.2, min_history=5)
    assert result is not None
    assert result.inside is False
    assert result.deviation > 0


def test_detect_envelope_outside_below():
    records = [_rec("cpu", 100.0)] * 6
    history = _FakeHistory(records)
    result = detect_envelope(_m("cpu", 50.0), history, tolerance=0.2, min_history=5)
    assert result is not None
    assert result.inside is False
    assert result.deviation < 0


def test_detect_envelope_to_dict_keys():
    records = [_rec("cpu", 100.0)] * 6
    history = _FakeHistory(records)
    result = detect_envelope(_m("cpu", 100.0), history, tolerance=0.1, min_history=5)
    assert result is not None
    d = result.to_dict()
    for key in ["name", "current_value", "mean", "lower_bound", "upper_bound", "tolerance", "inside", "deviation"]:
        assert key in d


# --- scan_envelopes ---

def test_scan_envelopes_returns_results_for_sufficient_history():
    records = [_rec("x", 10.0)] * 6 + [_rec("y", 20.0)] * 6
    history = _FakeHistory(records)
    metrics = [_m("x", 10.0), _m("y", 20.0)]
    results = scan_envelopes(metrics, history, tolerance=0.1, min_history=5)
    assert len(results) == 2


def test_scan_envelopes_skips_insufficient_history():
    records = [_rec("x", 10.0)] * 3  # only 3 records
    history = _FakeHistory(records)
    metrics = [_m("x", 10.0)]
    results = scan_envelopes(metrics, history, tolerance=0.1, min_history=5)
    assert results == []
