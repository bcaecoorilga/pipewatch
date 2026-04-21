"""Export window-alert results to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.window_alert import WindowAlertResult


def export_window_alerts_json(results: List[WindowAlertResult]) -> str:
    """Return a JSON string of all window-alert results."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_window_alerts_csv(results: List[WindowAlertResult]) -> str:
    """Return a CSV string of all window-alert results."""
    buf = io.StringIO()
    fieldnames = [
        "metric_name",
        "level",
        "window",
        "min_breaches",
        "readings_checked",
        "breach_count",
        "fired",
        "latest_value",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    return buf.getvalue()
