"""Tests for pipewatch.forecast_cli."""
import json
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pipewatch.forecast_cli import forecast_cli
from pipewatch.forecast import ForecastResult


def _result():
    return ForecastResult(
        name="cpu",
        steps=3,
        predicted_values=[10.0, 11.0, 12.0],
        slope=1.0,
        intercept=7.0,
        confidence="medium",
    )


@patch("pipewatch.forecast_cli.forecast")
@patch("pipewatch.forecast_cli.MetricHistory")
def test_predict_text_output(mock_history_cls, mock_forecast):
    mock_forecast.return_value = _result()
    runner = CliRunner()
    result = runner.invoke(forecast_cli, ["predict", "cpu"])
    assert result.exit_code == 0
    assert "cpu" in result.output
    assert "Step +1" in result.output
    assert "medium" in result.output


@patch("pipewatch.forecast_cli.forecast")
@patch("pipewatch.forecast_cli.MetricHistory")
def test_predict_json_output(mock_history_cls, mock_forecast):
    mock_forecast.return_value = _result()
    runner = CliRunner()
    result = runner.invoke(forecast_cli, ["predict", "cpu", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "cpu"
    assert len(data["predicted_values"]) == 3


@patch("pipewatch.forecast_cli.forecast")
@patch("pipewatch.forecast_cli.MetricHistory")
def test_predict_no_data(mock_history_cls, mock_forecast):
    mock_forecast.return_value = None
    runner = CliRunner()
    result = runner.invoke(forecast_cli, ["predict", "missing_metric"])
    assert result.exit_code == 0
    assert "Not enough history" in result.output


@patch("pipewatch.forecast_cli.forecast")
@patch("pipewatch.forecast_cli.MetricHistory")
def test_predict_custom_steps(mock_history_cls, mock_forecast):
    r = _result()
    mock_forecast.return_value = r
    runner = CliRunner()
    runner.invoke(forecast_cli, ["predict", "cpu", "--steps", "5"])
    call_kwargs = mock_forecast.call_args
    assert call_kwargs[1]["steps"] == 5 or call_kwargs[0][2] == 5
