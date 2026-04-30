"""Tests for pipewatch.burndown."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.burndown import BurndownResult, detect_burndown, scan_burndowns
from pipewatch.metrics import Metric, MetricStatus


def _m(name: str, value: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK)


def _fake_history(name: str, values: list, base_time: datetime = None) -> MagicMock:
    if base_time is None:
        base_time = datetime(2024, 1, 1, 0, 0, 0)
    records = []
    for i, v in enumerate(values):
        rec = MagicMock()
        rec.metric = _m(name, v)
        rec.timestamp = base_time + timedelta(seconds=i * 60)
        records.append(rec)
    history = MagicMock()
    history.for_name.return_value = records
    return history


def test_detect_burndown_returns_none_for_empty_history():
    history = MagicMock()
    history.for_name.return_value = []
    result = detect_burndown(_m("errors", 100.0), history, target=0.0)
    assert result is None


def test_detect_burndown_returns_none_for_single_record():
    history = _fake_history("errors", [50.0])
    result = detect_burndown(_m("errors", 50.0), history, target=0.0)
    assert result is None


def test_detect_burndown_falling_toward_target():
    history = _fake_history("errors", [100.0, 80.0, 60.0, 40.0])
    metric = _m("errors", 40.0)
    result = detect_burndown(metric, history, target=0.0)
    assert result is not None
    assert result.metric_name == "errors"
    assert result.current_value == pytest.approx(40.0)
    assert result.initial_value == pytest.approx(100.0)
    assert result.rate_per_second < 0
    assert result.eta_seconds is not None
    assert result.eta_seconds > 0
    assert result.percent_remaining == pytest.approx(40.0, rel=1e-2)


def test_detect_burndown_on_track_with_deadline():
    history = _fake_history("errors", [100.0, 50.0])
    metric = _m("errors", 50.0)
    # rate = -50 / 60 per sec; eta to 0 = 50 / (50/60) = 60 sec
    result = detect_burndown(metric, history, target=0.0, deadline_seconds=120.0)
    assert result is not None
    assert result.on_track is True


def test_detect_burndown_not_on_track_with_tight_deadline():
    history = _fake_history("errors", [100.0, 50.0])
    metric = _m("errors", 50.0)
    result = detect_burndown(metric, history, target=0.0, deadline_seconds=10.0)
    assert result is not None
    assert result.on_track is False


def test_detect_burndown_no_convergence_rising():
    history = _fake_history("errors", [10.0, 20.0, 30.0])
    metric = _m("errors", 30.0)
    result = detect_burndown(metric, history, target=0.0)
    assert result is not None
    assert result.eta_seconds is None
    assert result.on_track is False


def test_detect_burndown_to_dict():
    history = _fake_history("errors", [100.0, 60.0])
    metric = _m("errors", 60.0)
    result = detect_burndown(metric, history, target=0.0)
    assert result is not None
    d = result.to_dict()
    assert d["metric_name"] == "errors"
    assert "eta_seconds" in d
    assert "percent_remaining" in d
    assert "on_track" in d


def test_scan_burndowns_skips_missing_targets():
    history = _fake_history("errors", [100.0, 50.0])
    metrics = [_m("errors", 50.0), _m("latency", 200.0)]
    targets = {"errors": 0.0}  # latency has no target
    results = scan_burndowns(metrics, history, targets)
    assert len(results) == 1
    assert results[0].metric_name == "errors"


def test_scan_burndowns_returns_multiple():
    def _h(name, values):
        h = _fake_history(name, values)
        return h

    history = MagicMock()
    history.for_name.side_effect = lambda name: [
        *[MagicMock(metric=_m(name, v),
                    timestamp=datetime(2024, 1, 1) + timedelta(seconds=i * 60))
          for i, v in enumerate([100.0, 50.0])]
    ]
    metrics = [_m("errors", 50.0), _m("warnings", 50.0)]
    targets = {"errors": 0.0, "warnings": 0.0}
    results = scan_burndowns(metrics, history, targets)
    assert len(results) == 2
