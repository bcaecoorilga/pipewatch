"""CLI commands for managing metric history retention."""

import json

import click

from pipewatch.history import MetricHistory
from pipewatch.retention import RetentionPolicy, prune

DEFAULT_HISTORY_PATH = "pipewatch_history.json"


@click.group("retention")
def retention_cli() -> None:
    """Manage metric history retention policies."""


@retention_cli.command("prune")
@click.option("--path", default=DEFAULT_HISTORY_PATH, show_default=True, help="History file path.")
@click.option("--max-age-hours", type=float, default=None, help="Drop records older than N hours.")
@click.option("--max-records", type=int, default=None, help="Keep only the N most recent records per metric.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output results as JSON.")
def prune_cmd(path: str, max_age_hours, max_records, as_json: bool) -> None:
    """Prune old metric history records according to the given policy."""
    if max_age_hours is None and max_records is None:
        click.echo("Error: specify --max-age-hours and/or --max-records.", err=True)
        raise SystemExit(1)

    policy = RetentionPolicy(max_age_hours=max_age_hours, max_records=max_records)
    results = prune(path, policy)

    if not results:
        click.echo("No metrics found or nothing to prune.")
        return

    if as_json:
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        total_pruned = sum(r.pruned for r in results)
        for r in results:
            if r.pruned:
                click.echo(f"  {r.metric_name}: {r.records_before} → {r.records_after} ({r.pruned} pruned)")
        click.echo(f"\nTotal pruned: {total_pruned} record(s) across {len(results)} metric(s).")


@retention_cli.command("stats")
@click.option("--path", default=DEFAULT_HISTORY_PATH, show_default=True, help="History file path.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def stats(path: str, as_json: bool) -> None:
    """Show record counts for all metrics in history."""
    from pipewatch.history import _load_raw

    raw = _load_raw(path)
    if not raw:
        click.echo("No history found.")
        return

    rows = [{"metric": name, "records": len(recs)} for name, recs in sorted(raw.items())]

    if as_json:
        click.echo(json.dumps(rows, indent=2))
    else:
        for row in rows:
            click.echo(f"  {row['metric']}: {row['records']} record(s)")
