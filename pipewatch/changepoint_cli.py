"""CLI commands for change-point detection."""
from __future__ import annotations

import json

import click

from pipewatch.changepoint import detect_changepoint, scan_changepoints
from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory


@click.group(name="changepoint")
def changepoint_cli() -> None:
    """Detect mean-shift change-points in metric history."""


def _format_result(result, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(result.to_dict(), indent=2)
    sign = "+" if result.delta >= 0 else ""
    status = "DETECTED" if result.detected else "none"
    return (
        f"[{status}] {result.metric_name}: "
        f"before={result.before_mean:.4f}  after={result.after_mean:.4f}  "
        f"delta={sign}{result.delta:.4f}  "
        f"rel={sign}{result.relative_change * 100:.1f}%  "
        f"split@{result.changepoint_index}"
    )


@changepoint_cli.command(name="check")
@click.argument("metric_name")
@click.option("--min-records", default=6, show_default=True, help="Minimum history records required.")
@click.option("--threshold", default=0.15, show_default=True, help="Relative change threshold (0–1).")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def check(metric_name: str, min_records: int, threshold: float, fmt: str) -> None:
    """Check a single metric for a change-point."""
    collector = MetricCollector()
    history = MetricHistory()
    result = detect_changepoint(metric_name, history, min_records, threshold)
    if result is None:
        click.echo(f"Insufficient history for '{metric_name}'.")
        return
    click.echo(_format_result(result, fmt))


@changepoint_cli.command(name="scan")
@click.option("--min-records", default=6, show_default=True, help="Minimum history records required.")
@click.option("--threshold", default=0.15, show_default=True, help="Relative change threshold (0–1).")
@click.option("--only-detected", is_flag=True, default=False, help="Show only detected change-points.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def scan(min_records: int, threshold: float, only_detected: bool, fmt: str) -> None:
    """Scan all known metrics for change-points."""
    collector = MetricCollector()
    history = MetricHistory()
    metrics = collector.all()
    if not metrics:
        click.echo("No metrics recorded.")
        return
    results = scan_changepoints(metrics, history, min_records, threshold)
    if only_detected:
        results = [r for r in results if r.detected]
    if not results:
        click.echo("No change-points found.")
        return
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            click.echo(_format_result(r, fmt))
