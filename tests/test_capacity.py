"""Tests for pipewatch.capacity and pipewatch.exporter_capacity."""
from __future__ import annotations

import time
from unittest.mock import patch, MagicMock

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.capacity import estimate_capacity, scan_capacity, CapacityResult
from pipewatch.exporter_capacity import export_capacity_json, export_capacity_csv
from pipewatch.forecast import ForecastResult


def _make_forecast(last_value: float, slope: float, predicted: list[float]) -> ForecastResult:
    return ForecastResult(
        metric_name="test",
        last_value=last_value,
        slope=slope,
        intercept=0.0,
        predicted_values=predicted,
        confidence=0.9,
        steps=len(predicted),
    )


def test_estimate_capacity_returns_none_when_no_forecast():
    history = MagicMock()
    with patch("pipewatch.capacity.forecast", return_value=None):
        result = estimate_capacity(history, "cpu", threshold=90.0)
    assert result is None


def test_estimate_capacity_finds_eta():
    predicted = [70.0, 80.0, 91.0, 95.0]
    mock_fr = _make_forecast(last_value=60.0, slope=10.0, predicted=predicted)
    history = MagicMock()
    with patch("pipewatch.capacity.forecast", return_value=mock_fr):
        result = estimate_capacity(history, "cpu", threshold=90.0, step_seconds=60.0)
    assert result is not None
    assert result.steps_to_threshold == 3
    assert result.eta_seconds == pytest.approx(180.0)
    assert result.current_value == 60.0


def test_estimate_capacity_never_reached():
    predicted = [50.0, 55.0, 58.0]
    mock_fr = _make_forecast(last_value=45.0, slope=5.0, predicted=predicted)
    history = MagicMock()
    with patch("pipewatch.capacity.forecast", return_value=mock_fr):
        result = estimate_capacity(history, "cpu", threshold=90.0, horizon_steps=3)
    assert result is not None
    assert result.steps_to_threshold is None
    assert result.eta_seconds is None


def test_estimate_capacity_falling_metric():
    """Falling metric should detect threshold crossing downward."""
    predicted = [40.0, 30.0, 19.0]
    mock_fr = _make_forecast(last_value=50.0, slope=-10.0, predicted=predicted)
    history = MagicMock()
    with patch("pipewatch.capacity.forecast", return_value=mock_fr):
        result = estimate_capacity(history, "queue", threshold=20.0, step_seconds=30.0)
    assert result is not None
    assert result.steps_to_threshold == 3
    assert result.eta_seconds == pytest.approx(90.0)


def test_scan_capacity_skips_missing_forecasts():
    history = MagicMock()
    thresholds = {"a": 100.0, "b": 200.0}
    with patch("pipewatch.capacity.forecast", return_value=None):
        results = scan_capacity(history, thresholds)
    assert results == []


def test_scan_capacity_returns_results():
    predicted = [95.0]
    mock_fr = _make_forecast(last_value=90.0, slope=5.0, predicted=predicted)
    history = MagicMock()
    thresholds = {"cpu": 94.0}
    with patch("pipewatch.capacity.forecast", return_value=mock_fr):
        results = scan_capacity(history, thresholds, horizon_steps=1)
    assert len(results) == 1
    assert results[0].metric_name == "cpu"


def test_export_capacity_json_valid():
    predicted = [91.0]
    mock_fr = _make_forecast(last_value=85.0, slope=6.0, predicted=predicted)
    r = CapacityResult(
        metric_name="mem",
        threshold=90.0,
        current_value=85.0,
        slope=6.0,
        steps_to_threshold=1,
        eta_seconds=60.0,
        horizon_steps=5,
        forecast_result=mock_fr,
    )
    import json
    data = json.loads(export_capacity_json([r]))
    assert data[0]["metric_name"] == "mem"
    assert data[0]["eta_seconds"] == 60.0


def test_export_capacity_csv_headers():
    csv_str = export_capacity_csv([])
    assert "metric_name" in csv_str
    assert "eta_seconds" in csv_str
    assert "slope" in csv_str
