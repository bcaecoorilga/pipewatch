"""Tag-based filtering and grouping for metrics."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pipewatch.metrics import Metric


@dataclass
class TagIndex:
    """Maintains an index of metrics grouped by tags."""
    _index: Dict[str, List[Metric]] = field(default_factory=dict)

    def add(self, metric: Metric, tags: List[str]) -> None:
        """Register a metric under one or more tags."""
        for tag in tags:
            self._index.setdefault(tag, []).append(metric)

    def get(self, tag: str) -> List[Metric]:
        """Return all metrics associated with a tag."""
        return list(self._index.get(tag, []))

    def all_tags(self) -> List[str]:
        """Return sorted list of all known tags."""
        return sorted(self._index.keys())

    def filter(self, metrics: List[Metric], tag: str) -> List[Metric]:
        """Filter a list of metrics to those registered under a tag."""
        tagged = {id(m) for m in self.get(tag)}
        return [m for m in metrics if id(m) in tagged]


def tag_summary(index: TagIndex, metrics: List[Metric]) -> Dict[str, int]:
    """Return a count of metrics per tag from a given metric list."""
    summary: Dict[str, int] = {}
    for tag in index.all_tags():
        matched = index.filter(metrics, tag)
        if matched:
            summary[tag] = len(matched)
    return summary
