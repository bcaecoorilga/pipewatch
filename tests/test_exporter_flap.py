"""Tests for pipewatch.exporter_flap."""
from __future__ import annotations

import csv
import io
import json

import pytest

from pipewatch.exporter_flap import export_flaps_csv, export_flaps_json
from pipewatch.flap import FlapResult


def _make_result(name: str = "cpu", flapping: bool = True) -> FlapResult:
    return FlapResult(
        name=name,
        transitions=6,
        window=10,
        flapping=flapping,
        statuses=["ok", "warning", "ok", "warning", "ok", "warning", "ok"],
    )


def test_export_flaps_json_valid():
    results = [_make_result("cpu"), _make_result("mem", flapping=False)]
    raw = export_flaps_json(results)
    parsed = json.loads(raw)
    assert len(parsed) == 2
    assert parsed[0]["name"] == "cpu"
    assert parsed[0]["flapping"] is True
    assert parsed[1]["flapping"] is False


def test_export_flaps_json_empty():
    raw = export_flaps_json([])
    assert json.loads(raw) == []


def test_export_flaps_csv_headers():
    raw = export_flaps_csv([_make_result()])
    reader = csv.DictReader(io.StringIO(raw))
    assert set(reader.fieldnames or []) == {"name", "transitions", "window", "flapping", "statuses"}


def test_export_flaps_csv_values():
    raw = export_flaps_csv([_make_result("disk", flapping=True)])
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["name"] == "disk"
    assert rows[0]["flapping"] == "True"
    assert "|" in rows[0]["statuses"]


def test_export_flaps_csv_empty():
    raw = export_flaps_csv([])
    reader = csv.DictReader(io.StringIO(raw))
    assert list(reader) == []
