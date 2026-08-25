"""
WebScraper Pro - Task Scheduler
Schedules and manages recurring scraping tasks.
"""

import threading
import time
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class ScheduleType(Enum):
    ONCE = "once"
    INTERVAL = "interval"  # Every N seconds/minutes/hours
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"  # Custom cron-like expression


@dataclass
class ScheduledTask:
    """A scheduled scraping task."""
    id: str
    name: str
    url: str
    schedule_type: ScheduleType
    enabled: bool = True
    interval_seconds: int = 3600  # For INTERVAL type
    specific_time: str = ""  # HH:MM for daily
    day_of_week: int = 0  # 0=Monday for weekly
    day_of_month: int = 1  # For monthly
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    total_runs: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    config: Dict[str, Any] = field(default_factory=dict)  # Scraper config
    export_format: str = "json"
    export_path: str = ""

    def calculate_next_run(self) -> Optional[datetime]:
        """Calculate when this task should run next."""
        now = datetime.now()

        if self.schedule_type == ScheduleType.ONCE:
            if not self.next_run:
                # Schedule for 1 minute from now if not set
                return now + timedelta(minutes=1)
            return None  # One-time tasks don't repeat

        elif self.schedule_type == ScheduleType.INTERVAL:
            return now + timedelta(seconds=self.interval_seconds)

        elif self.schedule_type == ScheduleType.DAILY:
            if self.specific_time:
                parts = self.specific_time.split(":")
                if len(parts) == 2:
                    target = now.replace(hour=int(parts[0]), minute=int(parts[1]), second=0, microsecond=0)
                    if target <= now:
                        target += timedelta(days=1)
                    return target
            return now + timedelta(days=1)

        elif self.schedule_type == ScheduleType.WEEKLY:
            target = now + timedelta(days=(7 - now.weekday() + self.day_of_week) % 7)
            if self.specific_time:
                parts = self.specific_time.split(":")
                if len(parts) == 2:
                    target = target.replace(hour=int(parts[0]), minute=int(parts[1]), second=0)
            return target

        elif self.schedule_type == ScheduleType.MONTHLY:
            target = now.replace(day=self.day_of_month, hour=0, minute=0, second=0, microsecond=0)
            if target <= now:
                if now.month == 12:
                    target = target.replace(year=now.year + 1, month=1)
                else:
                    target = target.replace(month=now.month + 1)
            return target

        return None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "schedule_type": self.schedule_type.value,
            "enabled": self.enabled,
            "interval_seconds": self.interval_seconds,
            "specific_time": self.specific_time,
            "day_of_week": self.day_of_week,
            "day_of_month": self.day_of_month,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "total_runs": self.total_runs,
            "created_at": self.created_at,
            "config": self.config,
            "export_format": self.export_format,
            "export_path": self.export_path,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ScheduledTask":
        data = data.copy()
        data["schedule_type"] = ScheduleType(data["schedule_type"])
        return cls(**data)


class TaskScheduler:
    """
    Manages scheduled scraping tasks.
    
    Features:
    - Multiple schedule types (once, interval, daily, weekly, monthly)
    - Enable/disable individual tasks
    - Task persistence to JSON file
    - Execution callback support
    - Thread-safe task management
    - Task history and statistics
    """

    def __init__(self, storage_path: str = "scheduled_tasks.json"):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._history: List[Dict] = []
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable] = None
        self._storage_path = storage_path
        self._stop_event = threading.Event()
        self._load_tasks()

    def add_task(self, task: ScheduledTask) -> None:
        """Add a new scheduled task."""
        with self._lock:
            task.next_run = task.calculate_next_run()
            if task.next_run:
                task.next_run = task.next_run.isoformat()
            self._tasks[task.id] = task
            self._save_tasks()

    def remove_task(self, task_id: str) -> bool:
        """Remove a task."""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                self._save_tasks()
                return True
            return False

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        with self._lock:
            return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[ScheduledTask]:
        with self._lock:
            return list(self._tasks.values())

    def enable_task(self, task_id: str, enabled: bool = True) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].enabled = enabled
                if enabled:
                    task = self._tasks[task_id]
                    task.next_run = task.calculate_next_run()
                    if task.next_run:
                        task.next_run = task.next_run.isoformat()
                self._save_tasks()

    def set_callback(self, callback: Callable) -> None:
        """Set the callback function to execute when a task is triggered."""
        self._callback = callback

    def start(self) -> None:
        """Start the scheduler daemon thread."""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self) -> None:
        """Main scheduler loop."""
        while not self._stop_event.is_set():
            now = datetime.now()
            tasks_to_run = []

            with self._lock:
                for task_id, task in self._tasks.items():
                    if not task.enabled:
                        continue
                    if task.next_run:
                        next_dt = datetime.fromisoformat(task.next_run)
                        if now >= next_dt:
                            tasks_to_run.append(task)

            for task in tasks_to_run:
                self._execute_task(task)

            self._stop_event.wait(10)  # Check every 10 seconds

    def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a scheduled task."""
        start = datetime.now()
        result = {
            "task_id": task.id,
            "task_name": task.name,
            "url": task.url,
            "started_at": start.isoformat(),
            "completed_at": None,
            "success": False,
            "error": None,
            "records_scraped": 0,
        }

        try:
            if self._callback:
                records = self._callback(task)
                result["success"] = True
                result["records_scraped"] = records if isinstance(records, int) else 0
        except Exception as e:
            result["error"] = str(e)[:200]

        result["completed_at"] = datetime.now().isoformat()

        with self._lock:
            task.last_run = start.isoformat()
            task.total_runs += 1

            # Calculate next run
            next_dt = task.calculate_next_run()
            if next_dt:
                task.next_run = next_dt.isoformat()
            else:
                task.enabled = False  # One-time task completed
                task.next_run = None

            self._history.append(result)
            if len(self._history) > 1000:
                self._history = self._history[-500:]
            self._save_tasks()

    def get_history(self, limit: int = 50) -> List[Dict]:
        with self._lock:
            return list(reversed(self._history[-limit:]))

    def get_summary(self) -> Dict:
        with self._lock:
            enabled = sum(1 for t in self._tasks.values() if t.enabled)
            total_runs = sum(t.total_runs for t in self._tasks.values())
            return {
                "total_tasks": len(self._tasks),
                "enabled_tasks": enabled,
                "total_executions": total_runs,
                "history_entries": len(self._history),
                "is_running": self._running,
            }

    def _save_tasks(self) -> None:
        try:
            data = {tid: task.to_dict() for tid, task in self._tasks.items()}
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_tasks(self) -> None:
        if not os.path.exists(self._storage_path):
            return
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for tid, tdata in data.items():
                self._tasks[tid] = ScheduledTask.from_dict(tdata)
        except Exception:
            pass
