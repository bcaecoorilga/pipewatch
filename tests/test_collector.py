"""Tests for the MetricCollector."""

import pytest
from pipewatch.collector import MetricCollector
from pipewatch.metrics import Metric, MetricThreshold, MetricStatus


@pytest.fixture
def collector():
    return MetricCollector()


def test_record_no_threshold(collector):
    m = Metric(name="cpu", value=30)
    result = collector.record(m)
    assert result.status == MetricStatus.OK


def test_record_with_threshold_warning(collector):
    collector.register_threshold("cpu", MetricThreshold(warning=70, critical=90))
    m = Metric(name="cpu", value=75)
    result = collector.record(m)
    assert result.status == MetricStatus.WARNING


def test_record_with_threshold_critical(collector):
    collector.register_threshold("cpu", MetricThreshold(warning=70, critical=90))
    m = Metric(name="cpu", value=95)
    result = collector.record(m)
    assert result.status == MetricStatus.CRITICAL


def test_latest_returns_most_recent(collector):
    collector.record(Metric(name="lag", value=10))
    collector.record(Metric(name="lag", value=20))
    assert collector.latest("lag").value == 20


def test_latest_unknown_metric(collector):
    assert collector.latest("nonexistent") is None


def test_history_length(collector):
    for i in range(5):
        collector.record(Metric(name="throughput", value=float(i)))
    assert len(collector.history("throughput")) == 5


def test_all_latest(collector):
    collector.record(Metric(name="a", value=1))
    collector.record(Metric(name="b", value=2))
    names = {m.name for m in collector.all_latest()}
    assert names == {"a", "b"}
