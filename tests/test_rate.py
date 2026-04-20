"""Tests for pipewatch.rate module."""
from datetime import datetime, timedelta
from typing import List

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.rate import RateResult, compute_rate, scan_rates


def _m(name: str, value: float, offset_seconds: float = 0.0) -> Metric:
    return Metric(
        name=name,
        value=value,
        status=MetricStatus.OK,
        timestamp=datetime(2024, 1, 1, 12, 0, 0) + timedelta(seconds=offset_seconds),
    )


def test_compute_rate_returns_none_for_empty():
    assert compute_rate([]) is None


def test_compute_rate_returns_none_for_single():
    assert compute_rate([_m("cpu", 50.0)]) is None


def test_compute_rate_returns_none_for_zero_period():
    t = datetime(2024, 1, 1, 12, 0, 0)
    m1 = Metric(name="cpu", value=10.0, status=MetricStatus.OK, timestamp=t)
    m2 = Metric(name="cpu", value=20.0, status=MetricStatus.OK, timestamp=t)
    assert compute_rate([m1, m2]) is None


def test_compute_rate_basic():
    records = [_m("cpu", 10.0, 0), _m("cpu", 70.0, 60)]
    result = compute_rate(records)
    assert result is not None
    assert result.name == "cpu"
    assert result.period_seconds == pytest.approx(60.0)
    assert result.start_value == pytest.approx(10.0)
    assert result.end_value == pytest.approx(70.0)
    assert result.absolute_change == pytest.approx(60.0)
    assert result.rate_per_second == pytest.approx(1.0)
    assert result.rate_per_minute == pytest.approx(60.0)
    assert result.pct_change == pytest.approx(600.0)


def test_compute_rate_pct_change_none_when_start_zero():
    records = [_m("cpu", 0.0, 0), _m("cpu", 5.0, 10)]
    result = compute_rate(records)
    assert result is not None
    assert result.pct_change is None


def test_compute_rate_orders_by_timestamp():
    # Pass records in reverse order; result should still use earliest as start.
    records = [_m("cpu", 80.0, 120), _m("cpu", 20.0, 0)]
    result = compute_rate(records)
    assert result.start_value == pytest.approx(20.0)
    assert result.end_value == pytest.approx(80.0)


def test_to_dict_keys():
    records = [_m("q", 1.0, 0), _m("q", 3.0, 30)]
    d = compute_rate(records).to_dict()
    expected_keys = {
        "name", "period_seconds", "start_value", "end_value",
        "absolute_change", "rate_per_second", "rate_per_minute", "pct_change",
    }
    assert set(d.keys()) == expected_keys


def test_scan_rates_multiple_metrics():
    grouped = {
        "cpu": [_m("cpu", 10.0, 0), _m("cpu", 20.0, 60)],
        "mem": [_m("mem", 100.0, 0), _m("mem", 150.0, 60)],
    }
    results = scan_rates(grouped)
    assert len(results) == 2
    names = {r.name for r in results}
    assert names == {"cpu", "mem"}


def test_scan_rates_skips_insufficient_data():
    grouped = {
        "cpu": [_m("cpu", 10.0, 0), _m("cpu", 20.0, 60)],
        "mem": [_m("mem", 100.0, 0)],  # only one record
    }
    results = scan_rates(grouped)
    assert len(results) == 1
    assert results[0].name == "cpu"
