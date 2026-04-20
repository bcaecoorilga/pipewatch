"""Tests for pipewatch.pipeline_score_history."""

import os
import pytest
from datetime import datetime, timezone

from pipewatch.pipeline_score_history import (
    ScoreRecord,
    append_score,
    load_score_history,
    latest_score,
    clear_score_history,
)


@pytest.fixture
def tmp_path_file(tmp_path):
    return str(tmp_path / "score_history.json")


def _make_record(score: float = 85.0, grade: str = "B") -> ScoreRecord:
    return ScoreRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),
        score=score,
        grade=grade,
        total=10,
        ok=8,
        warning=1,
        critical=1,
    )


def test_load_empty_returns_empty(tmp_path_file):
    result = load_score_history(tmp_path_file)
    assert result == []


def test_latest_score_empty_returns_none(tmp_path_file):
    assert latest_score(tmp_path_file) is None


def test_append_and_load_roundtrip(tmp_path_file):
    record = _make_record(score=90.0, grade="A")
    append_score(record, tmp_path_file)
    loaded = load_score_history(tmp_path_file)
    assert len(loaded) == 1
    assert loaded[0].score == 90.0
    assert loaded[0].grade == "A"
    assert loaded[0].total == 10
    assert loaded[0].ok == 8


def test_append_multiple_preserves_order(tmp_path_file):
    r1 = _make_record(score=70.0, grade="C")
    r2 = _make_record(score=95.0, grade="A")
    append_score(r1, tmp_path_file)
    append_score(r2, tmp_path_file)
    loaded = load_score_history(tmp_path_file)
    assert len(loaded) == 2
    assert loaded[0].score == 70.0
    assert loaded[1].score == 95.0


def test_latest_score_returns_last(tmp_path_file):
    append_score(_make_record(score=60.0, grade="D"), tmp_path_file)
    append_score(_make_record(score=80.0, grade="B"), tmp_path_file)
    last = latest_score(tmp_path_file)
    assert last is not None
    assert last.score == 80.0
    assert last.grade == "B"


def test_clear_score_history(tmp_path_file):
    append_score(_make_record(), tmp_path_file)
    clear_score_history(tmp_path_file)
    assert not os.path.exists(tmp_path_file)
    assert load_score_history(tmp_path_file) == []


def test_score_record_to_dict():
    r = _make_record(score=75.5, grade="C")
    d = r.to_dict()
    assert d["score"] == 75.5
    assert d["grade"] == "C"
    assert "timestamp" in d
    assert d["warning"] == 1
    assert d["critical"] == 1
