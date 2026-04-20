"""Tests for pipewatch.exporter_rate module."""
import csv
import io
import json
from datetime import datetime, timedelta

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.rate import compute_rate
from pipewatch.exporter_rate import export_rates_json, export_rates_csv


def _make_result(name: str = "cpu", start: float = 10.0, end: float = 70.0, period: float = 60.0):
    t0 = datetime(2024, 6, 1, 0, 0, 0)
    m1 = Metric(name=name, value=start, status=MetricStatus.OK, timestamp=t0)
    m2 = Metric(name=name, value=end, status=MetricStatus.OK,
                timestamp=t0 + timedelta(seconds=period))
    return compute_rate([m1, m2])


def test_export_rates_json_valid():
    result = _make_result()
    output = export_rates_json([result])
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "cpu"
    assert "rate_per_minute" in parsed[0]


def test_export_rates_json_empty():
    output = export_rates_json([])
    assert json.loads(output) == []


def test_export_rates_csv_headers():
    result = _make_result()
    output = export_rates_csv([result])
    reader = csv.DictReader(io.StringIO(output))
    headers = reader.fieldnames
    assert "name" in headers
    assert "rate_per_minute" in headers
    assert "pct_change" in headers


def test_export_rates_csv_values():
    result = _make_result(name="latency", start=100.0, end=200.0, period=60.0)
    output = export_rates_csv([result])
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["name"] == "latency"
    assert float(rows[0]["absolute_change"]) == pytest.approx(100.0)


def test_export_rates_csv_multiple_rows():
    results = [_make_result("cpu"), _make_result("mem", 200.0, 400.0)]
    output = export_rates_csv(results)
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 2
