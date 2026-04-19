"""Tests for trend analysis."""

import pytest

from pipewatch.trend import analyze, TrendResult


def _records(name, values):
    return [{"name": name, "value": v} for v in values]


def test_analyze_empty_returns_none():
    assert analyze([]) is None


def test_analyze_single_value():
    result = analyze(_records("cpu", [42.0]))
    assert isinstance(result, TrendResult)
    assert result.mean == 42.0
    assert result.trend == "stable"


def test_analyze_rising():
    result = analyze(_records("cpu", [1.0, 2.0, 3.0, 4.0]))
    assert result.trend == "rising"


def test_analyze_falling():
    result = analyze(_records("cpu", [4.0, 3.0, 2.0, 1.0]))
    assert result.trend == "falling"


def test_analyze_stable():
    result = analyze(_records("cpu", [3.0, 1.0, 3.0, 1.0]))
    assert result.trend == "stable"


def test_analyze_mean_and_bounds():
    result = analyze(_records("latency", [2.0, 4.0, 6.0]))
    assert result.mean == 4.0
    assert result.min_value == 2.0
    assert result.max_value == 6.0
    assert result.count == 3


def test_to_dict_keys():
    result = analyze(_records("x", [1.0, 2.0]))
    d = result.to_dict()
    assert set(d.keys()) == {"name", "count", "mean", "min", "max", "trend"}
