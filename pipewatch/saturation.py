"""Saturation detection: measures how close a metric is to a defined ceiling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric


@dataclass
class SaturationResult:
    metric_name: str
    current_value: float
    ceiling: float
    saturation_pct: float   # 0-100
    is_saturated: bool
    label: str              # e.g. "critical", "warning", "ok"

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "ceiling": self.ceiling,
            "saturation_pct": round(self.saturation_pct, 2),
            "is_saturated": self.is_saturated,
            "label": self.label,
        }


def _classify(pct: float, warn_pct: float, crit_pct: float) -> str:
    if pct >= crit_pct:
        return "critical"
    if pct >= warn_pct:
        return "warning"
    return "ok"


def detect_saturation(
    metric: Metric,
    ceiling: float,
    warn_pct: float = 75.0,
    crit_pct: float = 90.0,
) -> Optional[SaturationResult]:
    """Return saturation info for a single metric value against a ceiling."""
    if ceiling <= 0:
        return None
    pct = (metric.value / ceiling) * 100.0
    is_saturated = pct >= crit_pct
    label = _classify(pct, warn_pct, crit_pct)
    return SaturationResult(
        metric_name=metric.name,
        current_value=metric.value,
        ceiling=ceiling,
        saturation_pct=pct,
        is_saturated=is_saturated,
        label=label,
    )


def scan_saturations(
    metrics: List[Metric],
    ceilings: dict,
    warn_pct: float = 75.0,
    crit_pct: float = 90.0,
) -> List[SaturationResult]:
    """Scan a list of metrics against a name->ceiling mapping."""
    results = []
    for m in metrics:
        ceiling = ceilings.get(m.name)
        if ceiling is None:
            continue
        result = detect_saturation(m, ceiling, warn_pct, crit_pct)
        if result is not None:
            results.append(result)
    return results
