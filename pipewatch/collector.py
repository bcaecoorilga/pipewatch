"""Metric collector that evaluates thresholds and stores recent metrics."""

from collections import deque
from typing import Deque, Dict, List, Optional

from pipewatch.metrics import Metric, MetricThreshold, MetricStatus


DEFAULT_HISTORY_SIZE = 100


class MetricCollector:
    def __init__(self, history_size: int = DEFAULT_HISTORY_SIZE):
        self._history: Dict[str, Deque[Metric]] = {}
        self._thresholds: Dict[str, MetricThreshold] = {}
        self._history_size = history_size

    def register_threshold(self, metric_name: str, threshold: MetricThreshold) -> None:
        self._thresholds[metric_name] = threshold

    def record(self, metric: Metric) -> Metric:
        threshold = self._thresholds.get(metric.name)
        if threshold:
            metric.status = threshold.evaluate(metric.value)
        else:
            metric.status = MetricStatus.OK

        if metric.name not in self._history:
            self._history[metric.name] = deque(maxlen=self._history_size)
        self._history[metric.name].append(metric)
        return metric

    def latest(self, metric_name: str) -> Optional[Metric]:
        history = self._history.get(metric_name)
        if history:
            return history[-1]
        return None

    def history(self, metric_name: str) -> List[Metric]:
        return list(self._history.get(metric_name, []))

    def all_latest(self) -> List[Metric]:
        return [dq[-1] for dq in self._history.values() if dq]
