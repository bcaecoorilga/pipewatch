"""Export drift results to JSON and CSV formats."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.drift import DriftResult


def export_drifts_json(results: List[DriftResult]) -> str:
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_drifts_csv(results: List[DriftResult], file: io.TextIOBase | None = None) -> str:
    fieldnames = [
        "name",
        "reference_mean",
        "current_mean",
        "drift_abs",
        "drift_pct",
        "drifted",
        "threshold_pct",
    ]
    output = file or io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    if file is None:
        return output.getvalue()  # type: ignore[attr-defined]
    return ""
