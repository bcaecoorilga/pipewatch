"""Persistence layer for saving and loading collector state to/from disk."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from pipewatch.metrics import Metric, MetricStatus

_DEFAULT_PATH = Path(".pipewatch") / "state.json"


def _metric_from_dict(d: dict) -> Metric:
    return Metric(
        name=d["name"],
        value=d["value"],
        timestamp=d["timestamp"],
        status=MetricStatus(d["status"]),
        tags=d.get("tags", {}),
    )


def save_state(metrics: List[Metric], path: Optional[Path] = None) -> Path:
    """Persist a list of Metric objects to a JSON file.

    Creates parent directories if they do not exist.
    Returns the path written to.
    """
    target = Path(path) if path else _DEFAULT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)

    payload = [m.to_dict() for m in metrics]
    with target.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return target


def load_state(path: Optional[Path] = None) -> List[Metric]:
    """Load persisted Metric objects from a JSON file.

    Returns an empty list if the file does not exist or is malformed.
    """
    target = Path(path) if path else _DEFAULT_PATH
    if not target.exists():
        return []
    try:
        with target.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        return [_metric_from_dict(d) for d in raw]
    except (json.JSONDecodeError, KeyError, ValueError):
        return []


def clear_state(path: Optional[Path] = None) -> bool:
    """Delete the persisted state file.

    Returns True if the file was deleted, False if it did not exist.
    """
    target = Path(path) if path else _DEFAULT_PATH
    if target.exists():
        target.unlink()
        return True
    return False
