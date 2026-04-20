"""CLI commands for pipeline health scoring."""

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.pipeline_health import compute_health


@click.group("health")
def health() -> None:
    """Pipeline health scoring commands."""


@health.command("score")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.pass_context
def score(ctx: click.Context, fmt: str) -> None:
    """Display an overall health score for all tracked metrics."""
    collector: MetricCollector = ctx.obj.get("collector") if ctx.obj else None
    if collector is None:
        collector = MetricCollector()

    metrics = collector.all()
    result = compute_health(metrics)

    if result is None:
        click.echo("No metrics recorded yet.")
        return

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(f"Health Score : {result.score:.2%}  [{result.grade}]")
        click.echo(f"Total        : {result.total}")
        click.echo(f"  OK         : {result.ok_count}")
        click.echo(f"  Warning    : {result.warning_count}")
        click.echo(f"  Critical   : {result.critical_count}")
