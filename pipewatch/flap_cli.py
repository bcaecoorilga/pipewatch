"""CLI commands for flap detection."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.flap import detect_flap, scan_flaps
from pipewatch.history import MetricHistory


@click.group(name="flap")
def flap_cli() -> None:
    """Detect rapidly flapping metrics."""


@flap_cli.command(name="check")
@click.argument("name")
@click.option("--window", default=10, show_default=True, help="Number of recent records to inspect.")
@click.option("--min-transitions", default=4, show_default=True, help="Transitions required to flag as flapping.")
@click.option("--fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def check(name: str, window: int, min_transitions: int, fmt: str) -> None:
    """Check a single metric for flapping."""
    history = MetricHistory()
    result = detect_flap(name, history, window=window, min_transitions=min_transitions)
    if result is None:
        click.echo(f"No data for '{name}'.")
        return
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        flag = "FLAPPING" if result.flapping else "stable"
        click.echo(f"{name}: {flag} ({result.transitions} transitions in last {result.window} records)")


@flap_cli.command(name="scan")
@click.option("--window", default=10, show_default=True)
@click.option("--min-transitions", default=4, show_default=True)
@click.option("--fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def scan(window: int, min_transitions: int, fmt: str) -> None:
    """Scan all known metrics for flapping."""
    collector = MetricCollector()
    history = MetricHistory()
    names = list({m.name for m in collector.all()})
    results = scan_flaps(names, history, window=window, min_transitions=min_transitions)

    if not results:
        click.echo("No flap data available.")
        return

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            flag = "FLAPPING" if r.flapping else "stable"
            click.echo(f"{r.name}: {flag} ({r.transitions} transitions in last {r.window} records)")
