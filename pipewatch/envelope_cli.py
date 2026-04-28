"""CLI commands for envelope detection."""

from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.envelope import detect_envelope, scan_envelopes


@click.group("envelope")
def envelope_cli() -> None:
    """Envelope (dynamic band) detection commands."""


@envelope_cli.command("check")
@click.argument("name")
@click.option("--tolerance", default=0.2, show_default=True, help="Fractional band width (e.g. 0.2 = ±20%).")
@click.option("--min-history", default=5, show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def check(name: str, tolerance: float, min_history: int, fmt: str) -> None:
    """Check whether a single metric is inside its historical envelope."""
    collector = MetricCollector()
    history = MetricHistory()
    metric = collector.latest(name)
    if metric is None:
        click.echo(f"No metric found: {name}")
        return
    result = detect_envelope(metric, history, tolerance=tolerance, min_history=min_history)
    if result is None:
        click.echo(f"Insufficient history for '{name}' (need {min_history} records).")
        return
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        status = "INSIDE" if result.inside else "OUTSIDE"
        click.echo(
            f"{name}: {status}  value={result.current_value}  "
            f"band=[{result.lower_bound}, {result.upper_bound}]  "
            f"deviation={result.deviation:.4f}"
        )


@envelope_cli.command("scan")
@click.option("--tolerance", default=0.2, show_default=True)
@click.option("--min-history", default=5, show_default=True)
@click.option("--outside-only", is_flag=True, default=False, help="Only show metrics outside the envelope.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def scan(tolerance: float, min_history: int, outside_only: bool, fmt: str) -> None:
    """Scan all metrics for envelope violations."""
    collector = MetricCollector()
    history = MetricHistory()
    metrics = list(collector.all())
    results = scan_envelopes(metrics, history, tolerance=tolerance, min_history=min_history)
    if outside_only:
        results = [r for r in results if not r.inside]
    if not results:
        click.echo("No envelope results.")
        return
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "INSIDE" if r.inside else "OUTSIDE"
            click.echo(
                f"{r.name}: {status}  value={r.current_value}  "
                f"band=[{r.lower_bound}, {r.upper_bound}]  dev={r.deviation:.4f}"
            )
