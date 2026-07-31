# RPA Scheduling Module

Task scheduling patterns including cron-based execution, event-driven triggers, queue-based processing, and integration with system schedulers.

## Cron-Based Scheduling

### APScheduler Integration

```python
#!/usr/bin/env python3
"""Cron-based scheduling - run with: uv run script.py"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import structlog

log = structlog.get_logger()


class RPAScheduler:
    """Schedule RPA tasks with APScheduler."""
    
    def __init__(self, use_blocking: bool = True):
        if use_blocking:
            self.scheduler = BlockingScheduler()
        else:
            self.scheduler = BackgroundScheduler()
        
        # Add event listeners
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    def _job_listener(self, event):
        """Handle job events."""
        if event.exception:
            log.error("job_failed", job_id=event.job_id, error=str(event.exception))
        else:
            log.info("job_completed", job_id=event.job_id)
    
    def add_cron_job(
        self,
        func,
        job_id: str,
        hour: int = None,
        minute: int = None,
        day_of_week: str = None,
        day: int = None,
        month: int = None,
        **kwargs
    ):
        """Add cron-scheduled job."""
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            day_of_week=day_of_week,
            day=day,
            month=month
        )
        
        self.scheduler.add_job(func, trigger, id=job_id, **kwargs)
        log.info("job_added", job_id=job_id, trigger=str(trigger))
    
    def add_interval_job(
        self,
        func,
        job_id: str,
        seconds: int = None,
        minutes: int = None,
        hours: int = None,
        **kwargs
    ):
        """Add interval-scheduled job."""
        trigger = IntervalTrigger(
            seconds=seconds,
            minutes=minutes,
            hours=hours
        )
        
        self.scheduler.add_job(func, trigger, id=job_id, **kwargs)
    
    def add_one_time_job(self, func, job_id: str, run_at: datetime, **kwargs):
        """Add one-time scheduled job."""
        trigger = DateTrigger(run_date=run_at)
        self.scheduler.add_job(func, trigger, id=job_id, **kwargs)
    
    def remove_job(self, job_id: str):
        """Remove scheduled job."""
        self.scheduler.remove_job(job_id)
    
    def pause_job(self, job_id: str):
        """Pause job."""
        self.scheduler.pause_job(job_id)
    
    def resume_job(self, job_id: str):
        """Resume paused job."""
        self.scheduler.resume_job(job_id)
    
    def get_jobs(self) -> list[dict]:
        """Get all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs
    
    def start(self):
        """Start scheduler."""
        log.info("scheduler_starting")
        self.scheduler.start()
    
    def shutdown(self, wait: bool = True):
        """Shutdown scheduler."""
        self.scheduler.shutdown(wait=wait)


# Example RPA tasks
def daily_report_task():
    """Daily report extraction task."""
    log.info("task_started", task="daily_report")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("https://example.com/reports")
            # ... extraction logic
            log.info("task_completed", task="daily_report")
        except Exception as e:
            log.error("task_failed", task="daily_report", error=str(e))
        finally:
            browser.close()


def hourly_monitor_task():
    """Hourly monitoring task."""
    log.info("task_started", task="hourly_monitor")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("https://example.com/status")
            status = page.locator("#system-status").text_content()
            log.info("status_check", status=status)
        finally:
            browser.close()


def run_scheduled_tasks():
    """Run scheduler with example tasks."""
    scheduler = RPAScheduler(use_blocking=True)
    
    # Daily at 6 AM
    scheduler.add_cron_job(
        daily_report_task,
        job_id="daily_report",
        hour=6,
        minute=0
    )
    
    # Every hour
    scheduler.add_interval_job(
        hourly_monitor_task,
        job_id="hourly_monitor",
        hours=1
    )
    
    # Weekdays at 9 AM
    scheduler.add_cron_job(
        lambda: log.info("weekday_task"),
        job_id="weekday_task",
        day_of_week="mon-fri",
        hour=9,
        minute=0
    )
    
    # One-time job
    scheduler.add_one_time_job(
        lambda: log.info("one_time_task"),
        job_id="one_time",
        run_at=datetime.now() + timedelta(minutes=5)
    )
    
    # Show jobs
    for job in scheduler.get_jobs():
        log.info("scheduled_job", **job)
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.shutdown()


if __name__ == "__main__":
    run_scheduled_tasks()
```

---

## Schedule-Based Automation Framework

```python
#!/usr/bin/env python3
"""Schedule-based automation framework - run with: uv run script.py"""

from schedule import every, run_pending
from playwright.sync_api import sync_playwright
from dataclasses import dataclass
from typing import Callable, Optional, Any
from datetime import datetime, time
import threading
import time as time_module
import json
import structlog

log = structlog.get_logger()


@dataclass
class ScheduledTask:
    """Scheduled task definition."""
    name: str
    action: Callable
    schedule_expr: str  # e.g., "every().day.at('09:00')"
    enabled: bool = True
    last_run: Optional[datetime] = None
    last_result: Optional[Any] = None
    run_count: int = 0
    error_count: int = 0


class TaskScheduler:
    """Simple task scheduler using schedule library."""
    
    def __init__(self):
        self.tasks: dict[str, ScheduledTask] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def add_task(
        self,
        name: str,
        action: Callable,
        interval: str = "day",
        at_time: str = None,
        every_n: int = 1
    ) -> ScheduledTask:
        """Add scheduled task."""
        task = ScheduledTask(
            name=name,
            action=action,
            schedule_expr=f"every {every_n} {interval}" + (f" at {at_time}" if at_time else "")
        )
        
        # Create wrapper that updates task stats
        def wrapper():
            task.run_count += 1
            task.last_run = datetime.now()
            try:
                result = action()
                task.last_result = result
                log.info("task_completed", name=name, result=result)
            except Exception as e:
                task.error_count += 1
                task.last_result = str(e)
                log.error("task_failed", name=name, error=str(e))
        
        # Build schedule
        job = every(every_n)
        
        if interval == "second":
            job = job.seconds
        elif interval == "minute":
            job = job.minutes
        elif interval == "hour":
            job = job.hours
        elif interval == "day":
            job = job.days
        elif interval == "week":
            job = job.weeks
        elif interval == "monday":
            job = job.monday
        elif interval == "tuesday":
            job = job.tuesday
        elif interval == "wednesday":
            job = job.wednesday
        elif interval == "thursday":
            job = job.thursday
        elif interval == "friday":
            job = job.friday
        elif interval == "saturday":
            job = job.saturday
        elif interval == "sunday":
            job = job.sunday
        
        if at_time:
            job.at(at_time)
        
        job.do(wrapper)
        
        self.tasks[name] = task
        return task
    
    def run_once(self, name: str):
        """Run task immediately."""
        if name in self.tasks:
            task = self.tasks[name]
            task.action()
    
    def start(self, blocking: bool = True):
        """Start scheduler."""
        self._running = True
        log.info("scheduler_started")
        
        if blocking:
            self._run_loop()
        else:
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
    
    def _run_loop(self):
        """Main scheduler loop."""
        while self._running:
            run_pending()
            time_module.sleep(1)
    
    def stop(self):
        """Stop scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        log.info("scheduler_stopped")
    
    def get_status(self) -> list[dict]:
        """Get task status."""
        return [
            {
                "name": t.name,
                "schedule": t.schedule_expr,
                "enabled": t.enabled,
                "last_run": t.last_run.isoformat() if t.last_run else None,
                "run_count": t.run_count,
                "error_count": t.error_count
            }
            for t in self.tasks.values()
        ]


def example_scheduler():
    scheduler = TaskScheduler()
    
    def scrape_data():
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://example.com")
            title = page.title()
            browser.close()
            return title
    
    # Every day at 9 AM
    scheduler.add_task("daily_scrape", scrape_data, interval="day", at_time="09:00")
    
    # Every 30 minutes
    scheduler.add_task("frequent_check", lambda: log.info("check"), interval="minute", every_n=30)
    
    # Every Monday at 8 AM
    scheduler.add_task("weekly_report", lambda: log.info("weekly"), interval="monday", at_time="08:00")
    
    print(json.dumps(scheduler.get_status(), indent=2))
    
    try:
        scheduler.start(blocking=True)
    except KeyboardInterrupt:
        scheduler.stop()


if __name__ == "__main__":
    example_scheduler()
```

---

## Queue-Based Processing

```python
#!/usr/bin/env python3
"""Queue-based task processing - run with: uv run script.py"""

import asyncio
from asyncio import Queue
from playwright.async_api import async_playwright
from dataclasses import dataclass
from typing import Any, Callable, Awaitable
from datetime import datetime
import json
import structlog

log = structlog.get_logger()


@dataclass
class Task:
    """Task for queue processing."""
    id: str
    action: str
    params: dict
    priority: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def __lt__(self, other):
        return self.priority > other.priority  # Higher priority first


@dataclass
class TaskResult:
    """Result of task execution."""
    task_id: str
    success: bool
    result: Any = None
    error: str = None
    duration_seconds: float = 0


class TaskQueue:
    """Async task queue with priority support."""
    
    def __init__(self, max_workers: int = 3):
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.max_workers = max_workers
        self.results: dict[str, TaskResult] = {}
        self.handlers: dict[str, Callable] = {}
        self._running = False
    
    def register_handler(self, action: str, handler: Callable):
        """Register action handler."""
        self.handlers[action] = handler
    
    async def submit(self, task: Task):
        """Submit task to queue."""
        await self.queue.put((task.priority, task))
        log.info("task_submitted", task_id=task.id, action=task.action)
    
    async def _process_task(self, task: Task) -> TaskResult:
        """Process single task."""
        start = datetime.now()
        
        if task.action not in self.handlers:
            return TaskResult(
                task_id=task.id,
                success=False,
                error=f"Unknown action: {task.action}"
            )
        
        try:
            handler = self.handlers[task.action]
            result = await handler(**task.params)
            duration = (datetime.now() - start).total_seconds()
            
            return TaskResult(
                task_id=task.id,
                success=True,
                result=result,
                duration_seconds=duration
            )
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            return TaskResult(
                task_id=task.id,
                success=False,
                error=str(e),
                duration_seconds=duration
            )
    
    async def _worker(self, worker_id: int):
        """Worker coroutine."""
        log.info("worker_started", worker_id=worker_id)
        
        while self._running:
            try:
                priority, task = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                
                log.info("task_processing", worker_id=worker_id, task_id=task.id)
                result = await self._process_task(task)
                self.results[task.id] = result
                self.queue.task_done()
                
                if result.success:
                    log.info("task_completed", task_id=task.id, duration=result.duration_seconds)
                else:
                    log.error("task_failed", task_id=task.id, error=result.error)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                log.error("worker_error", worker_id=worker_id, error=str(e))
    
    async def start(self):
        """Start queue processing."""
        self._running = True
        workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]
        log.info("queue_started", workers=self.max_workers)
        await asyncio.gather(*workers)
    
    def stop(self):
        """Stop queue processing."""
        self._running = False
    
    def get_result(self, task_id: str) -> TaskResult:
        """Get task result."""
        return self.results.get(task_id)


async def example_queue():
    queue = TaskQueue(max_workers=2)
    
    # Register handlers
    async def scrape_handler(url: str, selector: str) -> dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            
            data = await page.locator(selector).all_text_contents()
            await browser.close()
            
            return {"url": url, "items": len(data)}
    
    async def screenshot_handler(url: str, path: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            await page.screenshot(path=path)
            await browser.close()
            return path
    
    queue.register_handler("scrape", scrape_handler)
    queue.register_handler("screenshot", screenshot_handler)
    
    # Submit tasks
    await queue.submit(Task(
        id="task-1",
        action="scrape",
        params={"url": "https://example.com", "selector": "a"},
        priority=1
    ))
    
    await queue.submit(Task(
        id="task-2",
        action="screenshot",
        params={"url": "https://example.com", "path": "example.png"},
        priority=2  # Higher priority
    ))
    
    # Run for 30 seconds then stop
    async def stop_after():
        await asyncio.sleep(30)
        queue.stop()
    
    await asyncio.gather(
        queue.start(),
        stop_after()
    )
    
    # Check results
    for task_id in ["task-1", "task-2"]:
        result = queue.get_result(task_id)
        if result:
            print(f"{task_id}: {result.success} - {result.result or result.error}")


if __name__ == "__main__":
    asyncio.run(example_queue())
```

---

## System Scheduler Integration

### Crontab (Linux/macOS)

```python
#!/usr/bin/env python3
"""Crontab integration - run with: uv run script.py"""

from crontab import CronTab
import os
import sys


class CrontabManager:
    """Manage system crontab entries."""
    
    def __init__(self, user: str = None):
        self.user = user or os.getenv("USER")
        self.cron = CronTab(user=self.user)
    
    def add_job(
        self,
        command: str,
        comment: str,
        minute: str = "*",
        hour: str = "*",
        day: str = "*",
        month: str = "*",
        dow: str = "*"
    ):
        """Add crontab entry."""
        job = self.cron.new(command=command, comment=comment)
        job.setall(f"{minute} {hour} {day} {month} {dow}")
        self.cron.write()
        print(f"Added: {job}")
    
    def add_rpa_job(
        self,
        script_path: str,
        comment: str,
        schedule: str
    ):
        """Add RPA script to crontab."""
        python_path = sys.executable
        command = f"cd {os.path.dirname(script_path)} && {python_path} {script_path} >> /var/log/rpa.log 2>&1"
        
        job = self.cron.new(command=command, comment=comment)
        job.setall(schedule)
        self.cron.write()
    
    def list_jobs(self) -> list[dict]:
        """List all crontab entries."""
        jobs = []
        for job in self.cron:
            jobs.append({
                "command": str(job.command),
                "comment": job.comment,
                "schedule": str(job.slices),
                "enabled": job.is_enabled()
            })
        return jobs
    
    def remove_job(self, comment: str):
        """Remove job by comment."""
        self.cron.remove_all(comment=comment)
        self.cron.write()
    
    def enable_job(self, comment: str):
        """Enable job by comment."""
        for job in self.cron.find_comment(comment):
            job.enable()
        self.cron.write()
    
    def disable_job(self, comment: str):
        """Disable job by comment."""
        for job in self.cron.find_comment(comment):
            job.enable(False)
        self.cron.write()


def setup_crontab():
    manager = CrontabManager()
    
    # Add daily report at 6 AM
    manager.add_rpa_job(
        script_path="/home/user/rpa/daily_report.py",
        comment="RPA Daily Report",
        schedule="0 6 * * *"
    )
    
    # Add hourly check
    manager.add_rpa_job(
        script_path="/home/user/rpa/status_check.py",
        comment="RPA Status Check",
        schedule="0 * * * *"
    )
    
    # List jobs
    for job in manager.list_jobs():
        print(f"{job['schedule']}: {job['comment']}")


if __name__ == "__main__":
    setup_crontab()
```

### Windows Task Scheduler

```python
#!/usr/bin/env python3
"""Windows Task Scheduler integration - run with: uv run script.py"""

import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime


class WindowsTaskScheduler:
    """Manage Windows scheduled tasks."""
    
    def __init__(self):
        self.schtasks = "schtasks.exe"
    
    def create_task(
        self,
        name: str,
        script_path: str,
        schedule_type: str,
        start_time: str = "09:00",
        days: str = None
    ):
        """Create Windows scheduled task."""
        python_exe = "python.exe"
        
        cmd = [
            self.schtasks,
            "/Create",
            "/TN", name,
            "/TR", f'"{python_exe}" "{script_path}"',
            "/SC", schedule_type.upper(),
            "/ST", start_time,
            "/F"  # Force overwrite
        ]
        
        if days and schedule_type.upper() == "WEEKLY":
            cmd.extend(["/D", days])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Task '{name}' created successfully")
            return True
        else:
            print(f"Error: {result.stderr}")
            return False
    
    def delete_task(self, name: str):
        """Delete scheduled task."""
        cmd = [self.schtasks, "/Delete", "/TN", name, "/F"]
        subprocess.run(cmd, capture_output=True)
    
    def run_task(self, name: str):
        """Run task immediately."""
        cmd = [self.schtasks, "/Run", "/TN", name]
        subprocess.run(cmd, capture_output=True)
    
    def enable_task(self, name: str):
        """Enable task."""
        cmd = [self.schtasks, "/Change", "/TN", name, "/ENABLE"]
        subprocess.run(cmd, capture_output=True)
    
    def disable_task(self, name: str):
        """Disable task."""
        cmd = [self.schtasks, "/Change", "/TN", name, "/DISABLE"]
        subprocess.run(cmd, capture_output=True)
    
    def list_tasks(self, folder: str = "\\") -> list[dict]:
        """List scheduled tasks."""
        cmd = [self.schtasks, "/Query", "/FO", "CSV", "/V"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        tasks = []
        lines = result.stdout.strip().split("\n")
        
        if len(lines) > 1:
            headers = lines[0].replace('"', '').split(",")
            for line in lines[1:]:
                values = line.replace('"', '').split(",")
                if len(values) == len(headers):
                    task = dict(zip(headers, values))
                    tasks.append(task)
        
        return tasks


def setup_windows_tasks():
    scheduler = WindowsTaskScheduler()
    
    # Daily task at 6 AM
    scheduler.create_task(
        name="RPA_DailyReport",
        script_path="C:\\RPA\\daily_report.py",
        schedule_type="DAILY",
        start_time="06:00"
    )
    
    # Weekly on Monday
    scheduler.create_task(
        name="RPA_WeeklyReport",
        script_path="C:\\RPA\\weekly_report.py",
        schedule_type="WEEKLY",
        start_time="09:00",
        days="MON"
    )


if __name__ == "__main__":
    setup_windows_tasks()
```

---

## Best Practices

1. **Use appropriate scheduler** - APScheduler for in-process, system crontab for persistence
2. **Implement logging** - Track all scheduled task executions
3. **Handle failures gracefully** - Retry logic and error notifications
4. **Monitor task health** - Alert on missed or failed runs
5. **Use queues for high volume** - Decouple submission from execution
6. **Consider timezone** - Explicitly set timezone for scheduled tasks

---

**Next Module:** See **rpa-ocr-vision.md** for visual automation and OCR.
