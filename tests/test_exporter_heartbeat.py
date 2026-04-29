"""Tests for pipewatch.exporter_heartbeat."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime

import pytest

from pipewatch.heartbeat import HeartbeatResult
from pipewatch.exporter_heartbeat import export_heartbeat_json, export_heartbeat_csv


def _make_result(name: str = "cpu", alive: bool = True) -> HeartbeatResult:
    return HeartbeatResult(
        name=name,
        expected_interval_s=60.0,
        last_seen=datetime(2024, 1, 1, 12, 0, 0),
        seconds_since=5.0,
        is_alive=alive,
        message=f"{name!r} last seen 5.0s ago",
    )


def test_export_heartbeat_json_valid():
    results = [_make_result("cpu"), _make_result("mem", alive=False)]
    output = export_heartbeat_json(results)
    data = json.loads(output)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] == "cpu"
    assert data[1]["is_alive"] is False


def test_export_heartbeat_json_empty():
    output = export_heartbeat_json([])
    data = json.loads(output)
    assert data == []


def test_export_heartbeat_csv_headers():
    output = export_heartbeat_csv([_make_result()])
    reader = csv.DictReader(io.StringIO(output))
    assert set(reader.fieldnames or []) >= {"name", "is_alive", "seconds_since", "expected_interval_s"}


def test_export_heartbeat_csv_values():
    output = export_heartbeat_csv([_make_result("disk", alive=False)])
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["name"] == "disk"
    assert rows[0]["is_alive"] == "False"


def test_export_heartbeat_csv_empty():
    output = export_heartbeat_csv([])
    reader = csv.DictReader(io.StringIO(output))
    assert list(reader) == []
