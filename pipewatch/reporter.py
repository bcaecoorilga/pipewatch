"""Report generation for pipeline health metrics."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from pipewatch.metrics import MetricStatus
from pipewatch.collector import MetricCollector
from pipewatch.alerts import AlertManager


@dataclass
class PipelineReport:
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    total_metrics: int = 0
    ok_count: int = 0
    warning_count: int = 0
    critical_count: int = 0
    alerts: List[dict] = field(default_factory=list)
    metrics: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "summary": {
                "total": self.total_metrics,
                "ok": self.ok_count,
                "warning": self.warning_count,
                "critical": self.critical_count,
            },
            "alerts": self.alerts,
            "metrics": self.metrics,
        }


class Reporter:
    def __init__(self, collector: MetricCollector, alert_manager: Optional[AlertManager] = None):
        self.collector = collector
        self.alert_manager = alert_manager

    def generate(self) -> PipelineReport:
        report = PipelineReport()
        all_metrics = self.collector.all_latest()
        report.total_metrics = len(all_metrics)

        for metric in all_metrics:
            report.metrics.append(metric.to_dict())
            if metric.status == MetricStatus.OK:
                report.ok_count += 1
            elif metric.status == MetricStatus.WARNING:
                report.warning_count += 1
            elif metric.status == MetricStatus.CRITICAL:
                report.critical_count += 1

        if self.alert_manager:
            report.alerts = [a.to_dict() for a in self.alert_manager.get_alerts()]

        return report
