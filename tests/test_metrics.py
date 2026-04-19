"""Tests for metric data structures and threshold evaluation."""

import pytest
from pipewatch.metrics import Metric, MetricThreshold, MetricStatus


def test_metric_defaults():
    m = Metric(name="latency", value=42.0)
    assert m.unit == ""
    assert m.tags == {}
    assert m.status == MetricStatus.UNKNOWN


def test_metric_to_dict():
    m = Metric(name="row_count", value=1000, unit="rows")
    d = m.to_dict()
    assert d["name"] == "row_count"
    assert d["value"] == 1000
    assert d["unit"] == "rows"
    assert "timestamp" in d


def test_threshold_ok():
    t = MetricThreshold(warning=100, critical=200)
    assert t.evaluate(50) == MetricStatus.OK


def test_threshold_warning():
    t = MetricThreshold(warning=100, critical=200)
    assert t.evaluate(150) == MetricStatus.WARNING


def test_threshold_critical():
    t = MetricThreshold(warning=100, critical=200)
    assert t.evaluate(250) == MetricStatus.CRITICAL


def test_threshold_only_critical():
    t = MetricThreshold(critical=50)
    assert t.evaluate(49) == MetricStatus.OK
    assert t.evaluate(50) == MetricStatus.CRITICAL


def test_threshold_no_limits():
    t = MetricThreshold()
    assert t.evaluate(9999) == MetricStatus.OK
