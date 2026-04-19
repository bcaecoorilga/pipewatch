"""Export baseline data to JSON or CSV."""
import csv
import io
import json
from typing import Dict
from pipewatch.baseline import BaselineEntry, BaselineDeviation
from typing import List


def export_baseline_json(entries: Dict[str, BaselineEntry]) -> str:
    """Serialize baseline entries to a JSON string."""
    return json.dumps(
        {name: entry.to_dict() for name, entry in entries.items()},
        indent=2,
    )


def export_deviations_json(deviations: List[BaselineDeviation]) -> str:
    """Serialize baseline deviations to a JSON string."""
    return json.dumps([d.to_dict() for d in deviations], indent=2)


def export_deviations_csv(deviations: List[BaselineDeviation]) -> str:
    """Serialize baseline deviations to a CSV string."""
    output = io.StringIO()
    fieldnames = ["name", "baseline_value", "current_value", "delta", "pct_change"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for d in deviations:
        writer.writerow(d.to_dict())
    return output.getvalue()


def export_baseline_csv(entries: Dict[str, BaselineEntry]) -> str:
    """Serialize baseline entries to a CSV string."""
    output = io.StringIO()
    fieldnames = ["name", "value", "label", "captured_at"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for entry in entries.values():
        writer.writerow(entry.to_dict())
    return output.getvalue()
