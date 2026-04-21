"""CLI commands for quota inspection."""
from __future__ import annotations

import json
from typing import Optional

import click

from pipewatch.collector import MetricCollector
from pipewatch.quota import QuotaRule, scan_quotas


@click.group(name="quota")
def quota_cli() -> None:
    """Quota enforcement commands."""


@quota_cli.command(name="check")
@click.argument("metric_name")
@click.option("--max-records", default=100, show_default=True, help="Max records allowed.")
@click.option("--window", default=3600, show_default=True, help="Window in seconds.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def check(metric_name: str, max_records: int, window: int, fmt: str) -> None:
    """Check quota for a single metric."""
    collector = MetricCollector()
    rule = QuotaRule(name=metric_name, max_records=max_records, window_seconds=window)
    records_by_name = {metric_name: collector.all(metric_name)}
    results = scan_quotas([rule], records_by_name)

    if not results:
        click.echo(f"No data found for metric '{metric_name}'.")
        return

    result = results[0]
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        status = "EXCEEDED" if result.exceeded else "OK"
        click.echo(
            f"[{status}] {result.metric_name}: "
            f"{result.count_in_window}/{result.limit} records "
            f"in last {window}s"
        )


@quota_cli.command(name="scan")
@click.option("--max-records", default=100, show_default=True)
@click.option("--window", default=3600, show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def scan(max_records: int, window: int, fmt: str) -> None:
    """Scan quotas for all known metrics."""
    collector = MetricCollector()
    names = collector.names()
    if not names:
        click.echo("No metrics recorded.")
        return

    rules = [QuotaRule(name=n, max_records=max_records, window_seconds=window) for n in names]
    records_by_name = {n: collector.all(n) for n in names}
    results = scan_quotas(rules, records_by_name)

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "EXCEEDED" if r.exceeded else "OK"
            click.echo(f"  [{status}] {r.metric_name}: {r.count_in_window}/{r.limit}")
