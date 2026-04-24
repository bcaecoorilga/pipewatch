"""Tests for pipewatch.regression."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.regression import RegressionResult, detect_regression, scan_regressions


def _m(name: str, value: float, ts: datetime) -> Metric:
    return Metric(name=name, value=value, timestamp=ts, status=MetricStatus.OK)


def _fake_history(name: str, values: list[float], base_ts: datetime | None = None):
    if base_ts is None:
        base_ts = datetime(2024, 1, 1, 0, 0, 0)
    records = [
        _m(name, v, base_ts + timedelta(minutes=i)) for i, v in enumerate(values)
    ]
    history = MagicMock()
    history.for_name.return_value = records
    return history


def test_detect_regression_returns_none_for_insufficient_history():
    history = _fake_history("cpu", [1.0] * 10)  # need 25 by default
    result = detect_regression(history, "cpu")
    assert result is None


def test_detect_regression_returns_none_for_empty_history():
    history = _fake_history("cpu", [])
    result = detect_regression(history, "cpu")
    assert result is None


def test_detect_regression_not_regressed():
    # stable values — no regression
    values = [10.0] * 25
    history = _fake_history("cpu", values)
    result = detect_regression(history, "cpu", baseline_window=20, recent_window=5, threshold_pct=15.0)
    assert result is not None
    assert result.regressed is False
    assert abs(result.deviation_pct) < 1.0


def test_detect_regression_is_regressed():
    # baseline ~10, recent ~20 → +100% deviation
    baseline_vals = [10.0] * 20
    recent_vals = [20.0] * 5
    history = _fake_history("cpu", baseline_vals + recent_vals)
    result = detect_regression(history, "cpu", baseline_window=20, recent_window=5, threshold_pct=15.0)
    assert result is not None
    assert result.regressed is True
    assert result.deviation_pct > 15.0


def test_detect_regression_negative_deviation():
    baseline_vals = [100.0] * 20
    recent_vals = [50.0] * 5
    history = _fake_history("cpu", baseline_vals + recent_vals)
    result = detect_regression(history, "cpu", baseline_window=20, recent_window=5, threshold_pct=15.0)
    assert result is not None
    assert result.deviation_pct < -15.0
    assert result.regressed is True


def test_regression_result_to_dict():
    r = RegressionResult(
        name="cpu",
        mean_baseline=10.0,
        recent_mean=12.0,
        deviation_pct=20.0,
        regressed=True,
        threshold_pct=15.0,
    )
    d = r.to_dict()
    assert d["name"] == "cpu"
    assert d["regressed"] is True
    assert d["deviation_pct"] == 20.0


def test_scan_regressions_deduplicates_names():
    values = [10.0] * 20 + [25.0] * 5
    history = _fake_history("mem", values)
    metrics = [_m("mem", 25.0, datetime.now())] * 3  # duplicates
    results = scan_regressions(history, metrics, baseline_window=20, recent_window=5)
    names = [r.name for r in results]
    assert names.count("mem") == 1


def test_scan_regressions_returns_empty_for_no_metrics():
    history = MagicMock()
    results = scan_regressions(history, [])
    assert results == []
