"""Tests for pipewatch.filter module."""

import pytest
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.tags import TagIndex
from pipewatch.filter import (
    filter_by_status,
    filter_by_name,
    filter_by_tag,
    apply_filters,
)


def _m(name: str, status: MetricStatus = MetricStatus.OK, value: float = 1.0) -> Metric:
    return Metric(name=name, value=value, status=status)


@pytest.fixture
def metrics():
    return [
        _m("pipeline.rows", MetricStatus.OK),
        _m("pipeline.lag", MetricStatus.WARNING),
        _m("pipeline.errors", MetricStatus.CRITICAL),
        _m("etl.duration", MetricStatus.OK),
    ]


def test_filter_by_status_ok(metrics):
    result = filter_by_status(metrics, MetricStatus.OK)
    assert len(result) == 2
    assert all(m.status == MetricStatus.OK for m in result)


def test_filter_by_status_critical(metrics):
    result = filter_by_status(metrics, MetricStatus.CRITICAL)
    assert len(result) == 1
    assert result[0].name == "pipeline.errors"


def test_filter_by_name_exact(metrics):
    result = filter_by_name(metrics, "pipeline.lag")
    assert len(result) == 1
    assert result[0].name == "pipeline.lag"


def test_filter_by_name_glob(metrics):
    result = filter_by_name(metrics, "pipeline.*")
    assert len(result) == 3


def test_filter_by_name_no_match(metrics):
    result = filter_by_name(metrics, "nonexistent.*")
    assert result == []


def test_filter_by_tag(metrics):
    index = TagIndex()
    index.add("etl", metrics[3])  # etl.duration
    result = filter_by_tag(metrics, "etl", index)
    assert len(result) == 1
    assert result[0].name == "etl.duration"


def test_apply_filters_combined(metrics):
    result = apply_filters(metrics, status=MetricStatus.OK, name_pattern="pipeline.*")
    assert len(result) == 1
    assert result[0].name == "pipeline.rows"


def test_apply_filters_no_filters(metrics):
    result = apply_filters(metrics)
    assert len(result) == len(metrics)
