"""CLI entry-point for pipewatch."""

import click
from pipewatch.collector import MetricCollector
from pipewatch.reporter import Reporter
from pipewatch.exporter import export_report_json, export_report_text

_collector = MetricCollector()
_reporter = Reporter(_collector)


@click.group()
def cli():
    """pipewatch — monitor and alert on data pipeline health metrics."""


@cli.command()
@click.argument("name")
@click.argument("value", type=float)
@click.option("--unit", default="", help="Unit of the metric value.")
def record(name: str, value: float, unit: str):
    """Record a metric VALUE for NAME."""
    metric = _collector.record(name, value, unit=unit)
    click.echo(f"Recorded {name}={value} [{unit}] status={metric.status.value}")


@cli.command(name="list")
def list_metrics():
    """List all metrics with their latest values."""
    metrics = _collector.all_latest()
    if not metrics:
        click.echo("No metrics recorded yet.")
        return
    for m in metrics:
        d = m.to_dict()
        click.echo(f"  {d['name']:30s} {d['value']:>10} {d.get('unit',''):10s} [{d.get('status','?')}]")


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text",
              help="Output format.")
def report(fmt: str):
    """Generate a health report for all recorded metrics."""
    pipeline_report = _reporter.generate()
    if fmt == "json":
        click.echo(export_report_json(pipeline_report))
    else:
        click.echo(export_report_text(pipeline_report))


@cli.command()
@click.argument("output", type=click.Path())
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="json")
def export(output: str, fmt: str):
    """Export the current report to OUTPUT file."""
    pipeline_report = _reporter.generate()
    content = export_report_json(pipeline_report) if fmt == "json" else export_report_text(pipeline_report)
    with open(output, "w") as fh:
        fh.write(content)
    click.echo(f"Report exported to {output} ({fmt}).")


if __name__ == "__main__":
    cli()
