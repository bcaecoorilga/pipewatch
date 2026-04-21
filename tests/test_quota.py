"""Tests for pipewatch.quota."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.quota import QuotaRule, QuotaResult, check_quota, scan_quotas


def _m(name: str, value: float, ts: datetime) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, timestamp=ts)


NOW = datetime(2024, 6, 1, 12, 0, 0)


def test_quota_rule_valid():
    rule = QuotaRule(name="cpu", max_records=10, window_seconds=60)
    assert rule.is_valid()


def test_quota_rule_invalid_zero_limit():
    rule = QuotaRule(name="cpu", max_records=0, window_seconds=60)
    assert not rule.is_valid()


def test_quota_rule_invalid_zero_window():
    rule = QuotaRule(name="cpu", max_records=10, window_seconds=0)
    assert not rule.is_valid()


def test_check_quota_returns_none_for_invalid_rule():
    rule = QuotaRule(name="cpu", max_records=0, window_seconds=60)
    records = [_m("cpu", 1.0, NOW)]
    assert check_quota(rule, records, now=NOW) is None


def test_check_quota_returns_none_for_empty_records():
    rule = QuotaRule(name="cpu", max_records=10, window_seconds=60)
    assert check_quota(rule, [], now=NOW) is None


def test_check_quota_not_exceeded():
    rule = QuotaRule(name="cpu", max_records=5, window_seconds=60)
    records = [_m("cpu", float(i), NOW - timedelta(seconds=i * 5)) for i in range(3)]
    result = check_quota(rule, records, now=NOW)
    assert result is not None
    assert result.exceeded is False
    assert result.count_in_window == 3


def test_check_quota_exceeded():
    rule = QuotaRule(name="cpu", max_records=2, window_seconds=300)
    records = [_m("cpu", float(i), NOW - timedelta(seconds=i * 10)) for i in range(5)]
    result = check_quota(rule, records, now=NOW)
    assert result is not None
    assert result.exceeded is True
    assert result.count_in_window == 5


def test_check_quota_ignores_old_records():
    rule = QuotaRule(name="cpu", max_records=2, window_seconds=60)
    old = _m("cpu", 9.0, NOW - timedelta(seconds=120))
    fresh = _m("cpu", 1.0, NOW - timedelta(seconds=10))
    result = check_quota(rule, [old, fresh], now=NOW)
    assert result is not None
    assert result.count_in_window == 1
    assert not result.exceeded


def test_scan_quotas_multiple_rules():
    rule_a = QuotaRule(name="cpu", max_records=1, window_seconds=300)
    rule_b = QuotaRule(name="mem", max_records=10, window_seconds=300)
    records_by_name = {
        "cpu": [_m("cpu", float(i), NOW - timedelta(seconds=i)) for i in range(3)],
        "mem": [_m("mem", float(i), NOW - timedelta(seconds=i)) for i in range(2)],
    }
    results = scan_quotas([rule_a, rule_b], records_by_name, now=NOW)
    assert len(results) == 2
    cpu_r = next(r for r in results if r.metric_name == "cpu")
    mem_r = next(r for r in results if r.metric_name == "mem")
    assert cpu_r.exceeded is True
    assert mem_r.exceeded is False
