"""Tests for pipewatch.deduplicator."""

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.deduplicator import Deduplicator, DeduplicationResult


def _m(name: str, value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status)


@pytest.fixture
def dedup() -> Deduplicator:
    return Deduplicator()


def test_first_record_is_not_duplicate(dedup):
    result = dedup.check(_m("latency", 1.0))
    assert result.is_duplicate is False
    assert result.previous_value is None
    assert result.suppressed_count == 0


def test_same_value_is_duplicate(dedup):
    dedup.check(_m("latency", 1.0))
    result = dedup.check(_m("latency", 1.0))
    assert result.is_duplicate is True
    assert result.suppressed_count == 1


def test_duplicate_count_increments(dedup):
    dedup.check(_m("latency", 1.0))
    dedup.check(_m("latency", 1.0))
    result = dedup.check(_m("latency", 1.0))
    assert result.is_duplicate is True
    assert result.suppressed_count == 2


def test_different_value_resets_duplicate(dedup):
    dedup.check(_m("latency", 1.0))
    dedup.check(_m("latency", 1.0))  # duplicate
    result = dedup.check(_m("latency", 2.5))
    assert result.is_duplicate is False
    assert result.previous_value == 1.0
    assert result.current_value == 2.5


def test_tolerance_treats_close_values_as_duplicate():
    dedup = Deduplicator(tolerance=0.05)
    dedup.check(_m("cpu", 50.0))
    result = dedup.check(_m("cpu", 50.03))
    assert result.is_duplicate is True


def test_tolerance_distinguishes_values_outside_range():
    dedup = Deduplicator(tolerance=0.05)
    dedup.check(_m("cpu", 50.0))
    result = dedup.check(_m("cpu", 50.1))
    assert result.is_duplicate is False


def test_status_change_is_not_duplicate(dedup):
    dedup.check(_m("cpu", 80.0, MetricStatus.OK))
    result = dedup.check(_m("cpu", 80.0, MetricStatus.WARNING))
    assert result.is_duplicate is False


def test_reset_clears_single_metric(dedup):
    dedup.check(_m("latency", 1.0))
    dedup.reset("latency")
    result = dedup.check(_m("latency", 1.0))
    assert result.is_duplicate is False
    assert result.previous_value is None


def test_reset_all_clears_cache(dedup):
    dedup.check(_m("a", 1.0))
    dedup.check(_m("b", 2.0))
    dedup.reset_all()
    assert dedup.check(_m("a", 1.0)).is_duplicate is False
    assert dedup.check(_m("b", 2.0)).is_duplicate is False


def test_to_dict_shape(dedup):
    dedup.check(_m("q", 5.0))
    result = dedup.check(_m("q", 5.0))
    d = result.to_dict()
    assert set(d.keys()) == {"metric_name", "is_duplicate", "previous_value", "current_value", "suppressed_count"}
