"""Export latency results to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.latency import LatencyResult


def export_latencies_json(results: List[LatencyResult]) -> str:
    """Serialize latency results to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_latencies_csv(results: List[LatencyResult]) -> str:
    """Serialize latency results to a CSV string."""
    buf = io.StringIO()
    fieldnames = [
        "metric_name",
        "mean_latency",
        "max_latency",
        "min_latency",
        "p95_latency",
        "classification",
        "sample_count",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    return buf.getvalue()
