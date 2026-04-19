"""Tests for pipewatch.exporter."""

import json
import csv
import io
from unittest.mock import MagicMock
from pipewatch.exporter import export_report_json, export_metrics_csv, export_report_text
from pipewatch.metrics import Metric, MetricStatus


def _make_metric(name="latency", value=1.5, status=MetricStatus.OK):
    m = MagicMock(spec=Metric)
    m.to_dict.return_value = {
        "name": name,
        "value": value,
        "unit": "seconds",
        "status": status.value,
        "timestamp": "2024-01-01T00:00:00",
    }
    return m


def _make_report(total=3, ok=2, warning=1, critical=0, alerts=None):
    r = MagicMock()
    r.to_dict.return_value = {
        "generated_at": "2024-01-01T00:00:00",
        "total": total,
        "ok": ok,
        "warning": warning,
        "critical": critical,
        "alerts": alerts or [],
    }
    return r


def test_export_report_json_valid():
    report = _make_report()
    result = export_report_json(report)
    data = json.loads(result)
    assert data["total"] == 3
    assert data["ok"] == 2


def test_export_metrics_csv_headers():
    metrics = [_make_metric(), _make_metric("throughput", 99.0, MetricStatus.WARNING)]
    result = export_metrics_csv(metrics)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["name"] == "latency"
    assert rows[1]["name"] == "throughput"


def test_export_metrics_csv_to_file():
    buf = io.StringIO()
    metrics = [_make_metric()]
    export_metrics_csv(metrics, file=buf)
    buf.seek(0)
    content = buf.read()
    assert "latency" in content


def test_export_report_text_contains_counts():
    report = _make_report(total=5, ok=3, warning=1, critical=1)
    text = export_report_text(report)
    assert "Total metrics" in text
    assert "5" in text
    assert "Warning" in text


def test_export_report_text_lists_alerts():
    alerts = [{"severity": "critical", "metric_name": "lag", "message": "too high"}]
    report = _make_report(critical=1, alerts=alerts)
    text = export_report_text(report)
    assert "[CRITICAL]" in text
    assert "lag" in text
