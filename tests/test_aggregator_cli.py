"""Tests for pipewatch.aggregator_cli."""

from click.testing import CliRunner
from pipewatch.aggregator_cli import aggregator
from pipewatch.collector import MetricCollector
from pipewatch.metrics import MetricStatus
import json


def _make_collector():
    c = MetricCollector()
    c.record("cpu", 10.0)
    c.record("cpu", 20.0)
    c.record("mem", 55.0)
    return c


def test_summary_no_metrics():
    runner = CliRunner()
    result = runner.invoke(aggregator, ["summary"], obj={"collector": MetricCollector()})
    assert result.exit_code == 0
    assert "No metrics found" in result.output


def test_summary_text_output():
    runner = CliRunner()
    collector = _make_collector()
    result = runner.invoke(aggregator, ["summary"], obj={"collector": collector})
    assert result.exit_code == 0
    assert "cpu" in result.output
    assert "mem" in result.output
    assert "mean" in result.output


def test_summary_json_output():
    runner = CliRunner()
    collector = _make_collector()
    result = runner.invoke(aggregator, ["summary", "--json"], obj={"collector": collector})
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "cpu" in data
    assert data["cpu"]["count"] == 2
    assert data["mem"]["mean"] == 55.0


def test_summary_filter_by_name():
    runner = CliRunner()
    collector = _make_collector()
    result = runner.invoke(aggregator, ["summary", "--name", "cpu", "--json"], obj={"collector": collector})
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "cpu" in data
    assert "mem" not in data
