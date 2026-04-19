"""Tests for pipewatch.aggregator."""

import pytest
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.aggregator import aggregate, aggregate_by_name, AggregateResult


def _m(name, value, status=MetricStatus.OK):
    return Metric(name=name, value=value, status=status)


def test_aggregate_empty_returns_none():
    assert aggregate([]) is None


def test_aggregate_single():
    result = aggregate([_m("cpu", 42.0)])
    assert result.count == 1
    assert result.mean == 42.0
    assert result.min == 42.0
    assert result.max == 42.0
    assert result.latest == 42.0


def test_aggregate_mean():
    metrics = [_m("cpu", 10.0), _m("cpu", 20.0), _m("cpu", 30.0)]
    result = aggregate(metrics)
    assert result.mean == 20.0
    assert result.min == 10.0
    assert result.max == 30.0
    assert result.latest == 30.0


def test_aggregate_status_counts():
    metrics = [
        _m("cpu", 10.0, MetricStatus.OK),
        _m("cpu", 80.0, MetricStatus.WARNING),
        _m("cpu", 95.0, MetricStatus.CRITICAL),
        _m("cpu", 20.0, MetricStatus.OK),
    ]
    result = aggregate(metrics)
    assert result.status_counts["ok"] == 2
    assert result.status_counts["warning"] == 1
    assert result.status_counts["critical"] == 1


def test_aggregate_by_name_groups_correctly():
    metrics = [
        _m("cpu", 10.0),
        _m("mem", 50.0),
        _m("cpu", 20.0),
        _m("mem", 60.0),
    ]
    results = aggregate_by_name(metrics)
    assert set(results.keys()) == {"cpu", "mem"}
    assert results["cpu"].count == 2
    assert results["mem"].mean == 55.0


def test_aggregate_to_dict():
    result = aggregate([_m("cpu", 50.0)])
    d = result.to_dict()
    assert d["name"] == "cpu"
    assert d["count"] == 1
    assert "mean" in d
    assert "status_counts" in d
