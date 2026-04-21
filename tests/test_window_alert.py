"""Tests for pipewatch.window_alert."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.window_alert import (
    WindowAlertRule,
    WindowAlertResult,
    check_window_alert,
    scan_window_alerts,
)


def _m(value: float, status: MetricStatus, name: str = "cpu") -> Metric:
    return Metric(
        name=name,
        value=value,
        status=status,
        timestamp=datetime.now(tz=timezone.utc),
    )


# ---------------------------------------------------------------------------
# WindowAlertRule validation
# ---------------------------------------------------------------------------

def test_rule_valid():
    rule = WindowAlertRule("cpu", MetricStatus.WARNING, window=5, min_breaches=3)
    assert rule.is_valid()


def test_rule_invalid_min_breaches_exceeds_window():
    rule = WindowAlertRule("cpu", MetricStatus.WARNING, window=3, min_breaches=5)
    assert not rule.is_valid()


def test_rule_invalid_ok_level():
    rule = WindowAlertRule("cpu", MetricStatus.OK, window=5, min_breaches=3)
    assert not rule.is_valid()


# ---------------------------------------------------------------------------
# check_window_alert
# ---------------------------------------------------------------------------

def test_check_returns_none_for_empty_history():
    rule = WindowAlertRule("cpu", MetricStatus.WARNING, window=5, min_breaches=3)
    assert check_window_alert(rule, []) is None


def test_check_returns_none_for_invalid_rule():
    rule = WindowAlertRule("cpu", MetricStatus.OK, window=5, min_breaches=3)
    history = [_m(1.0, MetricStatus.OK)]
    assert check_window_alert(rule, history) is None


def test_check_not_fired_insufficient_breaches():
    rule = WindowAlertRule("cpu", MetricStatus.WARNING, window=5, min_breaches=3)
    history = [
        _m(10.0, MetricStatus.OK),
        _m(20.0, MetricStatus.WARNING),
        _m(10.0, MetricStatus.OK),
        _m(10.0, MetricStatus.OK),
        _m(10.0, MetricStatus.OK),
    ]
    result = check_window_alert(rule, history)
    assert result is not None
    assert not result.fired
    assert result.breach_count == 1


def test_check_fired_when_enough_breaches():
    rule = WindowAlertRule("cpu", MetricStatus.WARNING, window=5, min_breaches=3)
    history = [
        _m(10.0, MetricStatus.WARNING),
        _m(20.0, MetricStatus.WARNING),
        _m(10.0, MetricStatus.OK),
        _m(30.0, MetricStatus.CRITICAL),
        _m(25.0, MetricStatus.WARNING),
    ]
    result = check_window_alert(rule, history)
    assert result is not None
    assert result.fired
    assert result.breach_count == 4  # WARNING + WARNING + CRITICAL + WARNING


def test_check_critical_rule_ignores_warning():
    rule = WindowAlertRule("cpu", MetricStatus.CRITICAL, window=5, min_breaches=2)
    history = [
        _m(10.0, MetricStatus.WARNING),
        _m(20.0, MetricStatus.WARNING),
        _m(30.0, MetricStatus.CRITICAL),
        _m(10.0, MetricStatus.OK),
        _m(10.0, MetricStatus.OK),
    ]
    result = check_window_alert(rule, history)
    assert result is not None
    assert not result.fired
    assert result.breach_count == 1


def test_check_uses_only_last_window_readings():
    rule = WindowAlertRule("cpu", MetricStatus.WARNING, window=3, min_breaches=2)
    history = [
        _m(10.0, MetricStatus.WARNING),  # outside window
        _m(10.0, MetricStatus.WARNING),  # outside window
        _m(10.0, MetricStatus.OK),
        _m(10.0, MetricStatus.OK),
        _m(10.0, MetricStatus.OK),
    ]
    result = check_window_alert(rule, history)
    assert result is not None
    assert not result.fired
    assert result.readings_checked == 3


# ---------------------------------------------------------------------------
# scan_window_alerts
# ---------------------------------------------------------------------------

def test_scan_returns_fired_results():
    rules = [
        WindowAlertRule("cpu", MetricStatus.WARNING, window=3, min_breaches=2),
        WindowAlertRule("mem", MetricStatus.WARNING, window=3, min_breaches=2),
    ]
    history_map = {
        "cpu": [_m(1, MetricStatus.WARNING, "cpu")] * 3,
        "mem": [_m(1, MetricStatus.OK, "mem")] * 3,
    }
    results = scan_window_alerts(rules, history_map)
    assert len(results) == 2
    fired = [r for r in results if r.fired]
    assert len(fired) == 1
    assert fired[0].rule.metric_name == "cpu"
