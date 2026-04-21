"""CLI commands for pattern detection."""
from __future__ import annotations

import json

import click

from pipewatch.history import MetricHistory
from pipewatch.pattern import detect_pattern, scan_patterns


@click.group("pattern")
def pattern_cli() -> None:
    """Detect recurring status patterns in metric history."""


@pattern_cli.command("check")
@click.argument("metric_name")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--window", default=20, show_default=True, help="Number of recent records to analyse.")
@click.option("--min-repeats", default=2, show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def check(metric_name: str, history_file: str, window: int, min_repeats: int, fmt: str) -> None:
    """Check for a pattern in a single metric."""
    history = MetricHistory(path=history_file)
    result = detect_pattern(history, metric_name, window=window, min_repeats=min_repeats)
    if result is None:
        click.echo(f"No repeating pattern detected for '{metric_name}'.")
        return
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        osc = "yes" if result.is_oscillating else "no"
        click.echo(f"Metric      : {result.metric_name}")
        click.echo(f"Pattern     : {' -> '.join(result.pattern)}")
        click.echo(f"Repeats     : {result.repeats}")
        click.echo(f"Oscillating : {osc}")
        click.echo(f"Dominant    : {result.dominant_status}")


@pattern_cli.command("scan")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--window", default=20, show_default=True)
@click.option("--min-repeats", default=2, show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def scan(history_file: str, window: int, min_repeats: int, fmt: str) -> None:
    """Scan all metrics for repeating patterns."""
    history = MetricHistory(path=history_file)
    results = scan_patterns(history, window=window, min_repeats=min_repeats)
    if not results:
        click.echo("No patterns detected.")
        return
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            osc = "oscillating" if r.is_oscillating else "repeating"
            click.echo(
                f"{r.metric_name}: {' -> '.join(r.pattern)} "
                f"x{r.repeats} [{osc}] dominant={r.dominant_status}"
            )
