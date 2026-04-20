"""CLI commands for outlier detection."""
import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.outlier import scan_outliers


@click.group()
def outlier_cli():
    """Outlier detection commands."""


@outlier_cli.command("scan")
@click.option("--history-file", default=".pipewatch_history.json", show_default=True)
@click.option("--multiplier", default=1.5, show_default=True, type=float,
              help="IQR multiplier for fence calculation.")
@click.option("--only-outliers", is_flag=True, default=False,
              help="Only show metrics flagged as outliers.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]),
              show_default=True)
@click.pass_context
def scan(ctx, history_file: str, multiplier: float, only_outliers: bool, fmt: str):
    """Scan current metrics for outliers using IQR method."""
    collector: MetricCollector = ctx.obj.get("collector") if ctx.obj else None
    if collector is None:
        collector = MetricCollector()

    metrics = list(collector.all())
    if not metrics:
        click.echo("No metrics recorded.")
        return

    history = MetricHistory(path=history_file)
    results = scan_outliers(metrics, history, multiplier=multiplier)

    if only_outliers:
        results = [r for r in results if r.is_outlier]

    if not results:
        click.echo("No outlier data available (insufficient history).")
        return

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    for r in results:
        flag = " [OUTLIER {}]".format(r.direction.upper()) if r.is_outlier else ""
        click.echo(
            f"{r.name}: value={r.value:.4f}  "
            f"fence=[{r.lower_fence:.4f}, {r.upper_fence:.4f}]  "
            f"IQR={r.iqr:.4f}{flag}"
        )
