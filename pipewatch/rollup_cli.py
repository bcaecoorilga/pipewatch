"""CLI commands for metric rollup / time-window aggregation."""
import json
from typing import Optional

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.rollup import rollup, rollup_by_name


@click.group("rollup")
def rollup_cli() -> None:
    """Time-window rollup commands."""


@rollup_cli.command("windows")
@click.option("--window", default=300, show_default=True, help="Window size in seconds.")
@click.option("--name", default=None, help="Filter to a single metric name.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.pass_context
def windows(ctx: click.Context, window: int, name: Optional[str], fmt: str) -> None:
    """Show rolled-up aggregates grouped by time window."""
    history: MetricHistory = ctx.obj.get("history") if ctx.obj else None
    if history is None:
        click.echo("No history store available.")
        return

    all_metrics = history.all()
    if name:
        all_metrics = [m for m in all_metrics if m.name == name]

    if not all_metrics:
        click.echo("No metrics found.")
        return

    rolled = rollup(all_metrics, window_seconds=window)

    if fmt == "json":
        click.echo(json.dumps([w.to_dict() for w in rolled], indent=2))
        return

    for win in rolled:
        click.echo(f"\n[{win.label}]  {win.start.isoformat()} — {win.end.isoformat()}")
        for mname, result in win.results.items():
            click.echo(
                f"  {mname:30s}  count={result.count}  "
                f"mean={result.mean:.4f}  min={result.min:.4f}  max={result.max:.4f}"
            )


@rollup_cli.command("summary")
@click.argument("metric_name")
@click.option("--window", default=300, show_default=True, help="Window size in seconds.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.pass_context
def summary(ctx: click.Context, metric_name: str, window: int, fmt: str) -> None:
    """Show per-window rollup summary for a single metric."""
    history: MetricHistory = ctx.obj.get("history") if ctx.obj else None
    if history is None:
        click.echo("No history store available.")
        return

    metrics = [m for m in history.all() if m.name == metric_name]
    if not metrics:
        click.echo(f"No data for metric '{metric_name}'.")
        return

    by_name = rollup_by_name(metrics, window_seconds=window)
    wins = by_name.get(metric_name, [])

    if fmt == "json":
        click.echo(json.dumps([w.to_dict() for w in wins], indent=2))
        return

    click.echo(f"Rollup for '{metric_name}' (window={window}s):")
    for win in wins:
        r = win.results[metric_name]
        click.echo(
            f"  {win.label}  count={r.count}  mean={r.mean:.4f}  "
            f"min={r.min:.4f}  max={r.max:.4f}  status={r.status_counts}"
        )
