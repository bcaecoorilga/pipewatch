"""CLI commands for pipeline snapshots."""
from pathlib import Path

import click

from pipewatch.snapshot import capture, load_snapshots, save_snapshot
from pipewatch.collector import MetricCollector
from pipewatch.exporter import export_report_text

DEFAULT_SNAPSHOT_FILE = Path(".pipewatch") / "snapshots.jsonl"


@click.group()
def snapshot():
    """Manage pipeline snapshots."""


@snapshot.command("take")
@click.option("--label", default=None, help="Optional label for the snapshot.")
@click.option(
    "--file", "snap_file", default=str(DEFAULT_SNAPSHOT_FILE), show_default=True
)
@click.pass_context
def take_snapshot(ctx, label, snap_file):
    """Capture current metrics into a snapshot."""
    collector: MetricCollector = ctx.obj.get("collector") if ctx.obj else None
    if collector is None:
        click.echo("No collector available in context.", err=True)
        raise SystemExit(1)
    metrics = collector.all()
    snap = capture(metrics, label=label)
    save_snapshot(snap, Path(snap_file))
    click.echo(f"Snapshot saved ({len(snap.metrics)} metrics)" + (f" [{label}]" if label else ""))


@snapshot.command("list")
@click.option(
    "--file", "snap_file", default=str(DEFAULT_SNAPSHOT_FILE), show_default=True
)
def list_snapshots(snap_file):
    """List all saved snapshots."""
    snaps = load_snapshots(Path(snap_file))
    if not snaps:
        click.echo("No snapshots found.")
        return
    for i, s in enumerate(snaps):
        import datetime
        ts = datetime.datetime.fromtimestamp(s.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        label = f" [{s.label}]" if s.label else ""
        click.echo(f"  {i:>3}  {ts}{label}  ({len(s.metrics)} metrics)")


@snapshot.command("show")
@click.argument("index", type=int)
@click.option(
    "--file", "snap_file", default=str(DEFAULT_SNAPSHOT_FILE), show_default=True
)
def show_snapshot(index, snap_file):
    """Show metrics for a specific snapshot by index."""
    snaps = load_snapshots(Path(snap_file))
    if index < 0 or index >= len(snaps):
        click.echo(f"Index {index} out of range (0-{len(snaps)-1}).", err=True)
        raise SystemExit(1)
    snap = snaps[index]
    import json
    click.echo(json.dumps(snap.to_dict(), indent=2))
