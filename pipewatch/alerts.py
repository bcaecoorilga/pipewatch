"""Alert management for pipewatch.

Handles alert formatting, deduplication, and output for pipeline health notifications.
"""

import json
from datetime import datetime
from typing import List, Optional, Callable
from pipewatch.metrics import Metric, MetricStatus


class Alert:
    """Represents a triggered alert for a metric threshold violation."""

    def __init__(self, metric: Metric, message: str):
        self.metric = metric
        self.message = message
        self.timestamp = datetime.utcnow()

    def __repr__(self):
        return f"Alert(name={self.metric.name!r}, status={self.metric.status.value}, message={self.message!r})"

    def to_dict(self) -> dict:
        """Serialize alert to a dictionary."""
        return {
            "alert_time": self.timestamp.isoformat(),
            "metric": self.metric.to_dict(),
            "message": self.message,
        }


class AlertManager:
    """Manages alert handlers and dispatches alerts for unhealthy metrics."""

    def __init__(self):
        self._handlers: List[Callable[[Alert], None]] = []
        # Track last alerted status per metric to avoid duplicate alerts
        self._last_alerted: dict = {}

        # Register default stdout handler
        self.add_handler(self._stdout_handler)

    def add_handler(self, handler: Callable[[Alert], None]) -> None:
        """Register a callable that receives Alert objects."""
        self._handlers.append(handler)

    def evaluate_and_alert(self, metric: Metric, message: Optional[str] = None) -> Optional[Alert]:
        """Dispatch an alert if the metric is in a warning or critical state.

        Suppresses duplicate alerts when the status hasn't changed since last alert.
        """
        if metric.status == MetricStatus.OK:
            # Clear suppression so future violations re-alert
            self._last_alerted.pop(metric.name, None)
            return None

        last_status = self._last_alerted.get(metric.name)
        if last_status == metric.status:
            # Same status as last alert — suppress to avoid noise
            return None

        self._last_alerted[metric.name] = metric.status

        alert_message = message or self._default_message(metric)
        alert = Alert(metric=metric, message=alert_message)

        for handler in self._handlers:
            handler(alert)

        return alert

    def clear_history(self) -> None:
        """Reset alert suppression history."""
        self._last_alerted.clear()

    @staticmethod
    def _default_message(metric: Metric) -> str:
        """Generate a default human-readable alert message."""
        return (
            f"[{metric.status.value.upper()}] '{metric.name}' = {metric.value} "
            f"at {metric.timestamp.isoformat()}"
        )

    @staticmethod
    def _stdout_handler(alert: Alert) -> None:
        """Default handler: print alert as JSON to stdout."""
        print(json.dumps(alert.to_dict(), indent=2))
