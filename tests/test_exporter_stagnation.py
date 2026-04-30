"""Tests for pipewatch.exporter_stagnation."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime

import pytest

from pipewatch.stagnation import StagnationResult
from pipewatch.exporter_stagnation import export_stagnations_json, export_stagnations_csv


def _make_result(name: str = "cpu", stagnant: bool = True) -> StagnationResult:
    return StagnationResult(
        metric_name=name,
        window=10,
        unique_values=1 if stagnant else 5,
        min_value=42.0,
        max_value=42.0 if stagnant else 50.0,
        spread=0.0 if stagnant else 8.0,
        is_stagnant=stagnant,
        tolerance=0.0,
    )


def test_export_stagnations_json_valid():
    results = [_make_result("cpu"), _make_result("mem", stagnant=False)]
    output = export_stagnations_json(results)
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    assert parsed[0]["metric_name"] == "cpu"
    assert parsed[0]["is_stagnant"] is True


def test_export_stagnations_json_empty():
    output = export_stagnations_json([])
    assert json.loads(output) == []


def test_export_stagnations_csv_headers():
    output = export_stagnations_csv([])
    reader = csv.reader(io.StringIO(output))
    headers = next(reader)
    assert "metric_name" in headers
    assert "is_stagnant" in headers
    assert "spread" in headers


def test_export_stagnations_csv_values():
    results = [_make_result("disk", stagnant=True)]
    output = export_stagnations_csv(results)
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["metric_name"] == "disk"
    assert rows[0]["is_stagnant"] == "True"
    assert float(rows[0]["spread"]) == pytest.approx(0.0)


def test_export_stagnations_csv_multiple_rows():
    results = [_make_result("a"), _make_result("b", stagnant=False), _make_result("c")]
    output = export_stagnations_csv(results)
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 3
    assert {r["metric_name"] for r in rows} == {"a", "b", "c"}
