"""Tests for pipewatch.health_cli."""

import json
from unittest.mock import MagicMock

from click.testing import CliRunner

from pipewatch.health_cli import health
from pipewatch.metrics import Metric, MetricStatus


def _make_collector(*statuses: MetricStatus):
    collector = MagicMock()
    collector.all.return_value = [
        Metric(name=f"m{i}", value=float(i), status=s)
        for i, s in enumerate(statuses)
    ]
    return collector


def test_score_no_metrics():
    runner = CliRunner()
    collector = _make_collector()
    result = runner.invoke(health, ["score"], obj={"collector": collector})
    assert result.exit_code == 0
    assert "No metrics" in result.output


def test_score_text_output():
    runner = CliRunner()
    collector = _make_collector(MetricStatus.OK, MetricStatus.OK, MetricStatus.WARNING)
    result = runner.invoke(health, ["score"], obj={"collector": collector})
    assert result.exit_code == 0
    assert "Health Score" in result.output
    assert "Total" in result.output


def test_score_json_output():
    runner = CliRunner()
    collector = _make_collector(MetricStatus.OK, MetricStatus.CRITICAL)
    result = runner.invoke(health, ["score", "--format", "json"], obj={"collector": collector})
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "score" in data
    assert "grade" in data
    assert data["total"] == 2


def test_score_all_critical_grade_f():
    runner = CliRunner()
    collector = _make_collector(MetricStatus.CRITICAL, MetricStatus.CRITICAL)
    result = runner.invoke(health, ["score", "--format", "json"], obj={"collector": collector})
    data = json.loads(result.output)
    assert data["grade"] == "F"
    assert data["score"] == 0.0
