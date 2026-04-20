"""Tests for pipewatch.pipeline_summary."""

from unittest.mock import MagicMock
from datetime import datetime, timezone

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.history import MetricHistory
from pipewatch.pipeline_summary import build_summary, PipelineSummary


def _metric(name: str, value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, status=status, timestamp=datetime.now(timezone.utc))


@pytest.fixture
def empty_collector():
    c = MagicMock()
    c.all.return_value = []
    return c


@pytest.fixture
def collector_with_metrics():
    c = MagicMock()
    c.all.return_value = [
        _metric("cpu", 40.0, MetricStatus.OK),
        _metric("memory", 85.0, MetricStatus.WARNING),
        _metric("disk", 95.0, MetricStatus.CRITICAL),
    ]
    return c


@pytest.fixture
def empty_history(tmp_path):
    return MetricHistory(path=str(tmp_path / "history.json"))


def test_build_summary_empty_collector(empty_collector, empty_history):
    summary = build_summary(empty_collector, empty_history)
    assert isinstance(summary, PipelineSummary)
    assert summary.health is None
    assert summary.anomalies == []
    assert summary.trends == {}


def test_build_summary_has_health(collector_with_metrics, empty_history):
    summary = build_summary(collector_with_metrics, empty_history)
    assert summary.health is not None
    assert summary.health.score >= 0.0


def test_build_summary_no_anomalies_on_empty_history(collector_with_metrics, empty_history):
    summary = build_summary(collector_with_metrics, empty_history)
    assert summary.has_anomalies is False
    assert summary.anomaly_count == 0


def test_build_summary_to_dict_structure(collector_with_metrics, empty_history):
    summary = build_summary(collector_with_metrics, empty_history)
    d = summary.to_dict()
    assert "health" in d
    assert "anomalies" in d
    assert "trends" in d
    assert isinstance(d["anomalies"], list)
    assert isinstance(d["trends"], dict)


def test_build_summary_trends_populated(tmp_path, collector_with_metrics):
    history = MetricHistory(path=str(tmp_path / "h.json"))
    now = datetime.now(timezone.utc)
    for i in range(6):
        m = Metric(name="cpu", value=float(10 + i * 5), status=MetricStatus.OK, timestamp=now)
        history.append(m)

    summary = build_summary(collector_with_metrics, history)
    # cpu trend should be detected since we have enough history
    assert "cpu" in summary.trends
    assert summary.trends["cpu"] is not None
