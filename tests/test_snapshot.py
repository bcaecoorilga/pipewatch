"""Tests for pipewatch.snapshot."""
import time
from pathlib import Path

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.snapshot import Snapshot, capture, load_snapshots, save_snapshot


def _metric(name="latency", value=1.5, status=MetricStatus.OK):
    return Metric(name=name, value=value, status=status)


def test_capture_creates_snapshot():
    m = _metric()
    snap = capture([m], label="test")
    assert snap.label == "test"
    assert len(snap.metrics) == 1
    assert snap.metrics[0]["name"] == "latency"


def test_capture_no_label():
    snap = capture([])
    assert snap.label is None
    assert snap.metrics == []


def test_snapshot_to_dict():
    snap = Snapshot(timestamp=1000.0, label="x", metrics=[{"name": "a"}])
    d = snap.to_dict()
    assert d["timestamp"] == 1000.0
    assert d["label"] == "x"
    assert d["metrics"] == [{"name": "a"}]


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "snaps.jsonl"
    snap1 = capture([_metric("cpu", 0.8)], label="first")
    snap2 = capture([_metric("mem", 0.5)], label="second")
    save_snapshot(snap1, path)
    save_snapshot(snap2, path)

    loaded = load_snapshots(path)
    assert len(loaded) == 2
    assert loaded[0].label == "first"
    assert loaded[1].label == "second"
    assert loaded[0].metrics[0]["name"] == "cpu"


def test_load_missing_file(tmp_path):
    result = load_snapshots(tmp_path / "nonexistent.jsonl")
    assert result == []


def test_save_creates_parent_dirs(tmp_path):
    path = tmp_path / "deep" / "dir" / "snaps.jsonl"
    snap = capture([_metric()])
    save_snapshot(snap, path)
    assert path.exists()
