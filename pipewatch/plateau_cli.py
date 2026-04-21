"""CLI commands for plateau detection."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.plateau import detect_plateau, scan_plateaus


@click.group(name="plateau")
def plateau_cli() -> None:
    """Detect metrics that have flatlined (plateau detection)."""


@plateau_cli.command(name="check")
@click.argument("name")
@click.option("--window", default=10, show_default=True, help="History window size.")
@click.option("--tolerance", default=0.01, show_default=True, help="Max allowed range.")
@click.option("--history-file", default=".pipewatch_history.json", show_default=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def check(name: str, window: int, tolerance: float, history_file: str, as_json: bool) -> None:
    """Check a single metric for plateau behaviour."""
    history = MetricHistory(path=history_file)
    result = detect_plateau(name, history, window=window, tolerance=tolerance)
    if result is None:
        click.echo(f"Not enough history for '{name}' (need {window} records).")
        return
    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        status = "PLATEAU" if result.is_plateau else "OK"
        click.echo(
            f"{result.name}: {status}  range={result.range_value:.4f}  "
            f"tolerance={result.threshold}  window={result.window}  "
            f"duration={result.duration_seconds:.1f}s"
        )


@plateau_cli.command(name="scan")
@click.option("--window", default=10, show_default=True)
@click.option("--tolerance", default=0.01, show_default=True)
@click.option("--only-plateaus", is_flag=True, default=False, help="Show only flatlined metrics.")
@click.option("--history-file", default=".pipewatch_history.json", show_default=True)
@click.option("--json", "as_json", is_flag=True, default=False)
@click.pass_context
def scan(ctx: click.Context, window: int, tolerance: float, only_plateaus: bool, history_file: str, as_json: bool) -> None:
    """Scan all recorded metrics for plateau behaviour."""
    collector: MetricCollector = ctx.obj.get("collector") if ctx.obj else None
    if collector is None:
        collector = MetricCollector()
    history = MetricHistory(path=history_file)
    results = scan_plateaus(list(collector.all()), history, window=window, tolerance=tolerance)
    if only_plateaus:
        results = [r for r in results if r.is_plateau]
    if not results:
        click.echo("No plateau data available.")
        return
    if as_json:
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "PLATEAU" if r.is_plateau else "OK"
            click.echo(f"{r.name}: {status}  range={r.range_value:.4f}  window={r.window}")
