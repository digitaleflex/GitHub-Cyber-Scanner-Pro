# Temporal Scheduling

> Cron, interval, and calendar-based workflow schedules

## Overview

Temporal Schedules allow you to run workflows on a recurring basis - daily reports, hourly checks, weekly cleanups, and more.

---

## Schedule Types

| Type | Use Case | Example |
|------|----------|---------|
| **Cron** | Time-based patterns | "Every day at 9 AM" |
| **Interval** | Fixed intervals | "Every 5 minutes" |
| **Calendar** | Complex patterns | "First Monday of month at 10 AM" |

---

## Creating Schedules via Python

### Basic Cron Schedule

```python
from datetime import timedelta
from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
    ScheduleState,
    SchedulePolicy,
    ScheduleOverlapPolicy,
)

from .workflows import DailyReportWorkflow

async def create_daily_schedule():
    client = await Client.connect("localhost:7233")
    
    await client.create_schedule(
        "daily-report",
        Schedule(
            action=ScheduleActionStartWorkflow(
                DailyReportWorkflow.run,
                {"report_type": "daily"},
                id="daily-report",
                task_queue="reports-queue",
            ),
            spec=ScheduleSpec(
                cron_expressions=["0 9 * * *"],  # Daily at 9 AM
            ),
            state=ScheduleState(
                note="Daily report generation",
            ),
            policy=SchedulePolicy(
                overlap=ScheduleOverlapPolicy.SKIP,  # Skip if previous still running
            ),
        ),
    )
    
    print("Created daily-report schedule")
```

### Interval Schedule

```python
from temporalio.client import ScheduleIntervalSpec

async def create_health_check_schedule():
    client = await Client.connect("localhost:7233")
    
    await client.create_schedule(
        "health-check",
        Schedule(
            action=ScheduleActionStartWorkflow(
                HealthCheckWorkflow.run,
                {"services": ["api", "db", "cache"]},
                id="health-check",
                task_queue="monitoring-queue",
            ),
            spec=ScheduleSpec(
                intervals=[
                    ScheduleIntervalSpec(
                        every=timedelta(minutes=5),
                        offset=timedelta(seconds=30),  # Start at :30 seconds
                    ),
                ],
            ),
        ),
    )
    
    print("Created health-check schedule (every 5 minutes)")
```

### Calendar Schedule

```python
from temporalio.client import ScheduleCalendarSpec, ScheduleRange

async def create_monthly_report_schedule():
    client = await Client.connect("localhost:7233")
    
    await client.create_schedule(
        "monthly-report",
        Schedule(
            action=ScheduleActionStartWorkflow(
                MonthlyReportWorkflow.run,
                {"report_type": "financial"},
                id="monthly-report",
                task_queue="reports-queue",
            ),
            spec=ScheduleSpec(
                calendars=[
                    ScheduleCalendarSpec(
                        # First day of every month at 9 AM
                        day_of_month=[ScheduleRange(start=1)],
                        hour=[ScheduleRange(start=9)],
                        minute=[ScheduleRange(start=0)],
                    ),
                ],
            ),
        ),
    )
    
    print("Created monthly-report schedule")
```

### Complex Schedule (Business Hours)

```python
async def create_business_hours_schedule():
    client = await Client.connect("localhost:7233")
    
    await client.create_schedule(
        "business-hours-check",
        Schedule(
            action=ScheduleActionStartWorkflow(
                BusinessCheckWorkflow.run,
                {},
                id="business-check",
                task_queue="business-queue",
            ),
            spec=ScheduleSpec(
                calendars=[
                    ScheduleCalendarSpec(
                        # Monday to Friday (1-5), hourly from 9 AM to 5 PM
                        day_of_week=[ScheduleRange(start=1, end=5)],
                        hour=[ScheduleRange(start=9, end=17)],
                        minute=[ScheduleRange(start=0)],
                    ),
                ],
            ),
            policy=SchedulePolicy(
                overlap=ScheduleOverlapPolicy.BUFFER_ONE,
                catchup_window=timedelta(hours=1),
            ),
        ),
    )
```

---

## Schedule Policies

### Overlap Policies

```python
from temporalio.client import ScheduleOverlapPolicy

# SKIP - Skip this run if previous is still running
SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP)

# BUFFER_ONE - Queue one run if previous is running
SchedulePolicy(overlap=ScheduleOverlapPolicy.BUFFER_ONE)

# BUFFER_ALL - Queue all runs (unlimited)
SchedulePolicy(overlap=ScheduleOverlapPolicy.BUFFER_ALL)

# CANCEL_OTHER - Cancel previous run, start new one
SchedulePolicy(overlap=ScheduleOverlapPolicy.CANCEL_OTHER)

# TERMINATE_OTHER - Terminate previous run, start new one
SchedulePolicy(overlap=ScheduleOverlapPolicy.TERMINATE_OTHER)

# ALLOW_ALL - Allow concurrent runs
SchedulePolicy(overlap=ScheduleOverlapPolicy.ALLOW_ALL)
```

### Catchup Policy

```python
SchedulePolicy(
    # How far back to run missed schedules
    catchup_window=timedelta(hours=1),
    
    # Pause after any workflow failure
    pause_on_failure=True,
)
```

---

## Managing Schedules

### Get Schedule Handle

```python
async def manage_schedule():
    client = await Client.connect("localhost:7233")
    
    # Get handle to existing schedule
    handle = client.get_schedule_handle("daily-report")
    
    # Describe schedule
    desc = await handle.describe()
    print(f"Schedule: {desc.id}")
    print(f"Paused: {desc.schedule.state.paused}")
    print(f"Recent actions: {desc.info.recent_actions}")
    print(f"Next scheduled: {desc.info.next_action_times}")
```

### Pause/Unpause

```python
async def pause_schedule(schedule_id: str, reason: str):
    client = await Client.connect("localhost:7233")
    handle = client.get_schedule_handle(schedule_id)
    
    await handle.pause(note=reason)
    print(f"Paused {schedule_id}: {reason}")

async def resume_schedule(schedule_id: str, reason: str):
    client = await Client.connect("localhost:7233")
    handle = client.get_schedule_handle(schedule_id)
    
    await handle.unpause(note=reason)
    print(f"Resumed {schedule_id}: {reason}")
```

### Trigger Immediately

```python
async def trigger_schedule(schedule_id: str):
    client = await Client.connect("localhost:7233")
    handle = client.get_schedule_handle(schedule_id)
    
    # Trigger immediate execution
    await handle.trigger()
    print(f"Triggered {schedule_id}")
```

### Update Schedule

```python
async def update_schedule_time(schedule_id: str, new_cron: str):
    client = await Client.connect("localhost:7233")
    handle = client.get_schedule_handle(schedule_id)
    
    # Update schedule
    await handle.update(
        lambda schedule: Schedule(
            action=schedule.action,
            spec=ScheduleSpec(
                cron_expressions=[new_cron],
            ),
            state=ScheduleState(note=f"Updated to {new_cron}"),
            policy=schedule.policy,
        )
    )
    
    print(f"Updated {schedule_id} to {new_cron}")
```

### Delete Schedule

```python
async def delete_schedule(schedule_id: str):
    client = await Client.connect("localhost:7233")
    handle = client.get_schedule_handle(schedule_id)
    
    await handle.delete()
    print(f"Deleted {schedule_id}")
```

### List All Schedules

```python
async def list_schedules():
    client = await Client.connect("localhost:7233")
    
    async for schedule in client.list_schedules():
        print(f"Schedule: {schedule.id}")
        print(f"  Workflow: {schedule.info.workflow_type}")
        print(f"  Paused: {schedule.info.paused}")
        print(f"  Running: {schedule.info.running_workflows}")
        print()
```

### Backfill Missed Runs

```python
from datetime import datetime, timezone

async def backfill_schedule(schedule_id: str, start: datetime, end: datetime):
    client = await Client.connect("localhost:7233")
    handle = client.get_schedule_handle(schedule_id)
    
    # Backfill missed executions
    await handle.backfill(
        [
            ScheduleBackfill(
                start_at=start,
                end_at=end,
                overlap=ScheduleOverlapPolicy.ALLOW_ALL,
            )
        ]
    )
    
    print(f"Backfilled {schedule_id} from {start} to {end}")
```

---

## Cron Expression Reference

### Format

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday = 0)
│ │ │ │ │
* * * * *
```

### Common Patterns

| Expression | Description |
|------------|-------------|
| `* * * * *` | Every minute |
| `0 * * * *` | Every hour (at :00) |
| `0 0 * * *` | Daily at midnight |
| `0 9 * * *` | Daily at 9 AM |
| `0 9 * * 1` | Every Monday at 9 AM |
| `0 0 * * 0` | Weekly on Sunday at midnight |
| `0 0 1 * *` | Monthly on the 1st at midnight |
| `0 0 1 1 *` | Yearly on Jan 1st at midnight |
| `0 9-17 * * 1-5` | Hourly 9 AM-5 PM, Mon-Fri |
| `*/15 * * * *` | Every 15 minutes |
| `0 */2 * * *` | Every 2 hours |
| `0 0,12 * * *` | Twice daily (midnight, noon) |
| `0 9 1,15 * *` | 1st and 15th of month at 9 AM |

### Special Characters

| Character | Meaning | Example |
|-----------|---------|---------|
| `*` | Any value | `* * * * *` (every minute) |
| `,` | List | `0,30 * * * *` (at :00 and :30) |
| `-` | Range | `9-17 * * * *` (9 AM to 5 PM) |
| `/` | Step | `*/5 * * * *` (every 5 minutes) |

---

## CLI Commands

### Create Schedule

```bash
temporal schedule create \
  --schedule-id "daily-sync" \
  --cron "0 2 * * *" \
  --workflow-id "data-sync" \
  --task-queue "sync-queue" \
  --workflow-type "DataSyncWorkflow" \
  --input '{"source": "db1", "target": "db2"}'
```

### List Schedules

```bash
temporal schedule list
```

### Describe Schedule

```bash
temporal schedule describe --schedule-id "daily-sync"
```

### Trigger Schedule

```bash
temporal schedule trigger --schedule-id "daily-sync"
```

### Pause/Unpause

```bash
# Pause
temporal schedule toggle \
  --schedule-id "daily-sync" \
  --pause \
  --reason "Maintenance"

# Unpause
temporal schedule toggle \
  --schedule-id "daily-sync" \
  --unpause \
  --reason "Maintenance complete"
```

### Update Schedule

```bash
temporal schedule update \
  --schedule-id "daily-sync" \
  --cron "0 3 * * *"  # Changed to 3 AM
```

### Delete Schedule

```bash
temporal schedule delete --schedule-id "daily-sync"
```

### Backfill

```bash
temporal schedule backfill \
  --schedule-id "daily-sync" \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-07T00:00:00Z"
```

---

## Schedule Patterns

### Daily Report at 6 AM

```python
await client.create_schedule(
    "daily-report",
    Schedule(
        action=ScheduleActionStartWorkflow(
            DailyReportWorkflow.run,
            {},
            id="daily-report",
            task_queue="reports",
        ),
        spec=ScheduleSpec(
            cron_expressions=["0 6 * * *"],
        ),
    ),
)
```

### Every 5 Minutes (Health Check)

```python
await client.create_schedule(
    "health-check",
    Schedule(
        action=ScheduleActionStartWorkflow(
            HealthCheckWorkflow.run,
            {},
            id="health-check",
            task_queue="monitoring",
        ),
        spec=ScheduleSpec(
            intervals=[
                ScheduleIntervalSpec(every=timedelta(minutes=5)),
            ],
        ),
        policy=SchedulePolicy(
            overlap=ScheduleOverlapPolicy.SKIP,
        ),
    ),
)
```

### Weekly on Monday at 9 AM

```python
await client.create_schedule(
    "weekly-review",
    Schedule(
        action=ScheduleActionStartWorkflow(
            WeeklyReviewWorkflow.run,
            {},
            id="weekly-review",
            task_queue="reviews",
        ),
        spec=ScheduleSpec(
            cron_expressions=["0 9 * * 1"],  # Monday at 9 AM
        ),
    ),
)
```

### First Day of Month

```python
await client.create_schedule(
    "monthly-billing",
    Schedule(
        action=ScheduleActionStartWorkflow(
            MonthlyBillingWorkflow.run,
            {},
            id="monthly-billing",
            task_queue="billing",
        ),
        spec=ScheduleSpec(
            calendars=[
                ScheduleCalendarSpec(
                    day_of_month=[ScheduleRange(start=1)],
                    hour=[ScheduleRange(start=0)],
                    minute=[ScheduleRange(start=0)],
                ),
            ],
        ),
    ),
)
```

### Multiple Times Per Day

```python
await client.create_schedule(
    "sync-job",
    Schedule(
        action=ScheduleActionStartWorkflow(
            SyncWorkflow.run,
            {},
            id="sync-job",
            task_queue="sync",
        ),
        spec=ScheduleSpec(
            cron_expressions=[
                "0 6 * * *",   # 6 AM
                "0 12 * * *",  # Noon
                "0 18 * * *",  # 6 PM
            ],
        ),
    ),
)
```

---

## Schedule Management Script

```python
# schedule_manager.py
import argparse
import asyncio
from temporalio.client import Client

async def main():
    parser = argparse.ArgumentParser(description="Schedule Manager")
    subparsers = parser.add_subparsers(dest="command")
    
    # List
    subparsers.add_parser("list", help="List all schedules")
    
    # Pause
    pause_parser = subparsers.add_parser("pause", help="Pause schedule")
    pause_parser.add_argument("schedule_id")
    pause_parser.add_argument("--reason", default="Manual pause")
    
    # Resume
    resume_parser = subparsers.add_parser("resume", help="Resume schedule")
    resume_parser.add_argument("schedule_id")
    resume_parser.add_argument("--reason", default="Manual resume")
    
    # Trigger
    trigger_parser = subparsers.add_parser("trigger", help="Trigger schedule")
    trigger_parser.add_argument("schedule_id")
    
    # Delete
    delete_parser = subparsers.add_parser("delete", help="Delete schedule")
    delete_parser.add_argument("schedule_id")
    
    args = parser.parse_args()
    
    client = await Client.connect("localhost:7233")
    
    if args.command == "list":
        async for schedule in client.list_schedules():
            status = "PAUSED" if schedule.info.paused else "ACTIVE"
            print(f"[{status}] {schedule.id} - {schedule.info.workflow_type}")
    
    elif args.command == "pause":
        handle = client.get_schedule_handle(args.schedule_id)
        await handle.pause(note=args.reason)
        print(f"Paused {args.schedule_id}")
    
    elif args.command == "resume":
        handle = client.get_schedule_handle(args.schedule_id)
        await handle.unpause(note=args.reason)
        print(f"Resumed {args.schedule_id}")
    
    elif args.command == "trigger":
        handle = client.get_schedule_handle(args.schedule_id)
        await handle.trigger()
        print(f"Triggered {args.schedule_id}")
    
    elif args.command == "delete":
        handle = client.get_schedule_handle(args.schedule_id)
        await handle.delete()
        print(f"Deleted {args.schedule_id}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Best Practices

1. **Use meaningful schedule IDs** - `daily-report`, `hourly-sync`, `weekly-cleanup`
2. **Set overlap policies** - Prevent concurrent runs when not needed
3. **Use catchup windows** - Recover from outages appropriately
4. **Monitor schedule health** - Check for failed runs
5. **Use pause on failure** - Prevent cascading failures
6. **Document schedules** - Use the note field
7. **Test cron expressions** - Verify they match your intent
8. **Consider timezones** - Temporal uses UTC by default

---

## Next Steps

- **temporal-signals-queries.md** - Interacting with running workflows
- **temporal-cli.md** - Complete CLI reference
- **temporal-advanced.md** - Advanced patterns
