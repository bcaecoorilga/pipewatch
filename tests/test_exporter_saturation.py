"""Tests for pipewatch.exporter_saturation."""
from __future__ import annotations

import csv
import io
import json

from pipewatch.saturation import SaturationResult
from pipewatch.exporter_saturation import export_saturations_json, export_saturations_csv


def _make_result(name: str, value: float, ceiling: float, pct: float, saturated: bool, label: str) -> SaturationResult:
    return SaturationResult(
        metric_name=name,
        current_value=value,
        ceiling=ceiling,
        saturation_pct=pct,
        is_saturated=saturated,
        label=label,
    )


def test_export_saturations_json_valid():
    results = [
        _make_result("cpu", 90.0, 100.0, 90.0, True, "critical"),
        _make_result("mem", 50.0, 100.0, 50.0, False, "ok"),
    ]
    raw = export_saturations_json(results)
    data = json.loads(raw)
    assert len(data) == 2
    assert data[0]["metric_name"] == "cpu"
    assert data[1]["label"] == "ok"


def test_export_saturations_json_empty():
    raw = export_saturations_json([])
    assert json.loads(raw) == []


def test_export_saturations_csv_headers():
    raw = export_saturations_csv([])
    reader = csv.DictReader(io.StringIO(raw))
    assert set(reader.fieldnames or []) == {
        "metric_name", "current_value", "ceiling", "saturation_pct", "is_saturated", "label"
    }


def test_export_saturations_csv_values():
    results = [_make_result("disk", 85.0, 100.0, 85.0, False, "warning")]
    raw = export_saturations_csv(results)
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["metric_name"] == "disk"
    assert rows[0]["label"] == "warning"


def test_export_saturations_csv_multiple_rows():
    results = [
        _make_result("a", 10.0, 100.0, 10.0, False, "ok"),
        _make_result("b", 95.0, 100.0, 95.0, True, "critical"),
    ]
    raw = export_saturations_csv(results)
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[1]["metric_name"] == "b"
