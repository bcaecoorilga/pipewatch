"""Export pattern detection results to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.pattern import PatternResult


def export_patterns_json(results: List[PatternResult]) -> str:
    """Serialise *results* to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_patterns_csv(results: List[PatternResult]) -> str:
    """Serialise *results* to a CSV string."""
    buf = io.StringIO()
    fieldnames = ["metric_name", "pattern", "repeats", "is_oscillating", "dominant_status"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        row = r.to_dict()
        row["pattern"] = "|".join(row["pattern"])
        writer.writerow(row)
    return buf.getvalue()
