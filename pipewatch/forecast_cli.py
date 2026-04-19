"""CLI commands for metric forecasting."""
import click
import json
from pipewatch.history import MetricHistory
from pipewatch.forecast import forecast


@click.group()
def forecast_cli():
    """Forecast future metric values."""


@forecast_cli.command("predict")
@click.argument("name")
@click.option("--steps", default=3, show_default=True, help="Number of future steps to predict.")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def predict(name: str, steps: int, history_file: str, fmt: str):
    """Predict future values for a metric."""
    history = MetricHistory(path=history_file)
    result = forecast(history, name, steps=steps)
    if result is None:
        click.echo(f"Not enough history to forecast '{name}' (need at least 2 records).")
        return
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(f"Forecast for '{name}' ({result.confidence} confidence):")
        click.echo(f"  Slope    : {result.slope}")
        click.echo(f"  Intercept: {result.intercept}")
        for i, val in enumerate(result.predicted_values, 1):
            click.echo(f"  Step +{i}  : {val}")
