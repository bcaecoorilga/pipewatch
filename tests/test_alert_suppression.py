"""Tests for pipewatch.alert_suppression."""

from datetime import datetime, timedelta

import pytest

from pipewatch.alert_suppression import AlertSuppressor, SuppressionRule


@pytest.fixture
def suppressor() -> AlertSuppressor:
    s = AlertSuppressor()
    s.register_rule(SuppressionRule(metric_name="cpu_usage", cooldown_seconds=60))
    return s


def test_no_rule_never_suppresses():
    s = AlertSuppressor()
    assert s.should_suppress("unknown_metric") is False


def test_first_alert_not_suppressed(suppressor):
    # No alert has been sent yet — should not suppress.
    assert suppressor.should_suppress("cpu_usage") is False


def test_alert_suppressed_within_cooldown(suppressor):
    now = datetime(2024, 1, 1, 12, 0, 0)
    suppressor.mark_sent("cpu_usage", at=now)
    # 30 seconds later — still within the 60-second cooldown.
    later = now + timedelta(seconds=30)
    assert suppressor.should_suppress("cpu_usage", now=later) is True


def test_alert_not_suppressed_after_cooldown(suppressor):
    now = datetime(2024, 1, 1, 12, 0, 0)
    suppressor.mark_sent("cpu_usage", at=now)
    # 61 seconds later — cooldown has expired.
    later = now + timedelta(seconds=61)
    assert suppressor.should_suppress("cpu_usage", now=later) is False


def test_alert_suppressed_exactly_at_cooldown_boundary(suppressor):
    now = datetime(2024, 1, 1, 12, 0, 0)
    suppressor.mark_sent("cpu_usage", at=now)
    # Exactly at 60 seconds — boundary is exclusive (< not <=).
    at_boundary = now + timedelta(seconds=60)
    assert suppressor.should_suppress("cpu_usage", now=at_boundary) is False


def test_reset_clears_suppression(suppressor):
    now = datetime(2024, 1, 1, 12, 0, 0)
    suppressor.mark_sent("cpu_usage", at=now)
    suppressor.reset("cpu_usage")
    later = now + timedelta(seconds=10)
    assert suppressor.should_suppress("cpu_usage", now=later) is False


def test_reset_unknown_metric_does_not_raise(suppressor):
    # Should be a no-op, not raise.
    suppressor.reset("nonexistent_metric")


def test_multiple_rules_independent():
    s = AlertSuppressor()
    s.register_rule(SuppressionRule(metric_name="metric_a", cooldown_seconds=120))
    s.register_rule(SuppressionRule(metric_name="metric_b", cooldown_seconds=30))

    now = datetime(2024, 6, 15, 8, 0, 0)
    s.mark_sent("metric_a", at=now)
    s.mark_sent("metric_b", at=now)

    later = now + timedelta(seconds=45)
    # metric_a cooldown is 120s — still suppressed.
    assert s.should_suppress("metric_a", now=later) is True
    # metric_b cooldown is 30s — no longer suppressed.
    assert s.should_suppress("metric_b", now=later) is False
