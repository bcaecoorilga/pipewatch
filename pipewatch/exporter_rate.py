"""Export rate-of-change results to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.rate import RateResult


def export_rates_json(results: List[RateResult]) -> str:
    """Serialise a list of RateResult objects to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_rates_csv(results: List[RateResult]) -> str:
    """Serialise a list of RateResult objects to a CSV string."""
    fieldnames = [
        "name",
        "period_seconds",
        "start_value",
        "end_value",
        "absolute_change",
        "rate_per_second",
        "rate_per_minute",
        "pct_change",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    return buf.getvalue()
