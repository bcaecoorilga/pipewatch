"""Tests for pipewatch.snapshot_cli."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.snapshot_cli import snapshot
from pipewatch.snapshot import load_snapshots


def _make_collector(*names):
    collector = MagicMock()
    collector.all.return_value = [
        Metric(name=n, value=float(i), status=MetricStatus.OK)
        for i, n in enumerate(names)
    ]
    return collector


def test_take_snapshot(tmp_path):
    runner = CliRunner()
    snap_file = str(tmp_path / "snaps.jsonl")
    collector = _make_collector("latency", "errors")
    result = runner.invoke(
        snapshot,
        ["take", "--label", "ci", "--file", snap_file],
        obj={"collector": collector},
    )
    assert result.exit_code == 0
    assert "2 metrics" in result.output
    snaps = load_snapshots(Path(snap_file))
    assert len(snaps) == 1
    assert snaps[0].label == "ci"


def test_list_snapshots_empty(tmp_path):
    runner = CliRunner()
    snap_file = str(tmp_path / "snaps.jsonl")
    result = runner.invoke(snapshot, ["list", "--file", snap_file])
    assert result.exit_code == 0
    assert "No snapshots" in result.output


def test_list_snapshots_shows_entries(tmp_path):
    from pipewatch.snapshot import capture, save_snapshot
    snap_file = tmp_path / "snaps.jsonl"
    save_snapshot(capture([Metric("a", 1.0, MetricStatus.OK)], label="run1"), snap_file)
    runner = CliRunner()
    result = runner.invoke(snapshot, ["list", "--file", str(snap_file)])
    assert "run1" in result.output


def test_show_snapshot(tmp_path):
    from pipewatch.snapshot import capture, save_snapshot
    snap_file = tmp_path / "snaps.jsonl"
    save_snapshot(capture([Metric("cpu", 0.9, MetricStatus.WARNING)], label="snap0"), snap_file)
    runner = CliRunner()
    result = runner.invoke(snapshot, ["show", "0", "--file", str(snap_file)])
    assert result.exit_code == 0
    assert "cpu" in result.output


def test_show_snapshot_invalid_index(tmp_path):
    runner = CliRunner()
    snap_file = str(tmp_path / "snaps.jsonl")
    result = runner.invoke(snapshot, ["show", "5", "--file", snap_file])
    assert result.exit_code != 0
