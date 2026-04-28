"""Export envelope detection results to JSON and CSV."""

from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.envelope import EnvelopeResult


def export_envelopes_json(results: List[EnvelopeResult]) -> str:
    """Serialize a list of EnvelopeResult objects to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_envelopes_csv(results: List[EnvelopeResult]) -> str:
    """Serialize a list of EnvelopeResult objects to a CSV string."""
    fieldnames = [
        "name",
        "current_value",
        "mean",
        "lower_bound",
        "upper_bound",
        "tolerance",
        "inside",
        "deviation",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    return buf.getvalue()
