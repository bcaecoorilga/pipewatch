"""Export aggregated metric results to JSON or CSV."""

import json
import csv
import io
from typing import Dict
from pipewatch.aggregator import AggregateResult


def export_aggregate_json(results: Dict[str, AggregateResult]) -> str:
    """Serialize aggregate results to a JSON string."""
    return json.dumps({k: v.to_dict() for k, v in results.items()}, indent=2)


def export_aggregate_csv(results: Dict[str, AggregateResult]) -> str:
    """Serialize aggregate results to a CSV string."""
    output = io.StringIO()
    fieldnames = ["name", "count", "mean", "min", "max", "latest",
                  "status_ok", "status_warning", "status_critical"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for result in results.values():
        sc = result.status_counts
        writer.writerow({
            "name": result.name,
            "count": result.count,
            "mean": result.mean,
            "min": result.min,
            "max": result.max,
            "latest": result.latest,
            "status_ok": sc.get("ok", 0),
            "status_warning": sc.get("warning", 0),
            "status_critical": sc.get("critical", 0),
        })
    return output.getvalue()
