"""Alert suppression rules to avoid repeated notifications for the same condition."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class SuppressionRule:
    """Defines how long to suppress repeated alerts for a given metric."""

    metric_name: str
    cooldown_seconds: int = 300  # default 5 minutes

    def cooldown(self) -> timedelta:
        return timedelta(seconds=self.cooldown_seconds)


@dataclass
class SuppressionState:
    """Tracks the last time an alert was sent for a metric."""

    last_sent: Dict[str, datetime] = field(default_factory=dict)

    def record_sent(self, metric_name: str, at: Optional[datetime] = None) -> None:
        self.last_sent[metric_name] = at or datetime.utcnow()

    def last_sent_at(self, metric_name: str) -> Optional[datetime]:
        return self.last_sent.get(metric_name)


class AlertSuppressor:
    """Decides whether an alert should be suppressed based on cooldown rules."""

    def __init__(self) -> None:
        self._rules: Dict[str, SuppressionRule] = {}
        self._state = SuppressionState()

    def register_rule(self, rule: SuppressionRule) -> None:
        self._rules[rule.metric_name] = rule

    def should_suppress(self, metric_name: str, now: Optional[datetime] = None) -> bool:
        """Return True if the alert for *metric_name* is within its cooldown window."""
        rule = self._rules.get(metric_name)
        if rule is None:
            return False
        last = self._state.last_sent_at(metric_name)
        if last is None:
            return False
        check_time = now or datetime.utcnow()
        return (check_time - last) < rule.cooldown()

    def mark_sent(self, metric_name: str, at: Optional[datetime] = None) -> None:
        """Record that an alert was just sent for *metric_name*."""
        self._state.record_sent(metric_name, at)

    def reset(self, metric_name: str) -> None:
        """Clear suppression state for a metric (e.g. when it recovers)."""
        self._state.last_sent.pop(metric_name, None)
