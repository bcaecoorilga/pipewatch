"""Export momentum results to JSON and CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.momentum import MomentumResult


def export_momentum_json(results: List[MomentumResult]) -> str:
    """Serialise a list of MomentumResult objects to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_momentum_csv(results: List[MomentumResult], filepath: str | None = None) -> str:
    """Serialise momentum results to CSV.

    If *filepath* is provided the CSV is also written to that file.
    Returns the CSV string regardless.
    """
    fieldnames = ["name", "momentum", "direction", "sample_count", "threshold", "is_significant"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    content = buf.getvalue()
    if filepath:
        with open(filepath, "w", newline="") as fh:
            fh.write(content)
    return content
