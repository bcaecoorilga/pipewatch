"""Export heartbeat results to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from pipewatch.heartbeat import HeartbeatResult


def export_heartbeat_json(results: List[HeartbeatResult]) -> str:
    """Serialize heartbeat results to a JSON string."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def export_heartbeat_csv(results: List[HeartbeatResult]) -> str:
    """Serialize heartbeat results to a CSV string."""
    buf = io.StringIO()
    fieldnames = ["name", "expected_interval_s", "last_seen", "seconds_since", "is_alive", "message"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow(r.to_dict())
    return buf.getvalue()
