"""Tests for pipewatch.scheduler."""

import time
import pytest
from pipewatch.scheduler import Scheduler, ScheduledTask


@pytest.fixture
def scheduler():
    return Scheduler()


def test_register_task(scheduler):
    scheduler.register("ping", 10, lambda: None)
    assert "ping" in scheduler.task_names


def test_unregister_task(scheduler):
    scheduler.register("ping", 10, lambda: None)
    scheduler.unregister("ping")
    assert "ping" not in scheduler.task_names


def test_task_runs_when_due(scheduler):
    results = []
    scheduler.register("collect", 0, lambda: results.append(1))
    ran = scheduler.run_once()
    assert "collect" in ran
    assert len(results) == 1


def test_task_not_run_before_interval(scheduler):
    results = []
    scheduler.register("collect", 9999, lambda: results.append(1))
    scheduler.run_once()  # first run sets last_run
    ran = scheduler.run_once()  # should not run again
    assert "collect" not in ran
    assert len(results) == 1


def test_disabled_task_skipped(scheduler):
    results = []
    scheduler.register("noop", 0, lambda: results.append(1))
    scheduler._tasks["noop"].enabled = False
    ran = scheduler.run_once()
    assert "noop" not in ran
    assert len(results) == 0


def test_failing_task_does_not_crash_scheduler(scheduler):
    def bad():
        raise RuntimeError("boom")

    scheduler.register("bad", 0, bad)
    ran = scheduler.run_once()  # should not raise
    assert "bad" not in ran


def test_start_stop(scheduler):
    counter = [0]

    def inc():
        counter[0] += 1

    scheduler.register("inc", 0.05, inc)
    scheduler.start(tick=0.05)
    time.sleep(0.3)
    scheduler.stop()
    assert counter[0] >= 2
