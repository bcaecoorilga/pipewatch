"""Window-based alerting: fire an alert when a metric exceeds a threshold
for a sustained number of consecutive readings within a sliding window."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.metrics import Metric, MetricStatus


@dataclass
class WindowAlertRule:
    """Rule that triggers when *min_breaches* out of the last *window* readings
    are at or above *level* (WARNING or CRITICAL)."""

    metric_name: str
    level: MetricStatus  # WARNING or CRITICAL
    window: int = 5       # number of most-recent readings to inspect
    min_breaches: int = 3  # how many must breach to fire

    def is_valid(self) -> bool:
        return (
            self.window >= 1
            and 1 <= self.min_breaches <= self.window
            and self.level in (MetricStatus.WARNING, MetricStatus.CRITICAL)
        )


@dataclass
class WindowAlertResult:
    rule: WindowAlertRule
    readings_checked: int
    breach_count: int
    fired: bool
    latest_value: Optional[float]

    def to_dict(self) -> dict:
        return {
            "metric_name": self.rule.metric_name,
            "level": self.rule.level.value,
            "window": self.rule.window,
            "min_breaches": self.rule.min_breaches,
            "readings_checked": self.readings_checked,
            "breach_count": self.breach_count,
            "fired": self.fired,
            "latest_value": self.latest_value,
        }


def _breaches(metrics: List[Metric], level: MetricStatus) -> int:
    """Count metrics whose status is >= *level* (WARNING counts for CRITICAL rule
    only when status is exactly CRITICAL; WARNING rule catches both)."""
    order = [MetricStatus.OK, MetricStatus.WARNING, MetricStatus.CRITICAL]
    threshold_idx = order.index(level)
    return sum(1 for m in metrics if order.index(m.status) >= threshold_idx)


def check_window_alert(
    rule: WindowAlertRule, history: List[Metric]
) -> Optional[WindowAlertResult]:
    """Evaluate *rule* against *history* (oldest-first list of Metric objects).
    Returns None if the rule is invalid or there are no readings."""
    if not rule.is_valid() or not history:
        return None

    window_slice = history[-rule.window :]
    breach_count = _breaches(window_slice, rule.level)
    fired = breach_count >= rule.min_breaches
    latest_value = window_slice[-1].value if window_slice else None

    return WindowAlertResult(
        rule=rule,
        readings_checked=len(window_slice),
        breach_count=breach_count,
        fired=fired,
        latest_value=latest_value,
    )


def scan_window_alerts(
    rules: List[WindowAlertRule], history_map: dict
) -> List[WindowAlertResult]:
    """Apply each rule using *history_map* {metric_name: [Metric, ...]}."""
    results: List[WindowAlertResult] = []
    for rule in rules:
        readings = history_map.get(rule.metric_name, [])
        result = check_window_alert(rule, readings)
        if result is not None:
            results.append(result)
    return results
