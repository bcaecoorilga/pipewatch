"""Tests for pipewatch.diff snapshot comparison."""

import pytest
from unittest.mock import patch
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.snapshot import capture, Snapshot
from pipewatch.diff import diff_snapshots, MetricDiff, SnapshotDiff


def _metric(name, value, status=MetricStatus.OK):
    return Metric(name=name, value=value, status=status)


@pytest.fixture
def snap_a():
    metrics = [_metric("cpu", 30.0), _metric("mem", 50.0)]
    return Snapshot(timestamp=1000.0, metrics=metrics, label="snap_a")


@pytest.fixture
def snap_b():
    metrics = [
        _metric("cpu", 75.0, MetricStatus.WARNING),
        _metric("mem", 50.0),
        _metric("disk", 20.0),
    ]
    return Snapshot(timestamp=2000.0, metrics=metrics, label="snap_b")


def test_diff_returns_snapshot_diff(snap_a, snap_b):
    result = diff_snapshots(snap_a, snap_b)
    assert isinstance(result, SnapshotDiff)
    assert result.snapshot_a_label == "snap_a"
    assert result.snapshot_b_label == "snap_b"


def test_diff_includes_all_metric_names(snap_a, snap_b):
    result = diff_snapshots(snap_a, snap_b)
    names = [d.name for d in result.diffs]
    assert "cpu" in names
    assert "mem" in names
    assert "disk" in names


def test_diff_value_delta(snap_a, snap_b):
    result = diff_snapshots(snap_a, snap_b)
    cpu_diff = next(d for d in result.diffs if d.name == "cpu")
    assert cpu_diff.value_delta == pytest.approx(45.0)


def test_diff_status_changed(snap_a, snap_b):
    result = diff_snapshots(snap_a, snap_b)
    cpu_diff = next(d for d in result.diffs if d.name == "cpu")
    assert cpu_diff.status_changed is True


def test_diff_no_status_change(snap_a, snap_b):
    result = diff_snapshots(snap_a, snap_b)
    mem_diff = next(d for d in result.diffs if d.name == "mem")
    assert mem_diff.status_changed is False
    assert mem_diff.value_delta == pytest.approx(0.0)


def test_diff_missing_in_a(snap_a, snap_b):
    result = diff_snapshots(snap_a, snap_b)
    disk_diff = next(d for d in result.diffs if d.name == "disk")
    assert disk_diff.old_value is None
    assert disk_diff.new_value == pytest.approx(20.0)


def test_to_dict_structure(snap_a, snap_b):
    result = diff_snapshots(snap_a, snap_b)
    d = result.to_dict()
    assert d["snapshot_a"] == "snap_a"
    assert d["snapshot_b"] == "snap_b"
    assert isinstance(d["diffs"], list)
    assert "total_changed" in d
    assert "status_changes" in d


def test_status_changes_count(snap_a, snap_b):
    result = diff_snapshots(snap_a, snap_b)
    assert len(result.status_changes) == 1
