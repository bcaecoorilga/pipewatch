"""Export capacity planning results to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.capacity import CapacityResult


def export_capacity_json(results: List[CapacityResult]) -> str:
    """Serialise a list of CapacityResult objects to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_capacity_csv(results: List[CapacityResult]) -> str:
    """Serialise a list of CapacityResult objects to a CSV string."""
    fieldnames = [
        "metric_name",
        "threshold",
        "current_value",
        "slope",
        "steps_to_threshold",
        "eta_seconds",
        "horizon_steps",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    return buf.getvalue()
