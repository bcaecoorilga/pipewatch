"""Tests for pipewatch.sla module."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.sla import SLARule, SLAResult, check_sla, scan_sla


def _make_history(records):
    """Return a mock MetricHistory whose for_name returns the given records."""
    h = MagicMock()
    h.for_name.return_value = records
    return h


def _m(name: str, value: float, status: MetricStatus, ts: float) -> Metric:
    return Metric(name=name, value=value, status=status, timestamp=ts)


@pytest.fixture
def rule():
    return SLARule(
        name="test-sla",
        metric_name="latency",
        max_critical_ratio=0.2,
        window_seconds=3600.0,
    )


def test_sla_rule_valid(rule):
    assert rule.is_valid()


def test_sla_rule_invalid_zero_window():
    r = SLARule("r", "m", 0.1, window_seconds=0)
    assert not r.is_valid()


def test_sla_rule_invalid_ratio_above_one():
    r = SLARule("r", "m", 1.5)
    assert not r.is_valid()


def test_check_sla_returns_none_for_invalid_rule():
    bad = SLARule("", "", -1.0)
    result = check_sla(bad, _make_history([]))
    assert result is None


def test_check_sla_empty_history_not_breached(rule):
    result = check_sla(rule, _make_history([]))
    assert result is not None
    assert result.total == 0
    assert not result.breached


def test_check_sla_all_ok_not_breached(rule):
    now = time.time()
    records = [_m("latency", 1.0, MetricStatus.OK, now - i * 10) for i in range(5)]
    result = check_sla(rule, _make_history(records))
    assert result.critical_count == 0
    assert not result.breached


def test_check_sla_critical_ratio_within_limit(rule):
    now = time.time()
    records = [
        _m("latency", 1.0, MetricStatus.OK, now - 10),
        _m("latency", 1.0, MetricStatus.OK, now - 20),
        _m("latency", 1.0, MetricStatus.OK, now - 30),
        _m("latency", 1.0, MetricStatus.OK, now - 40),
        _m("latency", 9.0, MetricStatus.CRITICAL, now - 50),  # 1/5 = 0.20 == limit
    ]
    result = check_sla(rule, _make_history(records))
    assert result.critical_count == 1
    assert not result.breached  # 0.20 is not > 0.20


def test_check_sla_critical_ratio_exceeds_limit(rule):
    now = time.time()
    records = [
        _m("latency", 9.0, MetricStatus.CRITICAL, now - 10),
        _m("latency", 9.0, MetricStatus.CRITICAL, now - 20),
        _m("latency", 1.0, MetricStatus.OK, now - 30),
    ]
    result = check_sla(rule, _make_history(records))
    assert result.critical_count == 2
    assert result.breached


def test_scan_sla_skips_invalid_rules(rule):
    bad = SLARule("", "", -1.0)
    results = scan_sla([rule, bad], _make_history([]))
    assert len(results) == 1
    assert results[0].rule.name == "test-sla"


def test_result_to_dict(rule):
    result = SLAResult(rule=rule, total=10, critical_count=1,
                       critical_ratio=0.1, breached=False)
    d = result.to_dict()
    assert d["rule"] == "test-sla"
    assert d["metric"] == "latency"
    assert d["total"] == 10
    assert d["critical_count"] == 1
    assert d["critical_ratio"] == 0.1
    assert d["breached"] is False
