"""Tests for pipewatch.heartbeat."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.collector import MetricCollector
from pipewatch.heartbeat import HeartbeatMonitor
from pipewatch.metrics import Metric, MetricStatus


@pytest.fixture()
def collector() -> MetricCollector:
    return MetricCollector()


@pytest.fixture()
def monitor() -> HeartbeatMonitor:
    return HeartbeatMonitor()


def _m(name: str, ts: datetime) -> Metric:
    return Metric(name=name, value=1.0, timestamp=ts, status=MetricStatus.OK)


def test_register_invalid_interval_raises(monitor):
    with pytest.raises(ValueError):
        monitor.register("cpu", 0)


def test_check_unregistered_returns_none(monitor, collector):
    assert monitor.check("cpu", collector) is None


def test_check_never_seen_is_dead(monitor, collector):
    monitor.register("cpu", 60)
    result = monitor.check("cpu", collector)
    assert result is not None
    assert result.is_alive is False
    assert result.last_seen is None
    assert result.seconds_since is None


def test_check_recent_metric_is_alive(monitor, collector):
    monitor.register("cpu", 60)
    now = datetime.utcnow()
    collector.record(_m("cpu", now - timedelta(seconds=10)))
    result = monitor.check("cpu", collector, now=now)
    assert result is not None
    assert result.is_alive is True
    assert result.seconds_since == pytest.approx(10.0, abs=0.1)


def test_check_stale_metric_is_dead(monitor, collector):
    monitor.register("cpu", 30)
    now = datetime.utcnow()
    collector.record(_m("cpu", now - timedelta(seconds=90)))
    result = monitor.check("cpu", collector, now=now)
    assert result is not None
    assert result.is_alive is False


def test_scan_returns_all_registered(monitor, collector):
    now = datetime.utcnow()
    monitor.register("cpu", 60)
    monitor.register("mem", 60)
    collector.record(_m("cpu", now - timedelta(seconds=5)))
    results = monitor.scan(collector, now=now)
    assert len(results) == 2
    names = {r.name for r in results}
    assert names == {"cpu", "mem"}


def test_to_dict_structure(monitor, collector):
    monitor.register("cpu", 60)
    now = datetime.utcnow()
    collector.record(_m("cpu", now - timedelta(seconds=5)))
    result = monitor.check("cpu", collector, now=now)
    d = result.to_dict()
    assert "name" in d
    assert "is_alive" in d
    assert "seconds_since" in d
    assert "last_seen" in d
