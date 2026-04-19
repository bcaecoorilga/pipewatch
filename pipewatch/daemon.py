"""Daemon entry point that wires Scheduler with MetricCollector and AlertManager."""

import click
from pipewatch.scheduler import Scheduler
from pipewatch.collector import MetricCollector
from pipewatch.alerts import AlertManager
from pipewatch.notifier import LogNotifier
from pipewatch.config import PipewatchConfig, load_config


def build_daemon(config: PipewatchConfig):
    collector = MetricCollector()
    alert_manager = AlertManager()
    notifier = LogNotifier()
    scheduler = Scheduler()

    for threshold_cfg in config.thresholds:
        from pipewatch.metrics import MetricThreshold
        collector.register_threshold(
            threshold_cfg.metric_name,
            MetricThreshold(
                warning=threshold_cfg.warning,
                critical=threshold_cfg.critical,
            ),
        )

    def flush_alerts():
        alerts = alert_manager.pending()
        for alert in alerts:
            notifier.send(alert)
        alert_manager.clear_pending()

    def collect_and_alert():
        metrics = collector.all_latest()
        for metric in metrics:
            triggered = alert_manager.evaluate(metric)
            if triggered:
                notifier.send(triggered)

    scheduler.register("collect_and_alert", config.poll_interval, collect_and_alert)
    scheduler.register("flush_alerts", config.poll_interval * 2, flush_alerts)

    return scheduler, collector, alert_manager


@click.command()
@click.option("--config", "config_path", default=None, help="Path to config file.")
def run_daemon(config_path):
    """Start the pipewatch monitoring daemon."""
    config = load_config(config_path) if config_path else None
    from pipewatch.config import default_config
    cfg = config or default_config()

    scheduler, collector, alert_manager = build_daemon(cfg)
    click.echo("[pipewatch] daemon starting...")
    try:
        scheduler.start()
        click.echo("[pipewatch] daemon running. Press Ctrl+C to stop.")
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\n[pipewatch] shutting down.")
        scheduler.stop()


if __name__ == "__main__":
    run_daemon()
