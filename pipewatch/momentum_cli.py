"""CLI commands for momentum analysis."""
from __future__ import annotations

import json

import click

from pipewatch.collector import MetricCollector
from pipewatch.history import MetricHistory
from pipewatch.momentum import detect_momentum, scan_momentums


@click.group(name="momentum")
def momentum_cli() -> None:
    """Analyse metric acceleration / momentum."""


@momentum_cli.command("check")
@click.argument("name")
@click.option("--min-samples", default=5, show_default=True, help="Minimum history samples.")
@click.option("--threshold", default=0.01, show_default=True, help="Significance threshold.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def check(name: str, min_samples: int, threshold: float, as_json: bool) -> None:
    """Check momentum for a single metric NAME."""
    history = MetricHistory()
    result = detect_momentum(name, history, min_samples=min_samples, threshold=threshold)
    if result is None:
        click.echo(f"[momentum] Insufficient data for '{name}'.")
        return
    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        sig = "*" if result.is_significant else ""
        click.echo(
            f"[momentum] {result.name}: {result.direction}{sig} "
            f"(momentum={result.momentum:.4f}, n={result.sample_count})"
        )


@momentum_cli.command("scan")
@click.option("--min-samples", default=5, show_default=True)
@click.option("--threshold", default=0.01, show_default=True)
@click.option("--significant-only", is_flag=True, default=False)
@click.option("--json", "as_json", is_flag=True, default=False)
def scan(min_samples: int, threshold: float, significant_only: bool, as_json: bool) -> None:
    """Scan all metrics for significant momentum."""
    collector = MetricCollector()
    history = MetricHistory()
    metrics = list(collector.all())
    results = scan_momentums(metrics, history, min_samples=min_samples, threshold=threshold)
    if significant_only:
        results = [r for r in results if r.is_significant]
    if not results:
        click.echo("[momentum] No results.")
        return
    if as_json:
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            sig = "*" if r.is_significant else ""
            click.echo(
                f"  {r.name}: {r.direction}{sig} (momentum={r.momentum:.4f}, n={r.sample_count})"
            )
