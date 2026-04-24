"""CLI commands for drift detection."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.drift import detect_drift, scan_drifts
from pipewatch.history import MetricHistory


@click.group(name="drift")
def drift_cli() -> None:
    """Detect value drift in pipeline metrics."""


@drift_cli.command(name="check")
@click.argument("name")
@click.option("--ref-window", default=10, show_default=True, help="Reference window size.")
@click.option("--cur-window", default=5, show_default=True, help="Current window size.")
@click.option("--threshold", default=20.0, show_default=True, help="Drift % threshold.")
@click.option("--json", "as_json", is_flag=True, default=False)
@click.pass_context
def check(ctx: click.Context, name: str, ref_window: int, cur_window: int, threshold: float, as_json: bool) -> None:
    """Check drift for a single metric NAME."""
    history: MetricHistory = ctx.obj["history"]
    result = detect_drift(history, name, ref_window, cur_window, threshold)
    if result is None:
        click.echo(f"Not enough history for '{name}' (need {ref_window + cur_window} records).")
        return
    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        status = "DRIFTED" if result.drifted else "stable"
        click.echo(
            f"{name}: ref_mean={result.reference_mean:.4f}  cur_mean={result.current_mean:.4f}  "
            f"drift={result.drift_pct:.2f}%  [{status}]"
        )


@drift_cli.command(name="scan")
@click.option("--ref-window", default=10, show_default=True)
@click.option("--cur-window", default=5, show_default=True)
@click.option("--threshold", default=20.0, show_default=True)
@click.option("--only-drifted", is_flag=True, default=False, help="Show only drifted metrics.")
@click.option("--json", "as_json", is_flag=True, default=False)
@click.pass_context
def scan(ctx: click.Context, ref_window: int, cur_window: int, threshold: float, only_drifted: bool, as_json: bool) -> None:
    """Scan all metrics for drift."""
    collector: MetricCollector = ctx.obj["collector"]
    history: MetricHistory = ctx.obj["history"]
    metrics = collector.all()
    results = scan_drifts(history, metrics, ref_window, cur_window, threshold)
    if only_drifted:
        results = [r for r in results if r.drifted]
    if not results:
        click.echo("No drift results available.")
        return
    if as_json:
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "DRIFTED" if r.drifted else "stable"
            click.echo(f"{r.name}: drift={r.drift_pct:.2f}%  [{status}]")
