"""Tests for pipewatch.retention."""

import json
import os
from datetime import datetime, timedelta

import pytest

from pipewatch.retention import RetentionPolicy, PruneResult, _apply_policy, prune


def _ts(hours_ago: float) -> str:
    return (datetime.utcnow() - timedelta(hours=hours_ago)).isoformat()


def _make_raw(records_spec: list) -> list:
    """Build a list of raw records from a list of hours_ago floats.

    Each record has a 'timestamp' (ISO-format string) and a 'value' (float).
    Records are ordered oldest-first, matching typical append order.
    """
    return [{"timestamp": _ts(h), "value": float(i)} for i, h in enumerate(records_spec)]


# ---------------------------------------------------------------------------
# _apply_policy
# ---------------------------------------------------------------------------

def test_apply_policy_max_age_drops_old():
    records = _make_raw([5.0, 2.0, 0.5])  # 5h, 2h, 0.5h ago
    policy = RetentionPolicy(max_age_hours=3.0)
    result = _apply_policy(records, policy)
    assert len(result) == 2  # 5h record dropped


def test_apply_policy_max_records_keeps_most_recent():
    records = _make_raw([4.0, 3.0, 2.0, 1.0, 0.5])
    policy = RetentionPolicy(max_records=3)
    result = _apply_policy(records, policy)
    assert len(result) == 3
    # The three most recent should be kept (tail of list)
    assert result == records[-3:]


def test_apply_policy_combined():
    records = _make_raw([10.0, 5.0, 2.0, 1.0, 0.5])
    policy = RetentionPolicy(max_age_hours=6.0, max_records=2)
    result = _apply_policy(records, policy)
    # After age filter: [5h, 2h, 1h, 0.5h] → 4 records; then keep last 2
    assert len(result) == 2


def test_apply_policy_no_op_when_all_fresh():
    records = _make_raw([0.1, 0.2, 0.3])
    policy = RetentionPolicy(max_age_hours=24.0)
    result = _apply_policy(records, policy)
    assert len(result) == 3


def test_apply_policy_empty_input():
    """Applying a policy to an empty record list should return an empty list."""
    policy = RetentionPolicy(max_age_hours=1.0, max_records=10)
    result = _apply_policy([], policy)
    assert result == []


def test_apply_policy_all_records_pruned_by_age():
    """When every record is older than max_age_hours, result should be empty."""
    records = _make_raw([10.0, 20.0, 30.0])
    policy = RetentionPolicy(max_age_hours=5.0)
    result = _apply_policy(records, policy)
    assert result == []


# ---------------------------------------------------------------------------
# RetentionPolicy.is_valid
# ---------------------------------------------------------------------------

def test_policy_invalid_when_neither_set():
    assert RetentionPolicy().is_valid() is False


def test_policy_valid_with_max_age():
    assert RetentionPolicy(max_age_hours=1.0).is_valid() is True


def test_policy_valid_with_max_records():
    assert RetentionPolicy(max_records=10).is_valid() is True


# ---------------------------------------------------------------------------
# prune (integration with file I/O)
# ---------------------------------------------------------------------------

def test_prune_writes_back_and_returns_results(tmp_path):
    path = str(tmp_path / "history.json")
    raw = {
        "cpu": _make_raw([5.0, 1.0, 0.5]),
        "mem": _make_raw([10.0, 0.2]),
    }
    with open(path, "w") as f:
        json.dump(raw, f)

    policy = RetentionPolicy(max_age_hours=3.0)
    results = prune(path, policy)

    assert len(results) == 2
    cpu_result = next(r for r in results if r.metric_name == "cpu")
    assert cpu_result.records_before == 3
    assert cpu_result.records_after == 2
    assert cpu_result.pruned == 1

    # Verify file was updated on disk
    with open(path) as f:
        written = json.load(f)
    assert len(written["cpu"]) == 2
    assert len(written["mem"]) == 1
