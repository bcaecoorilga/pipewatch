"""Tests for pipewatch.exporter_drift."""
from __future__ import annotations

import csv
import io
import json

import pytest

from pipewatch.drift import DriftResult
from pipewatch.exporter_drift import export_drifts_csv, export_drifts_json


def _make_result(name: str = "cpu", drifted: bool = False) -> DriftResult:
    return DriftResult(
        name=name,
        reference_mean=10.0,
        current_mean=12.0,
        drift_abs=2.0,
        drift_pct=20.0,
        drifted=drifted,
        threshold_pct=20.0,
    )


def test_export_drifts_json_valid():
    results = [_make_result("cpu", True), _make_result("mem", False)]
    output = export_drifts_json(results)
    parsed = json.loads(output)
    assert len(parsed) == 2
    assert parsed[0]["name"] == "cpu"
    assert parsed[0]["drifted"] is True


def test_export_drifts_json_empty():
    output = export_drifts_json([])
    assert json.loads(output) == []


def test_export_drifts_csv_headers():
    output = export_drifts_csv([_make_result()])
    reader = csv.DictReader(io.StringIO(output))
    assert set(reader.fieldnames or []) == {
        "name", "reference_mean", "current_mean",
        "drift_abs", "drift_pct", "drifted", "threshold_pct",
    }


def test_export_drifts_csv_values():
    result = _make_result("disk", drifted=True)
    output = export_drifts_csv([result])
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["name"] == "disk"
    assert rows[0]["drifted"] == "True"


def test_export_drifts_csv_to_file():
    result = _make_result("net")
    buf = io.StringIO()
    ret = export_drifts_csv([result], file=buf)
    assert ret == ""
    buf.seek(0)
    content = buf.read()
    assert "net" in content
