"""Tests for pipewatch.notifier module."""

import pytest
from unittest.mock import patch
from pipewatch.metrics import MetricStatus
from pipewatch.alerts import Alert
from pipewatch.notifier import (
    LogNotifier,
    ConsoleNotifier,
    NotificationDispatcher,
    NotificationRecord,
)


@pytest.fixture
def warning_alert():
    return Alert(metric_name="latency", severity=MetricStatus.WARNING, message="High latency")


@pytest.fixture
def critical_alert():
    return Alert(metric_name="error_rate", severity=MetricStatus.CRITICAL, message="Error spike")


@pytest.fixture
def ok_alert():
    return Alert(metric_name="throughput", severity=MetricStatus.OK, message="All good")


def test_log_notifier_sends(warning_alert):
    notifier = LogNotifier()
    record = notifier.send(warning_alert)
    assert isinstance(record, NotificationRecord)
    assert record.success is True
    assert record.channel == "log"
    assert "latency" in record.message


def test_console_notifier_prints(capsys, critical_alert):
    notifier = ConsoleNotifier()
    record = notifier.send(critical_alert)
    captured = capsys.readouterr()
    assert "error_rate" in captured.out
    assert record.success is True


def test_dispatcher_skips_ok_by_default(ok_alert):
    dispatcher = NotificationDispatcher()
    dispatcher.register(ConsoleNotifier())
    records = dispatcher.dispatch(ok_alert)
    assert records == []


def test_dispatcher_sends_warning(warning_alert, capsys):
    dispatcher = NotificationDispatcher()
    dispatcher.register(ConsoleNotifier())
    records = dispatcher.dispatch(warning_alert)
    assert len(records) == 1
    assert records[0].success is True


def test_dispatcher_history_tracked(critical_alert):
    dispatcher = NotificationDispatcher()
    dispatcher.register(ConsoleNotifier())
    dispatcher.dispatch(critical_alert)
    dispatcher.dispatch(critical_alert)
    assert len(dispatcher.history) == 2


def test_dispatcher_multiple_notifiers(warning_alert, capsys):
    dispatcher = NotificationDispatcher()
    dispatcher.register(ConsoleNotifier())
    dispatcher.register(LogNotifier())
    records = dispatcher.dispatch(warning_alert)
    assert len(records) == 2
