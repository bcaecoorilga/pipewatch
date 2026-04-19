"""Tests for MetricHistory."""

import os
import tempfile
from datetime import datetime, timedelta

import pytest

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus


@pytest.fixture
def tmp_history(tmp_path):
    return MetricHistory(path=str(tmp_path / "history.json"))


def _metric(name="latency", value=1.0):
    return Metric(name=name, value=value, unit="ms", status=MetricStatus.OK)


def test_append_and_all(tmp_history):
    tmp_history.append(_metric(value=1.0))
    tmp_history.append(_metric(value=2.0))
    records = tmp_history.all()
    assert len(records) == 2
    assert records[0]["value"] == 1.0


def test_for_name_filters(tmp_history):
    tmp_history.append(_metric(name="latency", value=1.0))
    tmp_history.append(_metric(name="error_rate", value=0.1))
    result = tmp_history.for_name("latency")
    assert len(result) == 1
    assert result[0]["name"] == "latency"


def test_since_filters_by_time(tmp_history):
    m = _metric(value=5.0)
    tmp_history.append(m)
    future = datetime.utcnow() + timedelta(hours=1)
    assert tmp_history.since(future) == []
    past = datetime.utcnow() - timedelta(hours=1)
    assert len(tmp_history.since(past)) == 1


def test_clear(tmp_history):
    tmp_history.append(_metric())
    tmp_history.clear()
    assert tmp_history.all() == []


def test_missing_file_returns_empty(tmp_path):
    h = MetricHistory(path=str(tmp_path / "nonexistent.json"))
    assert h.all() == []
