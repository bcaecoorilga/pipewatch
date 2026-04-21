"""Export heatmap data to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.heatmap import Heatmap


def export_heatmap_json(heatmap: Heatmap) -> str:
    """Serialise a Heatmap to a JSON string."""
    return json.dumps(heatmap.to_dict(), indent=2)


def export_heatmap_csv(heatmap: Heatmap) -> str:
    """Serialise a Heatmap to CSV with columns: name, bucket, status, count."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["name", "bucket", "status", "count"])
    for row in heatmap.rows:
        for cell in row.cells:
            writer.writerow([row.name, cell.bucket, cell.status.value, cell.count])
    return buf.getvalue()
