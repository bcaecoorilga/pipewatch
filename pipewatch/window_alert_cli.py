"""CLI commands for window-based sustained-breach alerting."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.metrics import MetricStatus
from pipewatch.window_alert import WindowAlertRule, scan_window_alerts


@click.group(name="window-alert")
def window_alert_cli() -> None:
    """Window-based sustained-breach alert commands."""


@window_alert_cli.command(name="check")
@click.argument("metric_name")
@click.option("--level", default="WARNING", show_default=True,
              type=click.Choice(["WARNING", "CRITICAL"], case_sensitive=False),
              help="Breach severity level to watch for.")
@click.option("--window", default=5, show_default=True, type=int,
              help="Number of most-recent readings to inspect.")
@click.option("--min-breaches", default=3, show_default=True, type=int,
              help="Minimum breaches required to fire the alert.")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--json", "as_json", is_flag=True, default=False)
@click.pass_context
def check(
    ctx: click.Context,
    metric_name: str,
    level: str,
    window: int,
    min_breaches: int,
    history_file: str,
    as_json: bool,
) -> None:
    """Check whether METRIC_NAME has sustained breaches in recent history."""
    mh = MetricHistory(path=history_file)
    readings = mh.for_name(metric_name)
    rule = WindowAlertRule(
        metric_name=metric_name,
        level=MetricStatus[level.upper()],
        window=window,
        min_breaches=min_breaches,
    )
    from pipewatch.window_alert import check_window_alert
    result = check_window_alert(rule, readings)
    if result is None:
        click.echo(f"No data or invalid rule for '{metric_name}'.")
        return
    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        status = "FIRED" if result.fired else "OK"
        click.echo(
            f"[{status}] {metric_name}: {result.breach_count}/{result.readings_checked} "
            f"breaches (need {min_breaches}) at {level} level"
        )


@window_alert_cli.command(name="scan")
@click.option("--level", default="WARNING", show_default=True,
              type=click.Choice(["WARNING", "CRITICAL"], case_sensitive=False))
@click.option("--window", default=5, show_default=True, type=int)
@click.option("--min-breaches", default=3, show_default=True, type=int)
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def scan(
    level: str,
    window: int,
    min_breaches: int,
    history_file: str,
    as_json: bool,
) -> None:
    """Scan all tracked metrics for sustained breaches."""
    mh = MetricHistory(path=history_file)
    all_records = mh.all()
    names = {m.name for m in all_records}
    rules = [
        WindowAlertRule(
            metric_name=n,
            level=MetricStatus[level.upper()],
            window=window,
            min_breaches=min_breaches,
        )
        for n in names
    ]
    history_map = {n: mh.for_name(n) for n in names}
    results = scan_window_alerts(rules, history_map)
    fired = [r for r in results if r.fired]
    if as_json:
        click.echo(json.dumps([r.to_dict() for r in fired], indent=2))
    else:
        if not fired:
            click.echo("No sustained breaches detected.")
        for r in fired:
            click.echo(
                f"[FIRED] {r.rule.metric_name}: {r.breach_count}/{r.readings_checked} "
                f"breaches at {r.rule.level.value}"
            )
