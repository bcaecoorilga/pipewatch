"""Tests for pipewatch.saturation."""
from __future__ import annotations

import pytest
from pipewatch.saturation import (
    SaturationResult,
    detect_saturation,
    scan_saturations,
    _classify,
)
from pipewatch.metrics import Metric, MetricStatus


def _m(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


# --- _classify ---

def test_classify_ok():
    assert _classify(50.0, 75.0, 90.0) == "ok"


def test_classify_warning():
    assert _classify(80.0, 75.0, 90.0) == "warning"


def test_classify_critical():
    assert _classify(95.0, 75.0, 90.0) == "critical"


# --- detect_saturation ---

def test_detect_saturation_returns_none_for_zero_ceiling():
    m = _m("cpu", 80.0)
    assert detect_saturation(m, ceiling=0) is None


def test_detect_saturation_ok():
    m = _m("cpu", 50.0)
    result = detect_saturation(m, ceiling=100.0)
    assert result is not None
    assert result.saturation_pct == pytest.approx(50.0)
    assert result.label == "ok"
    assert result.is_saturated is False


def test_detect_saturation_warning():
    m = _m("cpu", 80.0)
    result = detect_saturation(m, ceiling=100.0, warn_pct=75.0, crit_pct=90.0)
    assert result is not None
    assert result.label == "warning"
    assert result.is_saturated is False


def test_detect_saturation_critical():
    m = _m("cpu", 95.0)
    result = detect_saturation(m, ceiling=100.0, warn_pct=75.0, crit_pct=90.0)
    assert result is not None
    assert result.label == "critical"
    assert result.is_saturated is True


def test_detect_saturation_to_dict():
    m = _m("mem", 60.0)
    result = detect_saturation(m, ceiling=100.0)
    d = result.to_dict()
    assert d["metric_name"] == "mem"
    assert d["ceiling"] == 100.0
    assert "saturation_pct" in d


# --- scan_saturations ---

def test_scan_saturations_skips_missing_ceiling():
    metrics = [_m("a", 50.0), _m("b", 80.0)]
    results = scan_saturations(metrics, ceilings={"a": 100.0})
    assert len(results) == 1
    assert results[0].metric_name == "a"


def test_scan_saturations_returns_all_with_ceilings():
    metrics = [_m("a", 50.0), _m("b", 80.0)]
    results = scan_saturations(metrics, ceilings={"a": 100.0, "b": 100.0})
    assert len(results) == 2


def test_scan_saturations_empty_metrics():
    results = scan_saturations([], ceilings={"a": 100.0})
    assert results == []
