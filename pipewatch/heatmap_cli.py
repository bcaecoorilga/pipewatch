"""CLI commands for the heatmap feature."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.heatmap import build_heatmap


@click.group()
def heatmap_cli() -> None:
    """Heatmap commands for visualising metric status over time."""


@heatmap_cli.command("show")
@click.option("--name", multiple=True, help="Filter by metric name (repeatable).")
@click.option("--bucket-hours", default=1, show_default=True, help="Bucket width in hours.")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def show(
    name: tuple,
    bucket_hours: int,
    history_file: str,
    fmt: str,
) -> None:
    """Display a time-bucketed status heatmap."""
    history = MetricHistory(path=history_file)
    names = list(name) if name else None
    hm = build_heatmap(history, names=names, bucket_hours=bucket_hours)

    if fmt == "json":
        click.echo(json.dumps(hm.to_dict(), indent=2))
        return

    if not hm.rows:
        click.echo("No data available for heatmap.")
        return

    click.echo(f"Heatmap (bucket={bucket_hours}h)\n")
    for row in hm.rows:
        click.echo(f"  {row.name}")
        for cell in row.cells:
            symbol = {"ok": ".", "warning": "!", "critical": "X"}.get(cell.status.value, "?")
            click.echo(f"    [{cell.bucket}] {symbol}  ({cell.count} records)")
