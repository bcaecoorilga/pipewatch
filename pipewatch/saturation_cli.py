"""CLI commands for saturation detection."""
from __future__ import annotations

import json
import click

from pipewatch.collector import MetricCollector
from pipewatch.saturation import detect_saturation, scan_saturations


@click.group(name="saturation")
def saturation_cli() -> None:
    """Check how close metrics are to their ceilings."""


@saturation_cli.command(name="check")
@click.argument("metric_name")
@click.argument("ceiling", type=float)
@click.option("--warn", default=75.0, show_default=True, help="Warning threshold %")
@click.option("--crit", default=90.0, show_default=True, help="Critical threshold %")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
@click.pass_context
def check(ctx: click.Context, metric_name: str, ceiling: float, warn: float, crit: float, fmt: str) -> None:
    """Check saturation for a single metric."""
    collector: MetricCollector = ctx.obj["collector"]
    metric = collector.latest(metric_name)
    if metric is None:
        click.echo(f"No data for metric '{metric_name}'.")
        return
    result = detect_saturation(metric, ceiling, warn, crit)
    if result is None:
        click.echo("Invalid ceiling (must be > 0).")
        return
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(
            f"{result.metric_name}: {result.current_value:.2f} / {result.ceiling:.2f} "
            f"({result.saturation_pct:.1f}%) [{result.label.upper()}]"
        )


@saturation_cli.command(name="scan")
@click.argument("ceilings_json")
@click.option("--warn", default=75.0, show_default=True)
@click.option("--crit", default=90.0, show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
@click.pass_context
def scan(ctx: click.Context, ceilings_json: str, warn: float, crit: float, fmt: str) -> None:
    """Scan all metrics. CEILINGS_JSON is a JSON object mapping metric names to ceiling values."""
    collector: MetricCollector = ctx.obj["collector"]
    try:
        ceilings = json.loads(ceilings_json)
    except json.JSONDecodeError as exc:
        click.echo(f"Invalid JSON: {exc}")
        return
    metrics = [collector.latest(n) for n in collector.names() if collector.latest(n) is not None]
    results = scan_saturations(metrics, ceilings, warn, crit)
    if not results:
        click.echo("No saturation data available.")
        return
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            click.echo(
                f"{r.metric_name}: {r.current_value:.2f} / {r.ceiling:.2f} "
                f"({r.saturation_pct:.1f}%) [{r.label.upper()}]"
            )
