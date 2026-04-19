"""Scheduler for periodic metric collection tasks."""

import time
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class ScheduledTask:
    name: str
    interval_seconds: float
    func: Callable
    last_run: Optional[float] = None
    enabled: bool = True

    def is_due(self, now: float) -> bool:
        if not self.enabled:
            return False
        if self.last_run is None:
            return True
        return (now - self.last_run) >= self.interval_seconds


class Scheduler:
    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def register(self, name: str, interval_seconds: float, func: Callable) -> None:
        self._tasks[name] = ScheduledTask(
            name=name, interval_seconds=interval_seconds, func=func
        )

    def unregister(self, name: str) -> None:
        self._tasks.pop(name, None)

    def run_once(self) -> List[str]:
        now = time.time()
        ran = []
        for task in self._tasks.values():
            if task.is_due(now):
                try:
                    task.func()
                    task.last_run = now
                    ran.append(task.name)
                except Exception as e:
                    print(f"[scheduler] Task '{task.name}' failed: {e}")
        return ran

    def start(self, tick: float = 1.0) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, args=(tick,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self, tick: float) -> None:
        while not self._stop_event.is_set():
            self.run_once()
            time.sleep(tick)

    @property
    def task_names(self) -> List[str]:
        return list(self._tasks.keys())
