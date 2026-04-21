"""Tests for pipewatch.exporter_pattern."""
from __future__ import annotations

import csv
import io
import json

import pytest

from pipewatch.pattern import PatternResult
from pipewatch.exporter_pattern import export_patterns_json, export_patterns_csv


def _make_result(name: str = "cpu") -> PatternResult:
    return PatternResult(
        metric_name=name,
        pattern=["ok", "warning"],
        repeats=3,
        is_oscillating=True,
        dominant_status="ok",
    )


def test_export_patterns_json_valid():
    results = [_make_result("cpu"), _make_result("mem")]
    output = export_patterns_json(results)
    data = json.loads(output)
    assert len(data) == 2
    assert data[0]["metric_name"] == "cpu"
    assert data[1]["metric_name"] == "mem"


def test_export_patterns_json_empty():
    output = export_patterns_json([])
    assert json.loads(output) == []


def test_export_patterns_csv_headers():
    output = export_patterns_csv([_make_result()])
    reader = csv.DictReader(io.StringIO(output))
    assert set(reader.fieldnames or []) == {
        "metric_name", "pattern", "repeats", "is_oscillating", "dominant_status"
    }


def test_export_patterns_csv_values():
    result = _make_result("cpu")
    output = export_patterns_csv([result])
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["metric_name"] == "cpu"
    assert rows[0]["pattern"] == "ok|warning"
    assert rows[0]["repeats"] == "3"
    assert rows[0]["is_oscillating"] == "True"


def test_export_patterns_csv_empty():
    output = export_patterns_csv([])
    reader = csv.DictReader(io.StringIO(output))
    assert list(reader) == []
