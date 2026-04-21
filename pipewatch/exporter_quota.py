"""Export quota results to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.quota import QuotaResult


def export_quotas_json(results: List[QuotaResult]) -> str:
    """Serialise quota results to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_quotas_csv(results: List[QuotaResult]) -> str:
    """Serialise quota results to a CSV string."""
    buf = io.StringIO()
    fieldnames = [
        "metric_name",
        "rule",
        "count_in_window",
        "limit",
        "exceeded",
        "window_start",
        "window_end",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    return buf.getvalue()
