"""Tests for pipewatch.baseline_cli."""
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pipewatch.baseline_cli import baseline
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.baseline import BaselineDeviation


def _m(name, value):
    return Metric(name=name, value=value, unit="u", status=MetricStatus.OK)


def test_capture_no_metrics():
    runner = CliRunner()
    with patch("pipewatch.baseline_cli.MetricCollector") as MockC:
        MockC.return_value.all.return_value = []
        result = runner.invoke(baseline, ["capture"])
    assert "No metrics" in result.output


def test_capture_saves_metrics(tmp_path):
    runner = CliRunner()
    with patch("pipewatch.baseline_cli.MetricCollector") as MockC, \
         patch("pipewatch.baseline_cli.save_baseline") as mock_save:
        mock_save.return_value = [MagicMock(), MagicMock()]
        MockC.return_value.all.return_value = [_m("rows", 10.0), _m("errors", 1.0)]
        result = runner.invoke(baseline, ["capture", "--label", "v1"])
    assert "2 metric" in result.output


def test_list_empty_label():
    runner = CliRunner()
    with patch("pipewatch.baseline_cli.load_baseline", return_value={}):
        result = runner.invoke(baseline, ["list", "--label", "missing"])
    assert "No baseline" in result.output


def test_compare_text_output():
    runner = CliRunner()
    dev = BaselineDeviation(name="rows", baseline_value=100.0, current_value=120.0, delta=20.0, pct_change=20.0)
    with patch("pipewatch.baseline_cli.MetricCollector") as MockC, \
         patch("pipewatch.baseline_cli.compare_to_baseline", return_value=[dev]):
        MockC.return_value.all.return_value = [_m("rows", 120.0)]
        result = runner.invoke(baseline, ["compare"])
    assert "rows" in result.output
    assert "+20" in result.output


def test_compare_json_output():
    runner = CliRunner()
    dev = BaselineDeviation(name="rows", baseline_value=100.0, current_value=120.0, delta=20.0, pct_change=20.0)
    with patch("pipewatch.baseline_cli.MetricCollector") as MockC, \
         patch("pipewatch.baseline_cli.compare_to_baseline", return_value=[dev]):
        MockC.return_value.all.return_value = [_m("rows", 120.0)]
        result = runner.invoke(baseline, ["compare", "--format", "json"])
    import json
    data = json.loads(result.output)
    assert data[0]["name"] == "rows"
