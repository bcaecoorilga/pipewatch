"""Export pipeline metrics and reports to various formats."""

import json
import csv
import io
from typing import List, Optional
from pipewatch.reporter import PipelineReport
from pipewatch.metrics import Metric


def export_report_json(report: PipelineReport, indent: int = 2) -> str:
    """Serialize a PipelineReport to a JSON string."""
    return json.dumps(report.to_dict(), indent=indent, default=str)


def export_metrics_csv(metrics: List[Metric], file: Optional[io.StringIO] = None) -> str:
    """Serialize a list of Metric objects to CSV format.

    Returns the CSV as a string; if *file* is provided it is also written there.
    """
    fieldnames = ["name", "value", "unit", "status", "timestamp"]
    output = file or io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for metric in metrics:
        row = metric.to_dict()
        row["status"] = row.get("status", "")
        writer.writerow({k: row.get(k, "") for k in fieldnames})
    return output.getvalue() if file is None else ""


def export_report_text(report: PipelineReport) -> str:
    """Return a human-readable summary of a PipelineReport."""
    d = report.to_dict()
    lines = [
        f"Pipeline Report — {d.get('generated_at', 'N/A')}",
        f"  Total metrics : {d.get('total', 0)}",
        f"  OK            : {d.get('ok', 0)}",
        f"  Warning       : {d.get('warning', 0)}",
        f"  Critical      : {d.get('critical', 0)}",
    ]
    alerts = d.get("alerts", [])
    if alerts:
        lines.append("  Active alerts:")
        for alert in alerts:
            lines.append(f"    [{alert.get('severity','?').upper()}] {alert.get('metric_name')} — {alert.get('message')}")
    return "\n".join(lines)
