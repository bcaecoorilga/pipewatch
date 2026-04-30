"""Tests for pipewatch.flap."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from pipewatch.flap import FlapResult, detect_flap, scan_flaps
from pipewatch.metrics import Metric, MetricStatus


def _m(name: str, value: float, status: MetricStatus) -> Metric:
    m = Metric(name=name, value=value)
    m.status = status
    return m


def _fake_history(records_by_name: dict):
    history = MagicMock()
    history.for_name.side_effect = lambda name: records_by_name.get(name, [])
    return history


def test_detect_flap_returns_none_for_empty_history():
    history = _fake_history({})
    assert detect_flap("cpu", history) is None


def test_detect_flap_returns_none_for_single_record():
    history = _fake_history({"cpu": [_m("cpu", 1.0, MetricStatus.OK)]})
    assert detect_flap("cpu", history) is None


def test_detect_flap_not_flapping():
    records = [_m("cpu", float(i), MetricStatus.OK) for i in range(10)]
    history = _fake_history({"cpu": records})
    result = detect_flap("cpu", history, window=10, min_transitions=4)
    assert result is not None
    assert result.flapping is False
    assert result.transitions == 0


def test_detect_flap_is_flapping():
    statuses = [MetricStatus.OK, MetricStatus.WARNING] * 5
    records = [_m("cpu", float(i), s) for i, s in enumerate(statuses)]
    history = _fake_history({"cpu": records})
    result = detect_flap("cpu", history, window=10, min_transitions=4)
    assert result is not None
    assert result.flapping is True
    assert result.transitions == 9


def test_detect_flap_respects_window():
    stable = [_m("cpu", 1.0, MetricStatus.OK)] * 20
    flapping_tail = [_m("cpu", float(i), MetricStatus.OK if i % 2 == 0 else MetricStatus.CRITICAL) for i in range(6)]
    records = stable + flapping_tail
    history = _fake_history({"cpu": records})
    result = detect_flap("cpu", history, window=6, min_transitions=4)
    assert result is not None
    assert result.window == 6
    assert result.flapping is True


def test_scan_flaps_returns_all_results():
    ok_records = [_m("disk", 1.0, MetricStatus.OK)] * 5
    flap_records = [_m("mem", float(i), MetricStatus.OK if i % 2 == 0 else MetricStatus.WARNING) for i in range(10)]
    history = _fake_history({"disk": ok_records, "mem": flap_records})
    results = scan_flaps(["disk", "mem"], history, window=10, min_transitions=4)
    assert len(results) == 2
    names = {r.name for r in results}
    assert "disk" in names
    assert "mem" in names


def test_flap_result_to_dict():
    r = FlapResult(name="cpu", transitions=5, window=10, flapping=True, statuses=["ok", "warning"])
    d = r.to_dict()
    assert d["name"] == "cpu"
    assert d["transitions"] == 5
    assert d["flapping"] is True
    assert d["statuses"] == ["ok", "warning"]
