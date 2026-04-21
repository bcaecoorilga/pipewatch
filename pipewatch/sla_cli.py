"""CLI commands for SLA tracking."""
from __future__ import annotations

import json
from typing import List

import click

from pipewatch.history import MetricHistory
from pipewatch.sla import SLARule, SLAResult, scan_sla


@click.group(name="sla")
def sla_cli():
    """SLA compliance checking for pipeline metrics."""


def _format_result(result: SLAResult) -> str:
    status = "BREACHED" if result.breached else "OK"
    return (
        f"[{status}] {result.rule.name} | metric={result.rule.metric_name} "
        f"critical={result.critical_count}/{result.total} "
        f"({result.critical_ratio * 100:.1f}%) "
        f"limit={result.rule.max_critical_ratio * 100:.1f}%"
    )


@sla_cli.command(name="check")
@click.option("--metric", required=True, help="Metric name to evaluate.")
@click.option("--max-critical-ratio", default=0.1, show_default=True, type=float,
              help="Max allowed fraction of CRITICAL readings (0.0–1.0).")
@click.option("--window", default=3600.0, show_default=True, type=float,
              help="Lookback window in seconds.")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def check(metric: str, max_critical_ratio: float, window: float,
          history_file: str, fmt: str):
    """Check a single SLA rule against metric history."""
    history = MetricHistory(path=history_file)
    rule = SLARule(
        name=f"sla:{metric}",
        metric_name=metric,
        max_critical_ratio=max_critical_ratio,
        window_seconds=window,
    )
    result = __import__("pipewatch.sla", fromlist=["check_sla"]).check_sla(rule, history)
    if result is None:
        click.echo("Invalid SLA rule.", err=True)
        raise SystemExit(1)
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(_format_result(result))
    if result.breached:
        raise SystemExit(2)


@sla_cli.command(name="scan")
@click.option("--config-file", required=True, help="JSON file with list of SLA rule configs.")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def scan(config_file: str, history_file: str, fmt: str):
    """Scan all SLA rules defined in a config file."""
    with open(config_file) as fh:
        raw: List[dict] = json.load(fh)
    rules = [
        SLARule(
            name=r["name"],
            metric_name=r["metric_name"],
            max_critical_ratio=r.get("max_critical_ratio", 0.1),
            window_seconds=r.get("window_seconds", 3600.0),
        )
        for r in raw
    ]
    history = MetricHistory(path=history_file)
    results = scan_sla(rules, history)
    if fmt == "json":
        click.echo(json.dumps([res.to_dict() for res in results], indent=2))
    else:
        if not results:
            click.echo("No SLA rules evaluated.")
            return
        for res in results:
            click.echo(_format_result(res))
        breached = [r for r in results if r.breached]
        click.echo(f"\n{len(breached)}/{len(results)} SLA(s) breached.")
        if breached:
            raise SystemExit(2)
