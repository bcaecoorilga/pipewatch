"""CLI commands for metric history and trend analysis."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import click

from pipewatch.history import MetricHistory
from pipewatch.trend import analyze


@click.group()
def history():
    """Commands for metric history and trends."""


@history.command("show")
@click.argument("metric_name")
@click.option("--last", default=24, help="Hours of history to show (default 24).")
@click.option("--path", default=None, help="Custom history file path.")
def show_history(metric_name: str, last: int, path: str) -> None:
    """Show recorded history for a metric."""
    kwargs = {"path": path} if path else {}
    store = MetricHistory(**kwargs)
    since = datetime.utcnow() - timedelta(hours=last)
    records = [r for r in store.for_name(metric_name) if True]
    records = store.since(since)
    records = [r for r in records if r.get("name") == metric_name]
    if not records:
        click.echo(f"No history found for '{metric_name}' in the last {last}h.")
        return
    for r in records:
        click.echo(f"  {r.get('timestamp')}  {r.get('value')}  {r.get('status')}")


@history.command("trend")
@click.argument("metric_name")
@click.option("--path", default=None, help="Custom history file path.")
@click.option("--json", "as_json", is_flag=True, default=False)
def show_trend(metric_name: str, path: str, as_json: bool) -> None:
    """Analyse trend for a metric."""
    kwargs = {"path": path} if path else {}
    store = MetricHistory(**kwargs)
    records = store.for_name(metric_name)
    result = analyze(records)
    if result is None:
        click.echo(f"No data available for '{metric_name}'.")
        return
    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(f"Metric : {result.name}")
        click.echo(f"Count  : {result.count}")
        click.echo(f"Mean   : {result.mean}")
        click.echo(f"Min    : {result.min_value}")
        click.echo(f"Max    : {result.max_value}")
        click.echo(f"Trend  : {result.trend}")


@history.command("clear")
@click.option("--path", default=None)
@click.confirmation_option(prompt="Clear all history?")
def clear_history(path: str) -> None:
    """Delete all stored metric history."""
    kwargs = {"path": path} if path else {}
    MetricHistory(**kwargs).clear()
    click.echo("History cleared.")
