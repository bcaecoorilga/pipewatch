"""CLI commands for noise detection."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.noise import detect_noise, scan_noise


@click.group(name="noise")
def noise_cli() -> None:
    """Detect noisy metrics with high coefficient of variation."""


@noise_cli.command(name="check")
@click.argument("metric_name")
@click.option("--cv-threshold", default=0.1, show_default=True, help="CV threshold for noise.")
@click.option("--min-records", default=5, show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def check(metric_name: str, cv_threshold: float, min_records: int, fmt: str) -> None:
    """Check a single metric for noise."""
    collector = MetricCollector()
    history = MetricHistory()
    metric = collector.latest(metric_name)
    if metric is None:
        click.echo(f"No metric found: {metric_name}")
        return

    result = detect_noise(metric, history, min_records=min_records, cv_threshold=cv_threshold)
    if result is None:
        click.echo(f"Insufficient history for '{metric_name}'.")
        return

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        status = "NOISY" if result.noisy else "CLEAN"
        click.echo(
            f"{result.name}: {status} | cv={result.cv:.4f} "
            f"mean={result.mean:.4f} std={result.std_dev:.4f} [{result.label}]"
        )


@noise_cli.command(name="scan")
@click.option("--cv-threshold", default=0.1, show_default=True)
@click.option("--min-records", default=5, show_default=True)
@click.option("--noisy-only", is_flag=True, default=False, help="Show only noisy metrics.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def scan(cv_threshold: float, min_records: int, noisy_only: bool, fmt: str) -> None:
    """Scan all metrics for noise."""
    collector = MetricCollector()
    history = MetricHistory()
    metrics = list(collector.all())

    if not metrics:
        click.echo("No metrics recorded.")
        return

    results = scan_noise(metrics, history, min_records=min_records, cv_threshold=cv_threshold)
    if noisy_only:
        results = [r for r in results if r.noisy]

    if not results:
        click.echo("No results to display.")
        return

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "NOISY" if r.noisy else "CLEAN"
            click.echo(
                f"{r.name}: {status} cv={r.cv:.4f} [{r.label}]"
            )
