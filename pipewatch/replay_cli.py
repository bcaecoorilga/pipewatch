"""CLI commands for replaying historical metrics through thresholds."""
import json
from typing import Optional

import click

from pipewatch.history import MetricHistory
from pipewatch.replay import replay


@click.group("replay")
def replay_cli() -> None:
    """Replay historical metrics through threshold rules."""


@replay_cli.command("run")
@click.argument("name")
@click.option("--warn", type=float, default=None, help="Warning threshold.")
@click.option("--crit", type=float, default=None, help="Critical threshold.")
@click.option("--since", type=float, default=None, help="Unix timestamp lower bound.")
@click.option("--history-file", default="pipewatch_history.json", show_default=True)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def run(
    name: str,
    warn: Optional[float],
    crit: Optional[float],
    since: Optional[float],
    history_file: str,
    fmt: str,
) -> None:
    """Replay metric NAME through optional warn/crit thresholds."""
    history = MetricHistory(path=history_file)
    result = replay(history, name=name, warn=warn, crit=crit, since=since)

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if result.total == 0:
        click.echo(f"No history found for metric '{name}'.")
        return

    click.echo(f"Replay: {name}  ({result.total} records)")
    counts = result.status_counts
    click.echo(
        f"  OK={counts.get('ok', 0)}  "
        f"WARNING={counts.get('warning', 0)}  "
        f"CRITICAL={counts.get('critical', 0)}"
    )
    click.echo("")
    click.echo(f"  {'Timestamp':<20} {'Value':>12}  Status")
    click.echo("  " + "-" * 46)
    for ev in result.events:
        ts = f"{ev.metric.timestamp:.2f}"
        click.echo(f"  {ts:<20} {ev.metric.value:>12.4f}  {ev.status.value.upper()}")
