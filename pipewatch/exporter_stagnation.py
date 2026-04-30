"""Export stagnation results to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.stagnation import StagnationResult


def export_stagnations_json(results: List[StagnationResult]) -> str:
    """Serialise stagnation results to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_stagnations_csv(results: List[StagnationResult]) -> str:
    """Serialise stagnation results to a CSV string."""
    fieldnames = [
        "metric_name",
        "window",
        "unique_values",
        "min_value",
        "max_value",
        "spread",
        "is_stagnant",
        "tolerance",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    return buf.getvalue()
