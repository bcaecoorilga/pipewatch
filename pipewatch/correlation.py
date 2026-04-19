"""Correlation analysis between pairs of metrics."""
from dataclasses import dataclass, field
from typing import Optional
from pipewatch.history import MetricHistory


@dataclass
class CorrelationResult:
    metric_a: str
    metric_b: str
    coefficient: Optional[float]
    n: int
    interpretation: str

    def to_dict(self) -> dict:
        return {
            "metric_a": self.metric_a,
            "metric_b": self.metric_b,
            "coefficient": self.coefficient,
            "n": self.n,
            "interpretation": self.interpretation,
        }


def _pearson(xs: list, ys: list) -> Optional[float]:
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    if den == 0:
        return None
    return round(num / den, 4)


def _interpret(r: Optional[float]) -> str:
    if r is None:
        return "insufficient data"
    if abs(r) >= 0.8:
        return "strong"
    if abs(r) >= 0.5:
        return "moderate"
    if abs(r) >= 0.2:
        return "weak"
    return "negligible"


def correlate(history: MetricHistory, name_a: str, name_b: str) -> CorrelationResult:
    records_a = history.for_name(name_a)
    records_b = history.for_name(name_b)
    times_a = {r.timestamp: r.value for r in records_a}
    times_b = {r.timestamp: r.value for r in records_b}
    common = sorted(set(times_a) & set(times_b))
    xs = [times_a[t] for t in common]
    ys = [times_b[t] for t in common]
    coeff = _pearson(xs, ys)
    return CorrelationResult(
        metric_a=name_a,
        metric_b=name_b,
        coefficient=coeff,
        n=len(common),
        interpretation=_interpret(coeff),
    )
