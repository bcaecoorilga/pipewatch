"""Tests for the Reporter and PipelineReport."""
import pytest

from pipewatch.collector import MetricCollector
from pipewatch.alerts import AlertManager
from pipewatch.metrics import MetricThreshold, MetricStatus
from pipewatch.reporter import Reporter, PipelineReport


@pytest.fixture
def setup():
    collector = MetricCollector()
    alert_manager = AlertManager()
    return collector, alert_manager


def test_empty_report(setup):
    collector, alert_manager = setup
    reporter = Reporter(collector, alert_manager)
    report = reporter.generate()
    assert report.total_metrics == 0
    assert report.ok_count == 0
    assert report.warning_count == 0
    assert report.critical_count == 0


def test_report_counts_ok(setup):
    collector, alert_manager = setup
    collector.record("latency", 0.5)
    reporter = Reporter(collector, alert_manager)
    report = reporter.generate()
    assert report.total_metrics == 1
    assert report.ok_count == 1


def test_report_counts_warning(setup):
    collector, alert_manager = setup
    collector.register_threshold("latency", MetricThreshold(warning_above=1.0, critical_above=5.0))
    collector.record("latency", 2.0)
    reporter = Reporter(collector, alert_manager)
    report = reporter.generate()
    assert report.warning_count == 1
    assert report.critical_count == 0


def test_report_counts_critical(setup):
    collector, alert_manager = setup
    collector.register_threshold("latency", MetricThreshold(warning_above=1.0, critical_above=5.0))
    collector.record("latency", 6.0)
    reporter = Reporter(collector, alert_manager)
    report = reporter.generate()
    assert report.critical_count == 1


def test_report_to_dict_structure(setup):
    collector, alert_manager = setup
    collector.record("rows", 100)
    reporter = Reporter(collector, alert_manager)
    d = reporter.generate().to_dict()
    assert "generated_at" in d
    assert "summary" in d
    assert "metrics" in d
    assert "alerts" in d
    assert d["summary"]["total"] == 1


def test_report_includes_alerts(setup):
    collector, alert_manager = setup
    collector.register_threshold("errors", MetricThreshold(warning_above=0, critical_above=10))
    metric = collector.record("errors", 5)
    alert_manager.trigger(metric)
    reporter = Reporter(collector, alert_manager)
    report = reporter.generate()
    assert len(report.alerts) == 1
