"""Tests for pipewatch.pipeline_health."""

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.pipeline_health import HealthScore, compute_health, _grade


def _m(name: str, value: float, status: MetricStatus) -> Metric:
    return Metric(name=name, value=value, status=status)


def test_compute_health_empty_returns_none():
    assert compute_health([]) is None


def test_compute_health_all_ok():
    metrics = [_m("a", 1.0, MetricStatus.OK), _m("b", 2.0, MetricStatus.OK)]
    result = compute_health(metrics)
    assert result is not None
    assert result.score == pytest.approx(1.0)
    assert result.grade == "A"
    assert result.ok_count == 2
    assert result.warning_count == 0
    assert result.critical_count == 0


def test_compute_health_all_critical():
    metrics = [_m("a", 1.0, MetricStatus.CRITICAL)]
    result = compute_health(metrics)
    assert result is not None
    assert result.score == pytest.approx(0.0)
    assert result.grade == "F"


def test_compute_health_mixed():
    metrics = [
        _m("a", 1.0, MetricStatus.OK),       # weight 1.0
        _m("b", 2.0, MetricStatus.WARNING),   # weight 0.5
        _m("c", 3.0, MetricStatus.CRITICAL),  # weight 0.0
    ]
    result = compute_health(metrics)
    assert result is not None
    # (1.0 + 0.5 + 0.0) / 3 = 0.5
    assert result.score == pytest.approx(0.5)
    assert result.grade == "C"
    assert result.total == 3


def test_health_score_to_dict_keys():
    hs = HealthScore(score=0.8, total=5, ok_count=4, warning_count=1, critical_count=0)
    d = hs.to_dict()
    assert set(d.keys()) == {"score", "grade", "total", "ok_count", "warning_count", "critical_count"}


@pytest.mark.parametrize("score,expected", [
    (1.0, "A"),
    (0.9, "A"),
    (0.75, "B"),
    (0.5, "C"),
    (0.25, "D"),
    (0.1, "F"),
])
def test_grade_boundaries(score, expected):
    assert _grade(score) == expected
