"""CLI commands for heartbeat monitoring."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.heartbeat import HeartbeatMonitor


@click.group("heartbeat")
def heartbeat_cli() -> None:
    """Heartbeat monitoring commands."""


@heartbeat_cli.command("check")
@click.argument("name")
@click.option("--interval", "-i", type=float, required=True, help="Expected interval in seconds.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def check(ctx: click.Context, name: str, interval: float, fmt: str) -> None:
    """Check heartbeat for a single metric."""
    collector: MetricCollector = ctx.obj["collector"]
    monitor = HeartbeatMonitor()
    monitor.register(name, interval)
    result = monitor.check(name, collector)
    if result is None:
        click.echo(f"No heartbeat rule for {name!r}.")
        return
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        status = "ALIVE" if result.is_alive else "DEAD"
        click.echo(f"[{status}] {result.message}")


@heartbeat_cli.command("scan")
@click.option("--interval", "-i", type=float, required=True, help="Default expected interval in seconds.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def scan(ctx: click.Context, interval: float, fmt: str) -> None:
    """Scan all known metrics for heartbeat status."""
    collector: MetricCollector = ctx.obj["collector"]
    monitor = HeartbeatMonitor()
    for name in collector.all_names():
        monitor.register(name, interval)
    results = monitor.scan(collector)
    if not results:
        click.echo("No metrics registered.")
        return
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "ALIVE" if r.is_alive else "DEAD "
            click.echo(f"[{status}] {r.message}")
