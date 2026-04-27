"""CLI commands for step-change detection."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.stepchange import detect_step_change, scan_step_changes


@click.group("stepchange")
def stepchange_cli() -> None:
    """Detect sudden sustained shifts in metric values."""


def _format_result(r, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(r.to_dict(), indent=2)
    sign = "+" if r.shift_magnitude >= 0 else ""
    status = "DETECTED" if r.detected else "none"
    return (
        f"{r.metric_name}: step={status}  "
        f"pre={r.pre_mean:.4f}  post={r.post_mean:.4f}  "
        f"shift={sign}{r.shift_magnitude:.4f} ({r.shift_pct*100:.1f}%)  "
        f"n={r.record_count}"
    )


@stepchange_cli.command("check")
@click.argument("metric_name")
@click.option("--min-records", default=6, show_default=True, help="Minimum history records required.")
@click.option("--threshold", default=0.20, show_default=True, help="Relative shift threshold (0–1).")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def check(metric_name: str, min_records: int, threshold: float, fmt: str) -> None:
    """Check a single metric for a step change."""
    collector = MetricCollector()
    history = MetricHistory()
    metric = collector.latest(metric_name)
    if metric is None:
        click.echo(f"No metric found: {metric_name}")
        raise SystemExit(1)
    result = detect_step_change(metric, history, min_records=min_records, threshold_pct=threshold)
    if result is None:
        click.echo(f"{metric_name}: insufficient history (need {min_records} records)")
    else:
        click.echo(_format_result(result, fmt))


@stepchange_cli.command("scan")
@click.option("--min-records", default=6, show_default=True)
@click.option("--threshold", default=0.20, show_default=True)
@click.option("--only-detected", is_flag=True, default=False, help="Show only detected step changes.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def scan(min_records: int, threshold: float, only_detected: bool, fmt: str) -> None:
    """Scan all metrics for step changes."""
    collector = MetricCollector()
    history = MetricHistory()
    metrics = list(collector.all())
    if not metrics:
        click.echo("No metrics recorded.")
        return
    results = scan_step_changes(metrics, history, min_records=min_records, threshold_pct=threshold)
    if only_detected:
        results = [r for r in results if r.detected]
    if not results:
        click.echo("No step changes detected.")
        return
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            click.echo(_format_result(r, fmt))
