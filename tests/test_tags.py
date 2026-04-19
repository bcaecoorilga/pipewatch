"""Tests for pipewatch.tags module."""
import pytest
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.tags import TagIndex, tag_summary


def _metric(name: str, value: float = 1.0) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


@pytest.fixture
def index() -> TagIndex:
    return TagIndex()


def test_add_and_get(index):
    m = _metric("cpu")
    index.add(m, ["infra", "system"])
    assert m in index.get("infra")
    assert m in index.get("system")


def test_get_unknown_tag_returns_empty(index):
    assert index.get("nonexistent") == []


def test_all_tags_sorted(index):
    m = _metric("cpu")
    index.add(m, ["zebra", "alpha", "middle"])
    assert index.all_tags() == ["alpha", "middle", "zebra"]


def test_filter_returns_tagged_metrics(index):
    m1 = _metric("cpu")
    m2 = _metric("memory")
    m3 = _metric("disk")
    index.add(m1, ["infra"])
    index.add(m2, ["infra"])
    index.add(m3, ["storage"])
    result = index.filter([m1, m2, m3], "infra")
    assert m1 in result
    assert m2 in result
    assert m3 not in result


def test_filter_empty_list(index):
    m = _metric("cpu")
    index.add(m, ["infra"])
    assert index.filter([], "infra") == []


def test_tag_summary(index):
    m1 = _metric("cpu")
    m2 = _metric("memory")
    m3 = _metric("disk")
    index.add(m1, ["infra"])
    index.add(m2, ["infra"])
    index.add(m3, ["storage"])
    summary = tag_summary(index, [m1, m2, m3])
    assert summary["infra"] == 2
    assert summary["storage"] == 1


def test_tag_summary_excludes_unmatched(index):
    m1 = _metric("cpu")
    m2 = _metric("memory")
    index.add(m1, ["infra"])
    index.add(m2, ["other"])
    summary = tag_summary(index, [m1])
    assert "other" not in summary
