"""Configuration loader for pipewatch notifiers and thresholds."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import os


@dataclass
class ThresholdConfig:
    metric_name: str
    warning: Optional[float] = None
    critical: Optional[float] = None


@dataclass
class NotifierConfig:
    type: str  # "log" or "console"
    level: str = "WARNING"  # for log notifier


@dataclass
class PipewatchConfig:
    thresholds: List[ThresholdConfig] = field(default_factory=list)
    notifiers: List[NotifierConfig] = field(default_factory=list)
    min_severity: str = "WARNING"


def load_config(path: str) -> PipewatchConfig:
    """Load configuration from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        data = json.load(f)

    thresholds = [
        ThresholdConfig(
            metric_name=t["metric_name"],
            warning=t.get("warning"),
            critical=t.get("critical"),
        )
        for t in data.get("thresholds", [])
    ]

    notifiers = [
        NotifierConfig(type=n["type"], level=n.get("level", "WARNING"))
        for n in data.get("notifiers", [])
    ]

    return PipewatchConfig(
        thresholds=thresholds,
        notifiers=notifiers,
        min_severity=data.get("min_severity", "WARNING"),
    )


def default_config() -> PipewatchConfig:
    """Return a sensible default configuration."""
    return PipewatchConfig(
        notifiers=[NotifierConfig(type="console")],
        min_severity="WARNING",
    )
