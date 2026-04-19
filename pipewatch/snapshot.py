"""Snapshot: capture and persist pipeline state at a point in time."""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from pipewatch.metrics import Metric, to_dict as metric_to_dict


@dataclass
class Snapshot:
    timestamp: float = field(default_factory=time.time)
    metrics: List[dict] = field(default_factory=list)
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "label": self.label,
            "metrics": self.metrics,
        }


def capture(metrics: List[Metric], label: Optional[str] = None) -> Snapshot:
    """Create a snapshot from a list of Metric objects."""
    return Snapshot(
        metrics=[metric_to_dict(m) for m in metrics],
        label=label,
    )


def save_snapshot(snapshot: Snapshot, path: Path) -> None:
    """Append a snapshot to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(snapshot.to_dict()) + "\n")


def load_snapshots(path: Path) -> List[Snapshot]:
    """Load all snapshots from a JSONL file."""
    if not path.exists():
        return []
    snapshots = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            snapshots.append(
                Snapshot(
                    timestamp=data["timestamp"],
                    label=data.get("label"),
                    metrics=data.get("metrics", []),
                )
            )
    return snapshots
