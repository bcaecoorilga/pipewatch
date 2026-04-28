"""CLI commands for EWMA-based smoothing and anomaly detection."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.ewma import detect_ewma, scan_ewma


@click.group("ewma")
def ewma_cli() -> None:
    """Exponentially Weighted Moving Average (EWMA) commands."""


@ewma_cli.command("check")
@click.argument("metric_name")
@click.option("--alpha", default=0.3, show_default=True, help="Smoothing factor (0, 1].")
@click.option("--threshold", default=0.2, show_default=True, help="Relative deviation threshold.")
@click.option("--min-records", default=5, show_default=True, help="Minimum history records needed.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.pass_context
def check(ctx: click.Context, metric_name: str, alpha: float, threshold: float, min_records: int, fmt: str) -> None:
    """Check EWMA deviation for a single metric."""
    collector: MetricCollector = ctx.obj["collector"]
    history: MetricHistory = ctx.obj["history"]

    metric = collector.latest(metric_name)
    if metric is None:
        click.echo(f"No metric found: {metric_name}")
        return

    result = detect_ewma(metric, history, alpha=alpha, threshold=threshold, min_records=min_records)
    if result is None:
        click.echo(f"Insufficient history for '{metric_name}' (need {min_records} records).")
        return

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        status = "ANOMALOUS" if result.is_anomalous else "OK"
        click.echo(
            f"{result.name}: value={result.current_value:.4f}  "
            f"ewma={result.ewma:.4f}  "
            f"rel_dev={result.relative_deviation:.2%}  "
            f"[{status}]"
        )


@ewma_cli.command("scan")
@click.option("--alpha", default=0.3, show_default=True, help="Smoothing factor (0, 1].")
@click.option("--threshold", default=0.2, show_default=True, help="Relative deviation threshold.")
@click.option("--min-records", default=5, show_default=True, help="Minimum history records needed.")
@click.option("--anomalous-only", is_flag=True, default=False, help="Only show anomalous metrics.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.pass_context
def scan(ctx: click.Context, alpha: float, threshold: float, min_records: int, anomalous_only: bool, fmt: str) -> None:
    """Scan all metrics for EWMA deviations."""
    collector: MetricCollector = ctx.obj["collector"]
    history: MetricHistory = ctx.obj["history"]

    metrics = list(collector.all())
    results = scan_ewma(metrics, history, alpha=alpha, threshold=threshold, min_records=min_records)

    if anomalous_only:
        results = [r for r in results if r.is_anomalous]

    if not results:
        click.echo("No EWMA results to display.")
        return

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "ANOMALOUS" if r.is_anomalous else "OK"
            click.echo(
                f"{r.name}: value={r.current_value:.4f}  "
                f"ewma={r.ewma:.4f}  "
                f"rel_dev={r.relative_deviation:.2%}  "
                f"[{status}]"
            )
