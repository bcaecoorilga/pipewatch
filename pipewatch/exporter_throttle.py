"""Export throttle detection results to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.throttle import ThrottleResult


def export_throttles_json(results: List[ThrottleResult]) -> str:
    """Serialise throttle results to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_throttles_csv(results: List[ThrottleResult]) -> str:
    """Serialise throttle results to a CSV string."""
    buf = io.StringIO()
    fieldnames = ["name", "current_rate", "ceiling", "throttled", "ratio", "message"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    return buf.getvalue()
