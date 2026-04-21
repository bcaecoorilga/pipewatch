"""Tests for pipewatch.exporter_heatmap."""
from __future__ import annotations

import csv
import io
import json
from unittest.mock import MagicMock

import pytest

from pipewatch.metrics import MetricStatus
from pipewatch.heatmap import Heatmap, HeatmapRow, HeatmapCell
from pipewatch.exporter_heatmap import export_heatmap_json, export_heatmap_csv


def _make_heatmap() -> Heatmap:
    cells = [
        HeatmapCell(bucket="2024-06-01T10", status=MetricStatus.OK, count=3),
        HeatmapCell(bucket="2024-06-01T11", status=MetricStatus.WARNING, count=1),
    ]
    rows = [HeatmapRow(name="cpu", cells=cells)]
    return Heatmap(rows=rows, bucket_size_hours=1)


def test_export_heatmap_json_valid():
    hm = _make_heatmap()
    result = export_heatmap_json(hm)
    data = json.loads(result)
    assert data["bucket_size_hours"] == 1
    assert data["rows"][0]["name"] == "cpu"
    assert data["rows"][0]["cells"][0]["status"] == "ok"


def test_export_heatmap_json_empty():
    hm = Heatmap(rows=[])
    result = export_heatmap_json(hm)
    data = json.loads(result)
    assert data["rows"] == []


def test_export_heatmap_csv_headers():
    hm = _make_heatmap()
    result = export_heatmap_csv(hm)
    reader = csv.reader(io.StringIO(result))
    headers = next(reader)
    assert headers == ["name", "bucket", "status", "count"]


def test_export_heatmap_csv_values():
    hm = _make_heatmap()
    result = export_heatmap_csv(hm)
    rows = list(csv.reader(io.StringIO(result)))
    # rows[0] is header; rows[1] is first data row
    assert rows[1][0] == "cpu"
    assert rows[1][1] == "2024-06-01T10"
    assert rows[1][2] == "ok"
    assert rows[1][3] == "3"


def test_export_heatmap_csv_row_count():
    hm = _make_heatmap()
    result = export_heatmap_csv(hm)
    rows = [r for r in csv.reader(io.StringIO(result)) if r]
    # 1 header + 2 data rows
    assert len(rows) == 3
