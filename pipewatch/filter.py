"""Filtering utilities for metrics by tag, status, or name pattern."""

from __future__ import annotations

import fnmatch
from typing import Iterable, List, Optional

from pipewatch.metrics import Metric, MetricStatus


def filter_by_status(
    metrics: Iterable[Metric], status: MetricStatus
) -> List[Metric]:
    """Return metrics whose status matches the given status."""
    return [m for m in metrics if m.status == status]


def filter_by_name(
    metrics: Iterable[Metric], pattern: str
) -> List[Metric]:
    """Return metrics whose name matches a glob pattern."""
    return [m for m in metrics if fnmatch.fnmatch(m.name, pattern)]


def filter_by_tag(
    metrics: Iterable[Metric],
    tag: str,
    tag_index,  # TagIndex
) -> List[Metric]:
    """Return metrics that are associated with a given tag."""
    tagged_names = {m.name for m in tag_index.get(tag)}
    return [m for m in metrics if m.name in tagged_names]


def apply_filters(
    metrics: Iterable[Metric],
    *,
    status: Optional[MetricStatus] = None,
    name_pattern: Optional[str] = None,
    tag: Optional[str] = None,
    tag_index=None,
) -> List[Metric]:
    """Apply zero or more filters in sequence and return the result."""
    result = list(metrics)
    if status is not None:
        result = filter_by_status(result, status)
    if name_pattern is not None:
        result = filter_by_name(result, name_pattern)
    if tag is not None and tag_index is not None:
        result = filter_by_tag(result, tag, tag_index)
    return result
