"""Tests for pipewatch.exporter_latency."""
from __future__ import annotations

import csv
import io
import json

import pytest

from pipewatch.exporter_latency import export_latencies_csv, export_latencies_json
from pipewatch.latency import LatencyResult


def _make_result(name: str = "pipe.test", classification: str = "low") -> LatencyResult:
    return LatencyResult(
        metric_name=name,
        mean_latency=0.5,
        max_latency=1.2,
        min_latency=0.1,
        p95_latency=1.0,
        classification=classification,
        sample_count=5,
    )


def test_export_latencies_json_valid():
    results = [_make_result("a"), _make_result("b", "high")]
    output = export_latencies_json(results)
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    assert parsed[0]["metric_name"] == "a"
    assert parsed[1]["classification"] == "high"


def test_export_latencies_json_empty():
    output = export_latencies_json([])
    assert json.loads(output) == []


def test_export_latencies_csv_headers():
    output = export_latencies_csv([_make_result()])
    reader = csv.DictReader(io.StringIO(output))
    assert set(reader.fieldnames or []) == {
        "metric_name",
        "mean_latency",
        "max_latency",
        "min_latency",
        "p95_latency",
        "classification",
        "sample_count",
    }


def test_export_latencies_csv_values():
    result = _make_result("pipe.x", "moderate")
    output = export_latencies_csv([result])
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["metric_name"] == "pipe.x"
    assert rows[0]["classification"] == "moderate"
    assert rows[0]["sample_count"] == "5"


def test_export_latencies_csv_empty():
    output = export_latencies_csv([])
    reader = csv.DictReader(io.StringIO(output))
    assert list(reader) == []
