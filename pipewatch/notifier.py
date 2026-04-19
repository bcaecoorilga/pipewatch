"""Notification channels for pipewatch alerts."""

from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.alerts import Alert
from pipewatch.metrics import MetricStatus
import logging

logger = logging.getLogger(__name__)


@dataclass
class NotificationRecord:
    channel: str
    alert: Alert
    success: bool
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "alert": self.alert.to_dict(),
            "success": self.success,
            "message": self.message,
        }


class BaseNotifier:
    name: str = "base"

    def send(self, alert: Alert) -> NotificationRecord:
        raise NotImplementedError


class LogNotifier(BaseNotifier):
    """Logs alerts using Python's logging module."""

    name = "log"

    def __init__(self, level: str = "WARNING"):
        self.level = getattr(logging, level.upper(), logging.WARNING)

    def send(self, alert: Alert) -> NotificationRecord:
        msg = f"[pipewatch] {alert.severity.value.upper()} — {alert.metric_name}: {alert.message}"
        logger.log(self.level, msg)
        return NotificationRecord(channel=self.name, alert=alert, success=True, message=msg)


class ConsoleNotifier(BaseNotifier):
    """Prints alerts to stdout."""

    name = "console"

    def send(self, alert: Alert) -> NotificationRecord:
        msg = f"[{alert.severity.value.upper()}] {alert.metric_name}: {alert.message}"
        print(msg)
        return NotificationRecord(channel=self.name, alert=alert, success=True, message=msg)


class NotificationDispatcher:
    """Dispatches alerts to registered notifiers based on severity."""

    def __init__(self, min_severity: MetricStatus = MetricStatus.WARNING):
        self.notifiers: List[BaseNotifier] = []
        self.min_severity = min_severity
        self.history: List[NotificationRecord] = []

    def register(self, notifier: BaseNotifier) -> None:
        self.notifiers.append(notifier)

    def _should_notify(self, alert: Alert) -> bool:
        order = [MetricStatus.OK, MetricStatus.WARNING, MetricStatus.CRITICAL]
        return order.index(alert.severity) >= order.index(self.min_severity)

    def dispatch(self, alert: Alert) -> List[NotificationRecord]:
        if not self._should_notify(alert):
            return []
        records = [n.send(alert) for n in self.notifiers]
        self.history.extend(records)
        return records
