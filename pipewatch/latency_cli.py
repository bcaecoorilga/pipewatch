"""CLI commands for latency analysis."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.latency import detect_latency, scan_latencies


@click.group(name="latency")
def latency_cli() -> None:
    """Latency analysis commands."""


@latency_cli.command(name="check")
@click.argument("metric_name")
@click.option("--warn", default=1.0, show_default=True, help="Warning threshold (seconds).")
@click.option("--crit", default=5.0, show_default=True, help="Critical threshold (seconds).")
@click.option("--history-file", default=".pipewatch_history.json", show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def check(metric_name: str, warn: float, crit: float, history_file: str, fmt: str) -> None:
    """Check latency for a single metric."""
    collector = MetricCollector()
    history = MetricHistory(history_file)
    metric = collector.latest(metric_name)
    if metric is None:
        click.echo(f"No metric found: {metric_name}")
        return
    result = detect_latency(metric, history, warn_threshold=warn, crit_threshold=crit)
    if result is None:
        click.echo(f"Insufficient history for '{metric_name}'.")
        return
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(f"Metric : {result.metric_name}")
        click.echo(f"Mean   : {result.mean_latency:.4f}s")
        click.echo(f"P95    : {result.p95_latency:.4f}s")
        click.echo(f"Max    : {result.max_latency:.4f}s")
        click.echo(f"Class  : {result.classification}")
        click.echo(f"Samples: {result.sample_count}")


@latency_cli.command(name="scan")
@click.option("--warn", default=1.0, show_default=True)
@click.option("--crit", default=5.0, show_default=True)
@click.option("--history-file", default=".pipewatch_history.json", show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def scan(warn: float, crit: float, history_file: str, fmt: str) -> None:
    """Scan all metrics for latency issues."""
    collector = MetricCollector()
    history = MetricHistory(history_file)
    metrics = list(collector.all())
    results = scan_latencies(metrics, history, warn_threshold=warn, crit_threshold=crit)
    if not results:
        click.echo("No latency data available.")
        return
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            click.echo(f"{r.metric_name:<30} {r.classification:<10} mean={r.mean_latency:.4f}s p95={r.p95_latency:.4f}s")
