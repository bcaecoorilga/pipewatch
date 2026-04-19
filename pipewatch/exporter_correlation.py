"""Export correlation results to JSON or CSV."""
import json
import csv
import io
from typing import List
from pipewatch.correlation import CorrelationResult


def export_correlations_json(results: List[CorrelationResult]) -> str:
    """Serialize a list of CorrelationResult objects to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_correlations_csv(results: List[CorrelationResult], path: str = None) -> str:
    """Serialize correlation results to CSV; write to path if given, else return string."""
    fields = ["metric_a", "metric_b", "coefficient", "n", "interpretation"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    content = output.getvalue()
    if path:
        with open(path, "w", newline="") as f:
            f.write(content)
    return content
