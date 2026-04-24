"""Tests for pipewatch.seasonality."""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.seasonality import (
    detect_seasonality,
    scan_seasonality,
    SeasonalityResult,
    _classify_strength,
)


def _m(name: str, value: float, ts: datetime) -> Metric:
    return Metric(name=name, value=value, timestamp=ts, status=MetricStatus.OK)


def _fake_history(records: list) -> MetricHistory:
    h = MagicMock(spec=MetricHistory)
    all_names = {r.name for r in records}
    h.all.return_value = records
    h.for_name.side_effect = lambda n: [r for r in records if r.name == n]
    return h


# ── classify strength ────────────────────────────────────────────────────────

def test_classify_none():
    assert _classify_strength(0.1) == "none"


def test_classify_weak():
    assert _classify_strength(0.3) == "weak"


def test_classify_moderate():
    assert _classify_strength(0.5) == "moderate"


def test_classify_strong():
    assert _classify_strength(0.8) == "strong"


# ── detect_seasonality ───────────────────────────────────────────────────────

def test_detect_returns_none_for_insufficient_data():
    base = datetime(2024, 1, 1, 0, 0, 0)
    records = [_m("cpu", float(i), base + timedelta(hours=i)) for i in range(5)]
    h = _fake_history(records)
    result = detect_seasonality("cpu", h, min_records=12)
    assert result is None


def test_detect_returns_none_for_single_bucket():
    # All records fall in the same hour bucket
    base = datetime(2024, 1, 1, 3, 0, 0)
    records = [_m("cpu", float(i), base) for i in range(15)]
    h = _fake_history(records)
    result = detect_seasonality("cpu", h, min_records=12)
    assert result is None


def test_detect_flat_signal_not_seasonal():
    # Same value every hour => zero total variance
    base = datetime(2024, 1, 1, 0, 0, 0)
    records = [_m("cpu", 5.0, base + timedelta(hours=i)) for i in range(24)]
    h = _fake_history(records)
    result = detect_seasonality("cpu", h, period="hourly", min_records=12)
    assert result is not None
    assert result.is_seasonal is False
    assert result.strength == "none"


def test_detect_strong_hourly_seasonality():
    # Even hours: value=10, odd hours: value=1 => clear hourly pattern
    base = datetime(2024, 1, 1, 0, 0, 0)
    records = []
    for i in range(48):  # two full days
        value = 10.0 if i % 2 == 0 else 1.0
        records.append(_m("cpu", value, base + timedelta(hours=i)))
    h = _fake_history(records)
    result = detect_seasonality("cpu", h, period="hourly", min_records=12)
    assert result is not None
    assert result.is_seasonal is True
    assert result.strength in ("moderate", "strong")
    assert result.period == "hourly"


def test_detect_daily_seasonality():
    # Weekdays (Mon-Fri) value=100, weekends value=10
    base = datetime(2024, 1, 1)  # Monday
    records = []
    for i in range(28):  # 4 weeks
        day = base + timedelta(days=i)
        value = 10.0 if day.weekday() >= 5 else 100.0
        records.append(_m("load", value, day))
    h = _fake_history(records)
    result = detect_seasonality("load", h, period="daily", min_records=12)
    assert result is not None
    assert result.is_seasonal is True
    assert result.period == "daily"


def test_to_dict_keys():
    base = datetime(2024, 1, 1, 0, 0, 0)
    records = []
    for i in range(48):
        value = 10.0 if i % 2 == 0 else 1.0
        records.append(_m("cpu", value, base + timedelta(hours=i)))
    h = _fake_history(records)
    result = detect_seasonality("cpu", h, period="hourly", min_records=12)
    assert result is not None
    d = result.to_dict()
    assert set(d.keys()) == {"name", "period", "bucket_means", "variance_ratio", "is_seasonal", "strength"}


# ── scan_seasonality ─────────────────────────────────────────────────────────

def test_scan_returns_results_for_all_names():
    base = datetime(2024, 1, 1, 0, 0, 0)
    records = []
    for i in range(48):
        records.append(_m("a", float(i % 5), base + timedelta(hours=i)))
        records.append(_m("b", float(i % 3), base + timedelta(hours=i)))
    h = _fake_history(records)
    results = scan_seasonality(h, period="hourly", min_records=12)
    names = {r.name for r in results}
    assert "a" in names
    assert "b" in names


def test_scan_skips_insufficient_metrics():
    base = datetime(2024, 1, 1, 0, 0, 0)
    records = [_m("sparse", 1.0, base + timedelta(hours=i)) for i in range(3)]
    h = _fake_history(records)
    results = scan_seasonality(h, period="hourly", min_records=12)
    assert results == []
