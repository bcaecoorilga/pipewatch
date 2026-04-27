"""Tests for pipewatch.persistence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.persistence import clear_state, load_state, save_state


def _metric(name: str, value: float, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=value, timestamp=1_700_000_000.0, status=status)


# ---------------------------------------------------------------------------
# save_state
# ---------------------------------------------------------------------------

def test_save_state_creates_file(tmp_path):
    dest = tmp_path / "sub" / "state.json"
    metrics = [_metric("cpu", 42.0)]
    result = save_state(metrics, path=dest)
    assert result == dest
    assert dest.exists()


def test_save_state_writes_valid_json(tmp_path):
    dest = tmp_path / "state.json"
    metrics = [_metric("cpu", 10.0), _metric("mem", 80.0, MetricStatus.WARNING)]
    save_state(metrics, path=dest)
    with dest.open() as fh:
        data = json.load(fh)
    assert len(data) == 2
    assert data[0]["name"] == "cpu"
    assert data[1]["status"] == MetricStatus.WARNING.value


def test_save_state_overwrites_existing(tmp_path):
    dest = tmp_path / "state.json"
    save_state([_metric("a", 1.0)], path=dest)
    save_state([_metric("b", 2.0), _metric("c", 3.0)], path=dest)
    with dest.open() as fh:
        data = json.load(fh)
    assert len(data) == 2


# ---------------------------------------------------------------------------
# load_state
# ---------------------------------------------------------------------------

def test_load_state_returns_empty_for_missing_file(tmp_path):
    result = load_state(path=tmp_path / "nonexistent.json")
    assert result == []


def test_load_state_roundtrip(tmp_path):
    dest = tmp_path / "state.json"
    original = [
        _metric("latency", 55.5, MetricStatus.OK),
        _metric("errors", 12.0, MetricStatus.CRITICAL),
    ]
    save_state(original, path=dest)
    loaded = load_state(path=dest)
    assert len(loaded) == 2
    assert loaded[0].name == "latency"
    assert loaded[1].status == MetricStatus.CRITICAL
    assert loaded[1].value == 12.0


def test_load_state_returns_empty_for_malformed_json(tmp_path):
    dest = tmp_path / "state.json"
    dest.write_text("not valid json", encoding="utf-8")
    result = load_state(path=dest)
    assert result == []


# ---------------------------------------------------------------------------
# clear_state
# ---------------------------------------------------------------------------

def test_clear_state_removes_file(tmp_path):
    dest = tmp_path / "state.json"
    save_state([_metric("x", 1.0)], path=dest)
    removed = clear_state(path=dest)
    assert removed is True
    assert not dest.exists()


def test_clear_state_returns_false_when_no_file(tmp_path):
    dest = tmp_path / "state.json"
    removed = clear_state(path=dest)
    assert removed is False
