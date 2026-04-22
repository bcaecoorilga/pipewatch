"""Track and persist pipeline health scores over time."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".pipewatch", "score_history.json")


@dataclass
class ScoreRecord:
    timestamp: str
    score: float
    grade: str
    total: int
    ok: int
    warning: int
    critical: int

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "score": self.score,
            "grade": self.grade,
            "total": self.total,
            "ok": self.ok,
            "warning": self.warning,
            "critical": self.critical,
        }

    @staticmethod
    def from_dict(d: dict) -> "ScoreRecord":
        return ScoreRecord(
            timestamp=d["timestamp"],
            score=d["score"],
            grade=d["grade"],
            total=d["total"],
            ok=d["ok"],
            warning=d["warning"],
            critical=d["critical"],
        )


def _load_raw(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Score history file at '{path}' contains invalid JSON: {exc}"
            ) from exc


def _save_raw(records: List[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(records, f, indent=2)


def append_score(record: ScoreRecord, path: str = DEFAULT_PATH) -> None:
    """Append a new score record to the history file."""
    records = _load_raw(path)
    records.append(record.to_dict())
    _save_raw(records, path)


def load_score_history(path: str = DEFAULT_PATH) -> List[ScoreRecord]:
    """Load all score records from history."""
    return [ScoreRecord.from_dict(d) for d in _load_raw(path)]


def latest_score(path: str = DEFAULT_PATH) -> Optional[ScoreRecord]:
    """Return the most recently recorded score, or None."""
    records = load_score_history(path)
    return records[-1] if records else None


def clear_score_history(path: str = DEFAULT_PATH) -> None:
    """Remove all score history."""
    if os.path.exists(path):
        os.remove(path)
