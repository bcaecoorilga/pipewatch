"""CLI commands for capacity planning."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.capacity import estimate_capacity, scan_capacity


@click.group(name="capacity")
def capacity_cli() -> None:
    """Capacity planning: estimate when metrics will hit thresholds."""


@capacity_cli.command(name="check")
@click.argument("metric_name")
@click.argument("threshold", type=float)
@click.option("--horizon", default=20, show_default=True, help="Forecast steps.")
@click.option("--step-seconds", default=60.0, show_default=True)
@click.option("--history-path", default=".pipewatch_history.json", show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def check(
    metric_name: str,
    threshold: float,
    horizon: int,
    step_seconds: float,
    history_path: str,
    fmt: str,
) -> None:
    """Estimate when METRIC_NAME will reach THRESHOLD."""
    history = MetricHistory(path=history_path)
    result = estimate_capacity(history, metric_name, threshold, horizon, step_seconds)
    if result is None:
        click.echo(f"Insufficient history for '{metric_name}'.")
        return
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        eta = f"{result.eta_seconds:.0f}s" if result.eta_seconds is not None else "never within horizon"
        click.echo(f"metric   : {result.metric_name}")
        click.echo(f"current  : {result.current_value:.4f}")
        click.echo(f"threshold: {result.threshold}")
        click.echo(f"slope    : {result.slope:.6f} /s")
        click.echo(f"ETA      : {eta}")


@capacity_cli.command(name="scan")
@click.option("--horizon", default=20, show_default=True)
@click.option("--step-seconds", default=60.0, show_default=True)
@click.option("--history-path", default=".pipewatch_history.json", show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
@click.pass_context
def scan(
    ctx: click.Context,
    horizon: int,
    step_seconds: float,
    history_path: str,
    fmt: str,
) -> None:
    """Scan all registered thresholds for capacity projections."""
    collector: MetricCollector = ctx.obj.get("collector") if ctx.obj else None
    if collector is None:
        click.echo("No collector available.")
        return
    thresholds = {
        name: t.critical
        for name, t in collector.thresholds.items()
        if t.critical is not None
    }
    if not thresholds:
        click.echo("No critical thresholds registered.")
        return
    history = MetricHistory(path=history_path)
    results = scan_capacity(history, thresholds, horizon, step_seconds)
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            eta = f"{r.eta_seconds:.0f}s" if r.eta_seconds is not None else "never"
            click.echo(f"{r.metric_name}: current={r.current_value:.4f} threshold={r.threshold} ETA={eta}")
