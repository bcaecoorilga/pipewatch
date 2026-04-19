"""Simple anomaly detection using z-score against recent metric history."""
from dataclasses import dataclass, field
from typing import List, Optional
import statistics
from pipewatch.metrics import Metric


@dataclass
class AnomalyResult:
    name: str
    value: float
    mean: float
    stddev: float
    z_score: float
    is_anomaly: bool
    threshold: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "mean": round(self.mean, 4),
            "stddev": round(self.stddev, 4),
            "z_score": round(self.z_score, 4),
            "is_anomaly": self.is_anomaly,
            "threshold": self.threshold,
        }


def detect_anomaly(
    current: Metric,
    history: List[Metric],
    z_threshold: float = 2.5,
) -> Optional[AnomalyResult]:
    """Detect if current metric value is anomalous relative to history."""
    values = [m.value for m in history]
    if len(values) < 2:
        return None

    mean = statistics.mean(values)
    stddev = statistics.stdev(values)

    if stddev == 0:
        z_score = 0.0
    else:
        z_score = abs((current.value - mean) / stddev)

    return AnomalyResult(
        name=current.name,
        value=current.value,
        mean=mean,
        stddev=stddev,
        z_score=z_score,
        is_anomaly=z_score >= z_threshold,
        threshold=z_threshold,
    )


def scan_anomalies(
    current_metrics: List[Metric],
    history: List[Metric],
    z_threshold: float = 2.5,
) -> List[AnomalyResult]:
    """Scan a list of current metrics for anomalies using shared history."""
    results = []
    for metric in current_metrics:
        metric_history = [m for m in history if m.name == metric.name]
        result = detect_anomaly(metric, metric_history, z_threshold)
        if result is not None:
            results.append(result)
    return results
