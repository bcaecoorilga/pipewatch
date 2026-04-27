"""Tests for pipewatch.latency."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.latency import LatencyResult, _classify, detect_latency, scan_latencies
from pipewatch.metrics import Metric, MetricStatus


def _m(name: str = "pipe.latency") -> Metric:
    return Metric(name=name, value=1.0, status=MetricStatus.OK)


def _fake_history(name: str, timestamps: list):
    """Build a mock MetricHistory returning records with given timestamps."""
    records = []
    for ts in timestamps:
        r = MagicMock()
        r.timestamp = ts
        r.metric = _m(name)
        records.append(r)
    history = MagicMock()
    history.for_name.return_value = records
    return history


def test_classify_low():
    assert _classify(0.5, 1.0, 5.0) == "low"


def test_classify_moderate():
    assert _classify(2.0, 1.0, 5.0) == "moderate"


def test_classify_high():
    assert _classify(6.0, 1.0, 5.0) == "high"


def test_detect_latency_returns_none_for_empty_history():
    history = _fake_history("m", [])
    result = detect_latency(_m("m"), history)
    assert result is None


def test_detect_latency_returns_none_for_single_record():
    history = _fake_history("m", [100.0])
    result = detect_latency(_m("m"), history)
    assert result is None


def test_detect_latency_basic():
    # gaps: [1, 1, 1] => mean=1.0 => moderate
    history = _fake_history("m", [0.0, 1.0, 2.0, 3.0])
    result = detect_latency(_m("m"), history, warn_threshold=1.0, crit_threshold=5.0)
    assert result is not None
    assert result.metric_name == "m"
    assert result.mean_latency == pytest.approx(1.0)
    assert result.min_latency == pytest.approx(1.0)
    assert result.max_latency == pytest.approx(1.0)
    assert result.sample_count == 3
    assert result.classification == "moderate"


def test_detect_latency_high():
    history = _fake_history("m", [0.0, 10.0])
    result = detect_latency(_m("m"), history, warn_threshold=1.0, crit_threshold=5.0)
    assert result is not None
    assert result.classification == "high"


def test_scan_latencies_returns_results_for_all_metrics():
    h1 = _fake_history("a", [0.0, 1.0, 2.0])
    # We need a single history mock that dispatches by name
    history = MagicMock()
    history.for_name.side_effect = lambda name: (
        [MagicMock(timestamp=t) for t in [0.0, 1.0, 2.0]] if name in ("a", "b") else []
    )
    metrics = [_m("a"), _m("b"), _m("c")]
    results = scan_latencies(metrics, history)
    # "c" has no history, so only 2 results
    assert len(results) == 2
    names = {r.metric_name for r in results}
    assert names == {"a", "b"}


def test_latency_result_to_dict():
    r = LatencyResult(
        metric_name="x",
        mean_latency=2.5,
        max_latency=4.0,
        min_latency=1.0,
        p95_latency=3.8,
        classification="moderate",
        sample_count=10,
    )
    d = r.to_dict()
    assert d["metric_name"] == "x"
    assert d["classification"] == "moderate"
    assert d["sample_count"] == 10
