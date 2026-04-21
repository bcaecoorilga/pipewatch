"""Capacity planning: estimate when a metric will hit a threshold given recent trend."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pipewatch.history import MetricHistory
from pipewatch.forecast import forecast, ForecastResult


@dataclass
class CapacityResult:
    metric_name: str
    threshold: float
    current_value: float
    slope: float                  # units per second
    steps_to_threshold: Optional[int]  # None if never reached within horizon
    eta_seconds: Optional[float]
    horizon_steps: int
    forecast_result: ForecastResult

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "threshold": self.threshold,
            "current_value": self.current_value,
            "slope": self.slope,
            "steps_to_threshold": self.steps_to_threshold,
            "eta_seconds": self.eta_seconds,
            "horizon_steps": self.horizon_steps,
        }


def estimate_capacity(
    history: MetricHistory,
    metric_name: str,
    threshold: float,
    horizon_steps: int = 20,
    step_seconds: float = 60.0,
) -> Optional[CapacityResult]:
    """Forecast future values and find the first step that crosses *threshold*.

    Returns None if there is insufficient history to build a forecast.
    """
    result = forecast(history, metric_name, steps=horizon_steps)
    if result is None:
        return None

    steps_to_threshold: Optional[int] = None
    eta_seconds: Optional[float] = None

    for i, predicted in enumerate(result.predicted_values, start=1):
        if (result.slope >= 0 and predicted >= threshold) or (
            result.slope < 0 and predicted <= threshold
        ):
            steps_to_threshold = i
            eta_seconds = i * step_seconds
            break

    return CapacityResult(
        metric_name=metric_name,
        threshold=threshold,
        current_value=result.last_value,
        slope=result.slope,
        steps_to_threshold=steps_to_threshold,
        eta_seconds=eta_seconds,
        horizon_steps=horizon_steps,
        forecast_result=result,
    )


def scan_capacity(
    history: MetricHistory,
    thresholds: dict[str, float],
    horizon_steps: int = 20,
    step_seconds: float = 60.0,
) -> list[CapacityResult]:
    """Run capacity estimation for every metric that has a threshold entry."""
    results = []
    for name, threshold in thresholds.items():
        r = estimate_capacity(history, name, threshold, horizon_steps, step_seconds)
        if r is not None:
            results.append(r)
    return results
