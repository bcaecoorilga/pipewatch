"""Tests for pipewatch.budget."""
import time

import pytest

from pipewatch.budget import BudgetRule, BudgetResult, check_budget, scan_budgets
from pipewatch.metrics import Metric, MetricStatus


def _m(name: str, value: float, age: float = 0.0) -> Metric:
    """Helper: create a Metric with a timestamp relative to now."""
    return Metric(
        name=name,
        value=value,
        status=MetricStatus.OK,
        timestamp=time.time() - age,
    )


# ---------------------------------------------------------------------------
# BudgetRule validation
# ---------------------------------------------------------------------------

def test_budget_rule_valid():
    rule = BudgetRule(name="cpu", limit=100.0, window_seconds=60.0)
    assert rule.is_valid()


def test_budget_rule_invalid_zero_limit():
    rule = BudgetRule(name="cpu", limit=0.0)
    assert not rule.is_valid()


def test_budget_rule_invalid_zero_window():
    rule = BudgetRule(name="cpu", limit=50.0, window_seconds=0.0)
    assert not rule.is_valid()


# ---------------------------------------------------------------------------
# check_budget
# ---------------------------------------------------------------------------

def test_check_budget_returns_none_for_invalid_rule():
    rule = BudgetRule(name="cpu", limit=0.0)
    result = check_budget(rule, [_m("cpu", 10.0)])
    assert result is None


def test_check_budget_no_records():
    rule = BudgetRule(name="cpu", limit=100.0, window_seconds=3600.0)
    result = check_budget(rule, [])
    assert isinstance(result, BudgetResult)
    assert result.consumed == 0.0
    assert result.exceeded is False
    assert result.contributing_count == 0


def test_check_budget_within_limit():
    rule = BudgetRule(name="errors", limit=50.0, window_seconds=3600.0)
    records = [_m("errors", 10.0), _m("errors", 15.0), _m("errors", 5.0)]
    result = check_budget(rule, records)
    assert result.consumed == pytest.approx(30.0)
    assert result.remaining == pytest.approx(20.0)
    assert result.exceeded is False
    assert result.contributing_count == 3


def test_check_budget_exceeded():
    rule = BudgetRule(name="errors", limit=20.0, window_seconds=3600.0)
    records = [_m("errors", 15.0), _m("errors", 10.0)]
    result = check_budget(rule, records)
    assert result.exceeded is True
    assert result.consumed == pytest.approx(25.0)
    assert result.remaining == pytest.approx(-5.0)


def test_check_budget_ignores_old_records():
    rule = BudgetRule(name="cpu", limit=100.0, window_seconds=60.0)
    fresh = _m("cpu", 20.0, age=10.0)
    stale = _m("cpu", 999.0, age=120.0)  # outside 60-second window
    result = check_budget(rule, [fresh, stale])
    assert result.contributing_count == 1
    assert result.consumed == pytest.approx(20.0)


def test_check_budget_ignores_different_metric_names():
    rule = BudgetRule(name="cpu", limit=100.0)
    records = [_m("memory", 50.0), _m("disk", 30.0)]
    result = check_budget(rule, records)
    assert result.contributing_count == 0


def test_budget_result_to_dict():
    rule = BudgetRule(name="cpu", limit=100.0)
    result = check_budget(rule, [_m("cpu", 40.0)])
    d = result.to_dict()
    assert d["rule_name"] == "cpu"
    assert d["consumed"] == pytest.approx(40.0)
    assert d["exceeded"] is False


# ---------------------------------------------------------------------------
# scan_budgets
# ---------------------------------------------------------------------------

def test_scan_budgets_multiple_rules():
    rules = [
        BudgetRule(name="errors", limit=10.0),
        BudgetRule(name="latency", limit=500.0),
    ]
    records = [_m("errors", 5.0), _m("latency", 600.0)]
    results = scan_budgets(rules, records)
    assert "errors" in results
    assert "latency" in results
    assert results["errors"].exceeded is False
    assert results["latency"].exceeded is True


def test_scan_budgets_skips_invalid_rules():
    rules = [BudgetRule(name="bad", limit=0.0), BudgetRule(name="ok", limit=10.0)]
    results = scan_budgets(rules, [_m("ok", 1.0)])
    assert "bad" not in results
    assert "ok" in results
