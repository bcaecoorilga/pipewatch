"""CLI entry point for pipewatch metric reporting."""

import json
import sys
from datetime import datetime

import click

from pipewatch.collector import MetricCollector
from pipewatch.metrics import Metric, MetricThreshold


collector = MetricCollector()


@click.group()
def cli():
    """pipewatch — monitor and alert on data pipeline health metrics."""


@cli.command()
@click.argument("name")
@click.argument("value", type=float)
@click.option("--unit", default="", help="Unit of the metric (e.g. ms, rows, %)")
@click.option("--warning", type=float, default=None, help="Warning threshold")
@click.option("--critical", type=float, default=None, help="Critical threshold")
@click.option("--tag", multiple=True, help="Tags in key=value format")
def record(name, value, unit, warning, critical, tag):
    """Record a metric value and evaluate its health status."""
    tags = {}
    for t in tag:
        if "=" in t:
            k, v = t.split("=", 1)
            tags[k] = v

    if warning is not None or critical is not None:
        collector.register_threshold(name, MetricThreshold(warning=warning, critical=critical))

    metric = Metric(name=name, value=value, unit=unit, tags=tags)
    result = collector.record(metric)

    click.echo(json.dumps(result.to_dict(), indent=2))
    if result.status.value == "critical":
        sys.exit(2)
    elif result.status.value == "warning":
        sys.exit(1)


@cli.command(name="list")
def list_metrics():
    """List the latest recorded value for all metrics."""
    metrics = collector.all_latest()
    if not metrics:
        click.echo("No metrics recorded.")
        return
    for m in metrics:
        click.echo(json.dumps(m.to_dict(), indent=2))


if __name__ == "__main__":
    cli()
