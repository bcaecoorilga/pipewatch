"""CLI commands for baseline capture and comparison."""
import json
import click
from pipewatch.baseline import save_baseline, load_baseline, compare_to_baseline
from pipewatch.collector import MetricCollector


@click.group()
def baseline():
    """Manage metric baselines."""
    pass


@baseline.command("capture")
@click.option("--label", default="default", help="Baseline label")
@click.pass_context
def capture_baseline(ctx, label):
    """Capture current metrics as a baseline."""
    collector: MetricCollector = ctx.obj.get("collector") if ctx.obj else None
    if collector is None:
        collector = MetricCollector()
    metrics = collector.all()
    if not metrics:
        click.echo("No metrics to capture.")
        return
    entries = save_baseline(metrics, label=label)
    click.echo(f"Captured baseline '{label}' with {len(entries)} metric(s).")


@baseline.command("list")
@click.option("--label", default="default", help="Baseline label")
def list_baseline(label):
    """List stored baseline entries."""
    entries = load_baseline(label=label)
    if not entries:
        click.echo(f"No baseline found for label '{label}'.")
        return
    for name, entry in sorted(entries.items()):
        click.echo(f"  {name}: {entry.value} (captured {entry.captured_at})")


@baseline.command("compare")
@click.option("--label", default="default", help="Baseline label")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
@click.pass_context
def compare(ctx, label, fmt):
    """Compare current metrics against a baseline."""
    collector: MetricCollector = ctx.obj.get("collector") if ctx.obj else None
    if collector is None:
        collector = MetricCollector()
    metrics = collector.all()
    deviations = compare_to_baseline(metrics, label=label)
    if not deviations:
        click.echo("No deviations found (or no matching baseline).")
        return
    if fmt == "json":
        click.echo(json.dumps([d.to_dict() for d in deviations], indent=2))
    else:
        for d in deviations:
            pct_str = f"{d.pct_change:.1f}%" if d.pct_change is not None else "n/a"
            click.echo(f"  {d.name}: baseline={d.baseline_value} current={d.current_value} delta={d.delta:+.4f} ({pct_str})")
