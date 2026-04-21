"""Pattern detection: identify recurring status patterns across metric history."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus


@dataclass
class PatternResult:
    metric_name: str
    pattern: List[str]          # e.g. ["ok", "warning", "ok", "warning"]
    repeats: int                # how many times the pattern was found
    is_oscillating: bool        # True when metric alternates between two states
    dominant_status: Optional[str] = None  # most common status in window

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "pattern": self.pattern,
            "repeats": self.repeats,
            "is_oscillating": self.is_oscillating,
            "dominant_status": self.dominant_status,
        }


def _most_common(statuses: List[str]) -> Optional[str]:
    if not statuses:
        return None
    return max(set(statuses), key=statuses.count)


def _count_repeats(sequence: List[str], pattern: List[str]) -> int:
    """Count non-overlapping occurrences of *pattern* in *sequence*."""
    if not pattern:
        return 0
    count = 0
    step = len(pattern)
    i = 0
    while i <= len(sequence) - step:
        if sequence[i : i + step] == pattern:
            count += 1
            i += step
        else:
            i += 1
    return count


def detect_pattern(
    history: MetricHistory,
    metric_name: str,
    window: int = 20,
    min_repeats: int = 2,
) -> Optional[PatternResult]:
    """Analyse the last *window* records for *metric_name* and return a
    PatternResult when a repeating pattern is found, else None."""
    records = history.for_name(metric_name)[-window:]
    if len(records) < 4:
        return None

    statuses = [r.status.value for r in records]
    dominant = _most_common(statuses)

    # Detect simple 2-state oscillation
    unique = list(dict.fromkeys(statuses))  # ordered unique
    is_oscillating = False
    best_pattern: List[str] = []
    best_repeats = 0

    for length in range(2, len(statuses) // 2 + 1):
        candidate = statuses[:length]
        repeats = _count_repeats(statuses, candidate)
        if repeats >= min_repeats and repeats > best_repeats:
            best_repeats = repeats
            best_pattern = candidate

    if not best_pattern:
        return None

    is_oscillating = len(set(best_pattern)) == 2 and best_repeats >= min_repeats

    return PatternResult(
        metric_name=metric_name,
        pattern=best_pattern,
        repeats=best_repeats,
        is_oscillating=is_oscillating,
        dominant_status=dominant,
    )


def scan_patterns(
    history: MetricHistory,
    window: int = 20,
    min_repeats: int = 2,
) -> List[PatternResult]:
    """Run pattern detection for every metric name found in *history*."""
    names = {r.name for r in history.all()}
    results = []
    for name in sorted(names):
        result = detect_pattern(history, name, window=window, min_repeats=min_repeats)
        if result is not None:
            results.append(result)
    return results
