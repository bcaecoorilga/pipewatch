"""Tests for pipewatch.baseline."""
import pytest
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.baseline import (
    save_baseline,
    load_baseline,
    compare_to_baseline,
    BaselineEntry,
    BaselineDeviation,
)


def _m(name, value):
    return Metric(name=name, value=value, unit="count", status=MetricStatus.OK)


def test_save_and_load_roundtrip(tmp_path):
    path = str(tmp_path / "baselines.json")
    metrics = [_m("rows", 100.0), _m("errors", 5.0)]
    save_baseline(metrics, label="v1", path=path)
    loaded = load_baseline(label="v1", path=path)
    assert "rows" in loaded
    assert loaded["rows"].value == 100.0
    assert loaded["errors"].value == 5.0


def test_load_missing_label_returns_empty(tmp_path):
    path = str(tmp_path / "baselines.json")
    result = load_baseline(label="nonexistent", path=path)
    assert result == {}


def test_save_overwrites_same_label(tmp_path):
    path = str(tmp_path / "baselines.json")
    save_baseline([_m("rows", 50.0)], label="v1", path=path)
    save_baseline([_m("rows", 200.0)], label="v1", path=path)
    loaded = load_baseline(label="v1", path=path)
    assert loaded["rows"].value == 200.0


def test_compare_returns_deviations(tmp_path):
    path = str(tmp_path / "baselines.json")
    save_baseline([_m("rows", 100.0)], label="default", path=path)
    current = [_m("rows", 120.0)]
    deviations = compare_to_baseline(current, label="default", path=path)
    assert len(deviations) == 1
    d = deviations[0]
    assert d.name == "rows"
    assert d.delta == pytest.approx(20.0)
    assert d.pct_change == pytest.approx(20.0)


def test_compare_skips_unknown_metrics(tmp_path):
    path = str(tmp_path / "baselines.json")
    save_baseline([_m("rows", 100.0)], label="default", path=path)
    current = [_m("latency", 0.5)]
    deviations = compare_to_baseline(current, label="default", path=path)
    assert deviations == []


def test_pct_change_zero_baseline(tmp_path):
    path = str(tmp_path / "baselines.json")
    save_baseline([_m("errors", 0.0)], label="default", path=path)
    current = [_m("errors", 3.0)]
    deviations = compare_to_baseline(current, label="default", path=path)
    assert deviations[0].pct_change is None


def test_baseline_entry_to_dict():
    e = BaselineEntry(name="rows", value=42.0, label="test")
    d = e.to_dict()
    assert d["name"] == "rows"
    assert d["value"] == 42.0
    assert d["label"] == "test"
    assert "captured_at" in d
