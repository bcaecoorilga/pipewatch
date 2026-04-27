"""Export noise detection results to JSON and CSV formats."""

from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.noise import NoiseResult


def export_noise_json(results: List[NoiseResult]) -> str:
    """Serialize a list of NoiseResult objects to a JSON string.

    Args:
        results: List of NoiseResult instances to export.

    Returns:
        A JSON-formatted string representing all results.
    """
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_noise_csv(results: List[NoiseResult]) -> str:
    """Serialize a list of NoiseResult objects to a CSV string.

    The CSV includes one row per result with columns for metric name,
    coefficient of variation, noise level classification, mean, std_dev,
    and sample count.

    Args:
        results: List of NoiseResult instances to export.

    Returns:
        A CSV-formatted string with a header row followed by data rows.
    """
    output = io.StringIO()
    fieldnames = [
        "metric_name",
        "coefficient_of_variation",
        "noise_level",
        "mean",
        "std_dev",
        "sample_count",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        d = r.to_dict()
        writer.writerow({
            "metric_name": d.get("metric_name", ""),
            "coefficient_of_variation": d.get("coefficient_of_variation", ""),
            "noise_level": d.get("noise_level", ""),
            "mean": d.get("mean", ""),
            "std_dev": d.get("std_dev", ""),
            "sample_count": d.get("sample_count", ""),
        })
    return output.getvalue()
