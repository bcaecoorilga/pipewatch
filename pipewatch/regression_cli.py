"""CLI commands for regression detection."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.regression import detect_regression, scan_regressions


@click.group("regression")
def regression_cli() -> None:
    """Regression detection commands."""


@regression_cli.command("check")
@click.argument("name")
@click.option("--baseline", default=20, show_default=True, help="Baseline window size.")
@click.option("--recent", default=5, show_default=True, help="Recent window size.")
@click.option("--threshold", default=15.0, show_default=True, help="Deviation % threshold.")
@click.option("--json", "as_json", is_flag=True, default=False)
@click.pass_context
def check(ctx: click.Context, name: str, baseline: int, recent: int, threshold: float, as_json: bool) -> None:
    """Check regression for a single metric NAME."""
    history: MetricHistory = ctx.obj["history"]
    result = detect_regression(history, name, baseline, recent, threshold)
    if result is None:
        click.echo(f"Insufficient history for '{name}' (need {baseline + recent} records).")
        return
    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        status = "REGRESSED" if result.regressed else "OK"
        click.echo(
            f"{name}: {status}  baseline={result.mean_baseline:.4f}  "
            f"recent={result.recent_mean:.4f}  deviation={result.deviation_pct:+.2f}%"
        )


@regression_cli.command("scan")
@click.option("--baseline", default=20, show_default=True)
@click.option("--recent", default=5, show_default=True)
@click.option("--threshold", default=15.0, show_default=True)
@click.option("--only-regressed", is_flag=True, default=False)
@click.option("--json", "as_json", is_flag=True, default=False)
@click.pass_context
def scan(
    ctx: click.Context,
    baseline: int,
    recent: int,
    threshold: float,
    only_regressed: bool,
    as_json: bool,
) -> None:
    """Scan all metrics for regressions."""
    collector: MetricCollector = ctx.obj["collector"]
    history: MetricHistory = ctx.obj["history"]
    metrics = collector.all()
    results = scan_regressions(history, metrics, baseline, recent, threshold)
    if only_regressed:
        results = [r for r in results if r.regressed]
    if not results:
        click.echo("No regression data available.")
        return
    if as_json:
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "REGRESSED" if r.regressed else "OK"
            click.echo(
                f"{r.name}: {status}  deviation={r.deviation_pct:+.2f}%  "
                f"(threshold ±{r.threshold_pct:.1f}%)"
            )
