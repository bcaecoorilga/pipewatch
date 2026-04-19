"""CLI entry point for pipewatch."""
import json
import click

from pipewatch.collector import MetricCollector
from pipewatch.alerts import AlertManager
from pipewatch.reporter import Reporter
from pipewatch.metrics import MetricThreshold, MetricStatus

collector = MetricCollector()
alert_manager = AlertManager()


@click.group()
def cli():
    """pipewatch — monitor and alert on data pipeline health metrics."""
    pass


@cli.command()
@click.argument("name")
@click.argument("value", type=float)
@click.option("--warning", type=float, default=None)
@click.option("--critical", type=float, default=None)
def record(name, value, warning, critical):
    """Record a metric value."""
    if warning is not None or critical is not None:
        threshold = MetricThreshold(
            warning_above=warning,
            critical_above=critical,
        )
        collector.register_threshold(name, threshold)

    metric = collector.record(name, value)
    click.echo(f"Recorded {name}={value} [{metric.status.value}]")

    if metric.status in (MetricStatus.WARNING, MetricStatus.CRITICAL):
        alert_manager.trigger(metric)
        click.echo(f"Alert triggered: {metric.status.value.upper()} for '{name}'")


@cli.command(name="list")
def list_metrics():
    """List latest recorded metrics."""
    metrics = collector.all_latest()
    if not metrics:
        click.echo("No metrics recorded.")
        return
    for m in metrics:
        click.echo(f"{m.name}: {m.value} [{m.status.value}] at {m.timestamp}")


@cli.command()
@click.option("--json", "as_json", is_flag=True, default=False)
def report(as_json):
    """Generate a pipeline health report."""
    reporter = Reporter(collector, alert_manager)
    r = reporter.generate()
    if as_json:
        click.echo(json.dumps(r.to_dict(), indent=2))
    else:
        d = r.to_dict()
        s = d["summary"]
        click.echo(f"Report generated at {d['generated_at']}")
        click.echo(f"  Total: {s['total']}  OK: {s['ok']}  Warning: {s['warning']}  Critical: {s['critical']}")
        if d["alerts"]:
            click.echo(f"  Active alerts: {len(d['alerts'])}")


if __name__ == "__main__":
    cli()
