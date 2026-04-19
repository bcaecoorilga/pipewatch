"""Tests for pipewatch.watchdog."""

from datetime import datetime, timedelta

import pytest

from pipewatch.collector import MetricCollector
from pipewatch.watchdog import Watchdog


@pytest.fixture
def collector():
    return MetricCollector()


@pytest.fixture
def watchdog(collector):
    return Watchdog(collector)


def test_no_rules_returns_empty(watchdog):
    assert watchdog.check() == []


def test_metric_never_seen_is_stale(watchdog):
    watchdog.register_rule("pipeline.lag", max_age_seconds=60)
    results = watchdog.check()
    assert len(results) == 1
    r = results[0]
    assert r.metric_name == "pipeline.lag"
    assert r.is_stale is True
    assert r.last_seen is None
    assert r.age_seconds is None


def test_fresh_metric_not_stale(watchdog, collector):
    watchdog.register_rule("pipeline.lag", max_age_seconds=60)
    now = datetime.utcnow()
    collector.record("pipeline.lag", 5.0)
    results = watchdog.check(now=now)
    assert results[0].is_stale is False


def test_old_metric_is_stale(watchdog, collector):
    watchdog.register_rule("pipeline.lag", max_age_seconds=30)
    old_time = datetime.utcnow() - timedelta(seconds=120)
    collector.record("pipeline.lag", 5.0)
    # Override timestamp manually
    collector.latest("pipeline.lag").timestamp = old_time
    now = datetime.utcnow()
    results = watchdog.check(now=now)
    assert results[0].is_stale is True
    assert results[0].age_seconds >= 120


def test_stale_filters_only_stale(watchdog, collector):
    watchdog.register_rule("a", max_age_seconds=60)
    watchdog.register_rule("b", max_age_seconds=60)
    collector.record("a", 1.0)
    stale = watchdog.stale()
    assert len(stale) == 1
    assert stale[0].metric_name == "b"


def test_to_dict_keys(watchdog):
    watchdog.register_rule("x", max_age_seconds=10)
    result = watchdog.check()[0]
    d = result.to_dict()
    assert set(d.keys()) == {"metric_name", "last_seen", "max_age_seconds", "is_stale", "age_seconds"}
