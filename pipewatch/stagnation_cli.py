"""CLI commands for stagnation detection."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.stagnation import detect_stagnation, scan_stagnations


@click.group(name="stagnation")
def stagnation_cli() -> None:
    """Detect metrics that have stopped changing."""


@stagnation_cli.command(name="check")
@click.argument("name")
@click.option("--window", default=10, show_default=True, help="Number of recent records to examine.")
@click.option("--tolerance", default=0.0, show_default=True, help="Minimum spread to consider non-stagnant.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def check(name: str, window: int, tolerance: float, fmt: str) -> None:
    """Check a single metric for stagnation."""
    history = MetricHistory()
    result = detect_stagnation(name, history, window=window, tolerance=tolerance)
    if result is None:
        click.echo(f"Not enough data for '{name}'.")
        return
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        status = "STAGNANT" if result.is_stagnant else "ok"
        click.echo(
            f"{name}: {status} | window={result.window} spread={result.spread:.4f} "
            f"unique={result.unique_values} tolerance={result.tolerance}"
        )


@stagnation_cli.command(name="scan")
@click.option("--window", default=10, show_default=True)
@click.option("--tolerance", default=0.0, show_default=True)
@click.option("--only-stagnant", is_flag=True, default=False, help="Show only stagnant metrics.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def scan(window: int, tolerance: float, only_stagnant: bool, fmt: str) -> None:
    """Scan all metrics for stagnation."""
    history = MetricHistory()
    results = scan_stagnations(history, window=window, tolerance=tolerance)
    if only_stagnant:
        results = [r for r in results if r.is_stagnant]
    if not results:
        click.echo("No stagnation data available.")
        return
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "STAGNANT" if r.is_stagnant else "ok"
            click.echo(f"{r.metric_name}: {status} | spread={r.spread:.4f} unique={r.unique_values}")
