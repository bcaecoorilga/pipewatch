"""Metric budget tracking: define allowed value ranges and check spend against them."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics import Metric


@dataclass
class BudgetRule:
    name: str
    limit: float  # maximum cumulative value allowed in the window
    window_seconds: float = 3600.0  # rolling window size

    def is_valid(self) -> bool:
        return self.limit > 0 and self.window_seconds > 0


@dataclass
class BudgetResult:
    rule_name: str
    consumed: float
    limit: float
    remaining: float
    exceeded: bool
    contributing_count: int

    def to_dict(self) -> dict:
        return {
            "rule_name": self.rule_name,
            "consumed": self.consumed,
            "limit": self.limit,
            "remaining": self.remaining,
            "exceeded": self.exceeded,
            "contributing_count": self.contributing_count,
        }


def check_budget(
    rule: BudgetRule,
    records: List[Metric],
    now: Optional[float] = None,
) -> Optional[BudgetResult]:
    """Evaluate a BudgetRule against a list of Metric records.

    Only records whose *name* matches the rule name and whose timestamp falls
    within the rolling window are counted.
    """
    import time

    if not rule.is_valid():
        return None

    cutoff = (now if now is not None else time.time()) - rule.window_seconds
    contributing = [
        m for m in records
        if m.name == rule.name and m.timestamp >= cutoff
    ]

    consumed = sum(m.value for m in contributing)
    remaining = rule.limit - consumed
    exceeded = consumed > rule.limit

    return BudgetResult(
        rule_name=rule.name,
        consumed=consumed,
        limit=rule.limit,
        remaining=remaining,
        exceeded=exceeded,
        contributing_count=len(contributing),
    )


def scan_budgets(
    rules: List[BudgetRule],
    records: List[Metric],
    now: Optional[float] = None,
) -> Dict[str, BudgetResult]:
    """Check all rules and return a mapping of rule name -> BudgetResult."""
    results: Dict[str, BudgetResult] = {}
    for rule in rules:
        result = check_budget(rule, records, now=now)
        if result is not None:
            results[rule.name] = result
    return results
