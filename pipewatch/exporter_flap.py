"""Export flap detection results to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.flap import FlapResult


def export_flaps_json(results: List[FlapResult]) -> str:
    """Serialise flap results to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_flaps_csv(results: List[FlapResult]) -> str:
    """Serialise flap results to CSV."""
    output = io.StringIO()
    fieldnames = ["name", "transitions", "window", "flapping", "statuses"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        row = r.to_dict()
        row["statuses"] = "|".join(row["statuses"])
        writer.writerow(row)
    return output.getvalue()
