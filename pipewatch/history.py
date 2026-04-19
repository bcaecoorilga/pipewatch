"""Metric history storage and retrieval for pipewatch."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List, Optional

from pipewatch.metrics import Metric


DEFAULT_HISTORY_PATH = os.path.expanduser("~/.pipewatch/history.json")


def _load_raw(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_raw(records: List[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(records, f, indent=2, default=str)


class MetricHistory:
    """Persists and queries historical metric recordings."""

    def __init__(self, path: str = DEFAULT_HISTORY_PATH) -> None:
        self.path = path

    def append(self, metric: Metric) -> None:
        records = _load_raw(self.path)
        records.append(metric.to_dict())
        _save_raw(records, self.path)

    def all(self) -> List[dict]:
        return _load_raw(self.path)

    def for_name(self, name: str) -> List[dict]:
        return [r for r in self.all() if r.get("name") == name]

    def since(self, dt: datetime) -> List[dict]:
        result = []
        for r in self.all():
            ts = r.get("timestamp", "")
            try:
                if datetime.fromisoformat(str(ts)) >= dt:
                    result.append(r)
            except (ValueError, TypeError):
                pass
        return result

    def clear(self) -> None:
        _save_raw([], self.path)
