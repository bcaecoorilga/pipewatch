"""Export forecast results to JSON and CSV formats."""

import csv
import io
import json
from typing import List

from pipewatch.forecast import ForecastResult


def export_forecasts_json(results: List[ForecastResult], indent: int = 2) -> str:
    """Serialize a list of ForecastResult objects to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=indent, default=str)


def export_forecasts_csv(results: List[ForecastResult]) -> str:
    """Serialize a list of ForecastResult objects to a CSV string.

    Each row represents one forecasted step for a given metric.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["metric_name", "step", "predicted_value", "confidence", "slope", "intercept"])

    for r in results:
        for step_index, predicted in enumerate(r.predicted_values, start=1):
            writer.writerow([
                r.metric_name,
                step_index,
                round(predicted, 6),
                round(r.confidence, 6),
                round(r.slope, 6),
                round(r.intercept, 6),
            ])

    return output.getvalue()
