"""CLI commands for metric rate-of-change analysis."""
import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.rate import compute_rate, scan_rates


@click.group()
def rate_cli():
    """Rate-of-change analysis for pipeline metrics."""


@rate_cli.command("show")
@click.argument("metric_name")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def show_rate(metric_name: str, history_file: str, fmt: str):
    """Show rate of change for a specific metric."""
    history = MetricHistory(path=history_file)
    records = history.for_name(metric_name)

    result = compute_rate(records)
    if result is None:
        click.echo(f"Not enough data to compute rate for '{metric_name}'.")
        return

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(f"Metric       : {result.name}")
        click.echo(f"Period       : {result.period_seconds:.1f}s")
        click.echo(f"Start value  : {result.start_value}")
        click.echo(f"End value    : {result.end_value}")
        click.echo(f"Abs change   : {result.absolute_change:+.4f}")
        click.echo(f"Rate/sec     : {result.rate_per_second:+.6f}")
        click.echo(f"Rate/min     : {result.rate_per_minute:+.6f}")
        pct = f"{result.pct_change:+.2f}%" if result.pct_change is not None else "N/A"
        click.echo(f"% change     : {pct}")


@rate_cli.command("scan")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def scan(history_file: str, fmt: str):
    """Scan all metrics and display their rates of change."""
    history = MetricHistory(path=history_file)
    all_records = history.all()

    grouped: dict = {}
    for m in all_records:
        grouped.setdefault(m.name, []).append(m)

    results = scan_rates(grouped)
    if not results:
        click.echo("No rate data available.")
        return

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            pct = f"{r.pct_change:+.2f}%" if r.pct_change is not None else "N/A"
            click.echo(
                f"{r.name:<30} change={r.absolute_change:+.4f}  "
                f"rate/min={r.rate_per_minute:+.6f}  pct={pct}"
            )
