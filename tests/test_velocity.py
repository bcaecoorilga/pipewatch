"""Tests for pipewatch.velocity."""
from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest

from pipewatch.history import MetricHistory
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.velocity import (
    VelocityResult,
    _classify_direction,
    compute_velocity,
    scan_velocities,
)


def _m(name: str, value: float, ts: float) -> Metric:
    return Metric(name=name, value=value, status=MetricStatus.OK, timestamp=ts)


@pytest.fixture()
def history(tmp_path):
    return MetricHistory(path=str(tmp_path / "hist.json"))


# --- _classify_direction ---

def test_classify_accelerating():
    assert _classify_direction(0.5) == "accelerating"


def test_classify_decelerating():
    assert _classify_direction(-0.5) == "decelerating"


def test_classify_stable():
    assert _classify_direction(0.0) == "stable"
    assert _classify_direction(0.0005) == "stable"


# --- compute_velocity ---

def test_compute_velocity_returns_none_for_empty_history(history):
    assert compute_velocity("cpu", history) is None


def test_compute_velocity_returns_none_for_single_record(history):
    now = time.time()
    history.append(_m("cpu", 10.0, now))
    assert compute_velocity("cpu", history) is None


def test_compute_velocity_returns_none_for_zero_window(history):
    now = time.time()
    history.append(_m("cpu", 10.0, now - 10))
    history.append(_m("cpu", 20.0, now))
    assert compute_velocity("cpu", history, window_seconds=0) is None


def test_compute_velocity_basic(history):
    now = time.time()
    history.append(_m("cpu", 10.0, now - 60))
    history.append(_m("cpu", 70.0, now))

    result = compute_velocity("cpu", history, window_seconds=300)

    assert isinstance(result, VelocityResult)
    assert result.name == "cpu"
    assert result.samples == 2
    assert result.velocity_per_second == pytest.approx(1.0, rel=1e-3)
    assert result.velocity_per_minute == pytest.approx(60.0, rel=1e-3)
    assert result.direction == "accelerating"
    assert result.latest_value == 70.0


def test_compute_velocity_decelerating(history):
    now = time.time()
    history.append(_m("mem", 80.0, now - 60))
    history.append(_m("mem", 20.0, now))

    result = compute_velocity("mem", history, window_seconds=300)
    assert result is not None
    assert result.direction == "decelerating"
    assert result.velocity_per_second < 0


def test_compute_velocity_excludes_old_records(history):
    now = time.time()
    # This record is outside the 60-second window
    history.append(_m("cpu", 0.0, now - 120))
    history.append(_m("cpu", 10.0, now - 30))
    history.append(_m("cpu", 20.0, now))

    result = compute_velocity("cpu", history, window_seconds=60)
    assert result is not None
    assert result.samples == 2


def test_velocity_to_dict(history):
    now = time.time()
    history.append(_m("x", 0.0, now - 10))
    history.append(_m("x", 5.0, now))

    result = compute_velocity("x", history, window_seconds=60)
    d = result.to_dict()
    assert "velocity_per_second" in d
    assert "velocity_per_minute" in d
    assert "direction" in d
    assert d["name"] == "x"


def test_scan_velocities_multiple_metrics(history):
    now = time.time()
    history.append(_m("a", 0.0, now - 10))
    history.append(_m("a", 10.0, now))
    history.append(_m("b", 100.0, now - 10))
    history.append(_m("b", 50.0, now))

    results = scan_velocities(history, window_seconds=60)
    names = [r.name for r in results]
    assert "a" in names
    assert "b" in names
    assert len(results) == 2
