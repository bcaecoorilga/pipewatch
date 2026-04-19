"""Tests for pipewatch.forecast."""
import pytest
from unittest.mock import MagicMock
from pipewatch.forecast import forecast, ForecastResult, _linear_fit, _confidence
from pipewatch.metrics import Metric, MetricStatus
import datetime


def _rec(value: float, name: str = "cpu"):
    m = MagicMock()
    m.value = value
    m.name = name
    return m


def _history(records):
    h = MagicMock()
    h.for_name = MagicMock(return_value=records)
    return h


def test_forecast_returns_none_for_empty():
    h = _history([])
    assert forecast(h, "cpu") is None


def test_forecast_returns_none_for_single():
    h = _history([_rec(1.0)])
    assert forecast(h, "cpu") is None


def test_forecast_returns_result():
    h = _history([_rec(float(i)) for i in range(10)])
    result = forecast(h, "cpu", steps=3)
    assert isinstance(result, ForecastResult)
    assert result.name == "cpu"
    assert result.steps == 3
    assert len(result.predicted_values) == 3


def test_forecast_rising_trend():
    h = _history([_rec(float(i)) for i in range(10)])
    result = forecast(h, "cpu", steps=2)
    assert result.slope > 0
    assert result.predicted_values[1] > result.predicted_values[0]


def test_forecast_flat_trend():
    h = _history([_rec(5.0) for _ in range(6)])
    result = forecast(h, "cpu", steps=2)
    assert result.slope == 0.0
    assert all(abs(v - 5.0) < 1e-5 for v in result.predicted_values)


def test_confidence_levels():
    assert _confidence(1) == "low"
    assert _confidence(8) == "medium"
    assert _confidence(20) == "high"


def test_to_dict_keys():
    h = _history([_rec(float(i)) for i in range(5)])
    result = forecast(h, "mem", steps=2)
    d = result.to_dict()
    assert set(d.keys()) == {"name", "steps", "predicted_values", "slope", "intercept", "confidence"}


def test_linear_fit_known_values():
    slope, intercept = _linear_fit([0.0, 1.0, 2.0, 3.0])
    assert abs(slope - 1.0) < 1e-6
    assert abs(intercept) < 1e-6
