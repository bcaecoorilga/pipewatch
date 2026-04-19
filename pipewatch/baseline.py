"""Baseline management: capture and compare metric baselines."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from pipewatch.metrics import Metric

DEFAULT_BASELINE_PATH = ".pipewatch_baselines.json"


@dataclass
class BaselineEntry:
    name: str
    value: float
    captured_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    label: str = "default"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "captured_at": self.captured_at,
            "label": self.label,
        }


@dataclass
class BaselineDeviation:
    name: str
    baseline_value: float
    current_value: float
    delta: float
    pct_change: Optional[float]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "delta": self.delta,
            "pct_change": self.pct_change,
        }


def save_baseline(metrics: List[Metric], label: str = "default", path: str = DEFAULT_BASELINE_PATH) -> List[BaselineEntry]:
    entries = [BaselineEntry(name=m.name, value=m.value, label=label) for m in metrics]
    existing = _load_raw(path)
    existing = [e for e in existing if e["label"] != label]
    existing.extend([e.to_dict() for e in entries])
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)
    return entries


def load_baseline(label: str = "default", path: str = DEFAULT_BASELINE_PATH) -> Dict[str, BaselineEntry]:
    raw = _load_raw(path)
    result = {}
    for r in raw:
        if r.get("label") == label:
            result[r["name"]] = BaselineEntry(**r)
    return result


def compare_to_baseline(metrics: List[Metric], label: str = "default", path: str = DEFAULT_BASELINE_PATH) -> List[BaselineDeviation]:
    baseline = load_baseline(label, path)
    deviations = []
    for m in metrics:
        if m.name not in baseline:
            continue
        b = baseline[m.name]
        delta = m.value - b.value
        pct = (delta / b.value * 100) if b.value != 0 else None
        deviations.append(BaselineDeviation(name=m.name, baseline_value=b.value, current_value=m.value, delta=delta, pct_change=pct))
    return deviations


def _load_raw(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)
