"""Export saturation results to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.saturation import SaturationResult


def export_saturations_json(results: List[SaturationResult]) -> str:
    """Serialize saturation results to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_saturations_csv(results: List[SaturationResult]) -> str:
    """Serialize saturation results to a CSV string."""
    output = io.StringIO()
    fieldnames = ["metric_name", "current_value", "ceiling", "saturation_pct", "is_saturated", "label"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    return output.getvalue()
