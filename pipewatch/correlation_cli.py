"""CLI commands for metric correlation analysis."""
import json
import click
from pipewatch.history import MetricHistory
from pipewatch.correlation import correlate


@click.group()
def correlation():
    """Correlation analysis between metrics."""


@correlation.command("compare")
@click.argument("metric_a")
@click.argument("metric_b")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def compare(metric_a, metric_b, history_file, as_json):
    """Compute Pearson correlation between METRIC_A and METRIC_B."""
    history = MetricHistory(path=history_file)
    result = correlate(history, metric_a, metric_b)
    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        coeff = result.coefficient if result.coefficient is not None else "N/A"
        click.echo(f"Correlation: {metric_a} vs {metric_b}")
        click.echo(f"  n={result.n}  r={coeff}  ({result.interpretation})")
