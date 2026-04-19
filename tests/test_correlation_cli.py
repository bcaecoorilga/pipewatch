"""Tests for pipewatch.correlation_cli."""
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pipewatch.correlation_cli import correlation
from pipewatch.correlation import CorrelationResult


def _result(coeff, n, interp):
    return CorrelationResult(
        metric_a="cpu", metric_b="mem",
        coefficient=coeff, n=n, interpretation=interp
    )


def test_compare_text_output():
    runner = CliRunner()
    with patch("pipewatch.correlation_cli.MetricHistory"), \
         patch("pipewatch.correlation_cli.correlate", return_value=_result(0.92, 10, "strong")):
        result = runner.invoke(correlation, ["compare", "cpu", "mem"])
    assert result.exit_code == 0
    assert "r=0.92" in result.output
    assert "strong" in result.output


def test_compare_json_output():
    runner = CliRunner()
    with patch("pipewatch.correlation_cli.MetricHistory"), \
         patch("pipewatch.correlation_cli.correlate", return_value=_result(0.5, 5, "moderate")):
        result = runner.invoke(correlation, ["compare", "cpu", "mem", "--json"])
    assert result.exit_code == 0
    assert "coefficient" in result.output
    assert "0.5" in result.output


def test_compare_no_data():
    runner = CliRunner()
    with patch("pipewatch.correlation_cli.MetricHistory"), \
         patch("pipewatch.correlation_cli.correlate", return_value=_result(None, 0, "insufficient data")):
        result = runner.invoke(correlation, ["compare", "a", "b"])
    assert result.exit_code == 0
    assert "N/A" in result.output
