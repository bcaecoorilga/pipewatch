"""CLI commands for throttle detection."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.throttle import detect_throttle, scan_throttles


@click.group(name="throttle")
def throttle_cli() -> None:
    """Throttle detection commands."""


@throttle_cli.command(name="check")
@click.argument("name")
@click.option("--ceiling", required=True, type=float, help="Max allowed rate of change per second.")
@click.option("--window", default=60.0, show_default=True, type=float, help="Look-back window in seconds.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def check(name: str, ceiling: float, window: float, fmt: str) -> None:
    """Check throttle status for a single metric NAME."""
    history = MetricHistory()
    result = detect_throttle(name, history, ceiling, window)
    if result is None:
        click.echo(f"No throttle data available for '{name}'.")
        return
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        status = "THROTTLED" if result.throttled else "OK"
        click.echo(f"[{status}] {result.message}")


@throttle_cli.command(name="scan")
@click.option("--ceiling", required=True, type=float, help="Max allowed rate of change per second.")
@click.option("--window", default=60.0, show_default=True, type=float, help="Look-back window in seconds.")
@click.option("--only-throttled", is_flag=True, default=False, help="Show only throttled metrics.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def scan(ceiling: float, window: float, only_throttled: bool, fmt: str) -> None:
    """Scan all known metrics for throttle violations."""
    collector = MetricCollector()
    history = MetricHistory()
    metrics = collector.all()
    results = scan_throttles(metrics, history, ceiling, window)
    if only_throttled:
        results = [r for r in results if r.throttled]
    if not results:
        click.echo("No throttle results found.")
        return
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "THROTTLED" if r.throttled else "OK"
            click.echo(f"[{status}] {r.message}")
