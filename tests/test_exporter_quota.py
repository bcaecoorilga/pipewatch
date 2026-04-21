"""Tests for pipewatch.exporter_quota."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timedelta

import pytest

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.quota import QuotaRule, QuotaResult
from pipewatch.exporter_quota import export_quotas_json, export_quotas_csv

NOW = datetime(2024, 6, 1, 12, 0, 0)


def _make_result(name: str = "cpu", exceeded: bool = False) -> QuotaResult:
    rule = QuotaRule(name=name, max_records=10, window_seconds=60)
    return QuotaResult(
        metric_name=name,
        rule=rule,
        count_in_window=5,
        limit=10,
        exceeded=exceeded,
        window_start=NOW - timedelta(seconds=60),
        window_end=NOW,
    )


def test_export_quotas_json_valid():
    results = [_make_result("cpu"), _make_result("mem", exceeded=True)]
    output = export_quotas_json(results)
    parsed = json.loads(output)
    assert len(parsed) == 2
    assert parsed[0]["metric_name"] == "cpu"
    assert parsed[1]["exceeded"] is True


def test_export_quotas_json_empty():
    output = export_quotas_json([])
    assert json.loads(output) == []


def test_export_quotas_csv_headers():
    output = export_quotas_csv([_make_result()])
    reader = csv.DictReader(io.StringIO(output))
    assert set(reader.fieldnames or []) >= {
        "metric_name", "rule", "count_in_window", "limit", "exceeded"
    }


def test_export_quotas_csv_values():
    result = _make_result("latency", exceeded=True)
    output = export_quotas_csv([result])
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["metric_name"] == "latency"
    assert rows[0]["exceeded"] == "True"
    assert rows[0]["count_in_window"] == "5"


def test_export_quotas_csv_empty():
    output = export_quotas_csv([])
    reader = csv.DictReader(io.StringIO(output))
    assert list(reader) == []
