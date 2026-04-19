"""CLI commands for metric aggregation."""

import click
import json
from pipewatch.collector import MetricCollector
from pipewatch.aggregator import aggregate_by_name


@click.group()
def aggregator():
    """Aggregation commands for pipeline metrics."""
    pass


@aggregator.command("summary")
@click.option("--name", default=None, help="Filter by metric name.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def summary(ctx, name, as_json):
    """Show aggregated summary of recorded metrics."""
    collector: MetricCollector = ctx.obj.get("collector") if ctx.obj else None
    if collector is None:
        collector = MetricCollector()

    all_metrics = collector.all()
    if name:
        all_metrics = [m for m in all_metrics if m.name == name]

    results = aggregate_by_name(all_metrics)

    if not results:
        click.echo("No metrics found.")
        return

    if as_json:
        click.echo(json.dumps({k: v.to_dict() for k, v in results.items()}, indent=2))
    else:
        for metric_name, result in results.items():
            click.echo(f"[{metric_name}]")
            click.echo(f"  count : {result.count}")
            click.echo(f"  mean  : {result.mean}")
            click.echo(f"  min   : {result.min}")
            click.echo(f"  max   : {result.max}")
            click.echo(f"  latest: {result.latest}")
            for status, count in result.status_counts.items():
                click.echo(f"  {status}: {count}")
