"""Core metric data structures for pipeline health monitoring."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MetricStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    name: str
    value: float
    unit: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: dict = field(default_factory=dict)
    status: MetricStatus = MetricStatus.UNKNOWN

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "status": self.status.value,
        }


@dataclass
class MetricThreshold:
    warning: Optional[float] = None
    critical: Optional[float] = None

    def evaluate(self, value: float) -> MetricStatus:
        if self.critical is not None and value >= self.critical:
            return MetricStatus.CRITICAL
        if self.warning is not None and value >= self.warning:
            return MetricStatus.WARNING
        return MetricStatus.OK
