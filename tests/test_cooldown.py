"""Tests for pipewatch.cooldown."""
from datetime import datetime, timedelta

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.cooldown import CooldownTracker, CooldownResult


def _m(name: str, value: float, status: MetricStatus, offset_seconds: float = 0.0) -> Metric:
    ts = datetime(2024, 1, 1, 12, 0, 0) + timedelta(seconds=offset_seconds)
    return Metric(name=name, value=value, status=status, timestamp=ts)


@pytest.fixture
def tracker() -> CooldownTracker:
    return CooldownTracker(threshold_seconds=60.0)


def test_invalid_threshold_raises():
    with pytest.raises(ValueError):
        CooldownTracker(threshold_seconds=0)


def test_ok_metric_returns_none(tracker):
    m = _m("cpu", 10.0, MetricStatus.OK)
    assert tracker.update(m) is None


def test_first_bad_metric_returns_none(tracker):
    m = _m("cpu", 95.0, MetricStatus.WARNING)
    assert tracker.update(m) is None


def test_bad_metric_below_threshold_not_escalated(tracker):
    tracker.update(_m("cpu", 95.0, MetricStatus.WARNING, offset_seconds=0))
    result = tracker.update(_m("cpu", 96.0, MetricStatus.WARNING, offset_seconds=30))
    assert result is not None
    assert not result.escalated
    assert result.duration_seconds == pytest.approx(30.0)


def test_bad_metric_at_threshold_escalated(tracker):
    tracker.update(_m("cpu", 95.0, MetricStatus.CRITICAL, offset_seconds=0))
    result = tracker.update(_m("cpu", 97.0, MetricStatus.CRITICAL, offset_seconds=60))
    assert result is not None
    assert result.escalated
    assert result.name == "cpu"
    assert result.threshold_seconds == 60.0


def test_ok_clears_bad_since(tracker):
    tracker.update(_m("cpu", 95.0, MetricStatus.WARNING, offset_seconds=0))
    tracker.update(_m("cpu", 10.0, MetricStatus.OK, offset_seconds=10))
    # After OK, a new warning should restart the clock
    tracker.update(_m("cpu", 95.0, MetricStatus.WARNING, offset_seconds=20))
    result = tracker.update(_m("cpu", 96.0, MetricStatus.WARNING, offset_seconds=200))
    assert result is not None
    assert result.duration_seconds == pytest.approx(180.0)


def test_reset_clears_timer(tracker):
    tracker.update(_m("cpu", 95.0, MetricStatus.WARNING, offset_seconds=0))
    tracker.reset("cpu")
    # After reset, next bad record starts fresh
    assert tracker.update(_m("cpu", 96.0, MetricStatus.WARNING, offset_seconds=200)) is None


def test_scan_returns_only_escalated(tracker):
    metrics = [
        _m("a", 99.0, MetricStatus.CRITICAL, offset_seconds=0),
        _m("b", 99.0, MetricStatus.CRITICAL, offset_seconds=0),
    ]
    tracker.scan(metrics)  # seed bad_since

    later = [
        _m("a", 99.0, MetricStatus.CRITICAL, offset_seconds=90),  # escalated
        _m("b", 99.0, MetricStatus.CRITICAL, offset_seconds=30),  # not yet
    ]
    results = tracker.scan(later)
    assert len(results) == 1
    assert results[0].name == "a"


def test_to_dict_keys(tracker):
    tracker.update(_m("mem", 80.0, MetricStatus.WARNING, offset_seconds=0))
    result = tracker.update(_m("mem", 82.0, MetricStatus.WARNING, offset_seconds=120))
    assert result is not None
    d = result.to_dict()
    assert set(d.keys()) == {"name", "status", "bad_since", "duration_seconds", "threshold_seconds", "escalated"}
    assert d["escalated"] is True
