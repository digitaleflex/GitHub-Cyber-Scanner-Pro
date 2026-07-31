---
description: Expert Temporal workflow specialist for creating, running, scheduling, monitoring, and debugging durable workflows using Python and uv. Covers activities, workers, signals, queries, sagas, child workflows, testing, and production deployment patterns.
name: temporal
---

# Temporal: Durable Workflow Orchestration Framework

> **Expert AI Agent for Temporal Workflows**  
> Create, run, schedule, monitor, and debug fault-tolerant distributed workflows using Python and the Temporal SDK.

## What I Do

I am an expert Temporal workflow architect and developer. I help you build reliable, scalable, and fault-tolerant distributed applications using Temporal's durable execution platform.

**Temporal guarantees your workflows complete successfully, even through:**
- Network partitions and timeouts
- Server crashes and restarts
- Process failures and OOM kills
- Long-running operations (hours/days/weeks)

## Core Capabilities

| Capability | Description |
|------------|-------------|
| **Create** | Design and implement workflows, activities, workers, and clients |
| **Run** | Execute workflows locally or against Temporal server/cloud |
| **Schedule** | Set up cron, interval, and calendar-based workflow schedules |
| **Monitor** | Check workflow status, query state, read event history |
| **Debug** | Troubleshoot failed workflows, replay events, analyze errors |
| **Optimize** | Apply retry policies, timeouts, and production best practices |

## When to Use Me

Use this skill when you need to:

- Build reliable multi-step business processes
- Orchestrate microservices with guaranteed delivery
- Create long-running workflows that survive failures
- Implement saga patterns with compensation/rollback
- Build human-in-the-loop approval workflows
- Schedule recurring tasks with complex timing
- Process queues with exactly-once semantics
- Coordinate parallel and sequential activities
- Build self-healing automation systems

## Workflow Complexity Levels

| Level | Characteristics | Examples |
|-------|-----------------|----------|
| **Simple** | Single activity, basic input/output | Send email, call API |
| **Intermediate** | Multiple activities, retries, error handling | Order processing, data pipeline |
| **Advanced** | Signals, queries, timers, human-in-the-loop | Approval workflows, monitoring |
| **Complex** | Child workflows, saga patterns, continue-as-new | Multi-agent orchestration, long-running processes |

---

## Core Stack

### Required Dependencies

```bash
# Initialize project with uv
uv init temporal-project
cd temporal-project

# Core dependencies
uv add temporalio

# Recommended additions
uv add temporalio[opentelemetry]  # Observability
uv add pydantic                    # Data validation
uv add pydantic-settings           # Configuration
uv add structlog                   # Structured logging
uv add httpx                       # Async HTTP for activities
```

### Temporal Server Options

```bash
# Option 1: Temporal CLI (Development - Recommended)
brew install temporal  # macOS
# or
curl -sSf https://temporal.download/cli.sh | sh

# Start development server (SQLite, in-memory)
temporal server start-dev

# Start with UI on custom port
temporal server start-dev --ui-port 8080

# Option 2: Temporal CLI with MySQL (Production-like)
temporal server start-dev \
  --db-filename /path/to/temporal.db \
  --namespace default

# Option 3: Temporal Cloud (Production)
export TEMPORAL_ADDRESS="namespace.account.tmprl.cloud:7233"
export TEMPORAL_NAMESPACE="your-namespace"
export TEMPORAL_TLS_CERT="/path/to/client.pem"
export TEMPORAL_TLS_KEY="/path/to/client.key"
```

---

## Project Structure Templates

### Simple Project
```
temporal-project/
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── activities.py      # Activity definitions
│   ├── workflows.py       # Workflow definitions
│   ├── worker.py          # Worker process
│   └── client.py          # Client to start workflows
└── README.md
```

### Production Project
```
temporal-project/
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── config.py              # Pydantic settings
│   ├── client.py              # CLI client
│   ├── worker.py              # Worker entry point
│   ├── activities/
│   │   ├── __init__.py
│   │   ├── email.py
│   │   ├── payment.py
│   │   └── notification.py
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── order.py
│   │   ├── approval.py
│   │   └── saga.py
│   └── models/
│       ├── __init__.py
│       └── schemas.py         # Pydantic models
├── tests/
│   ├── __init__.py
│   ├── test_activities.py
│   └── test_workflows.py
├── scripts/
│   ├── start_worker.sh
│   └── create_schedules.sh
└── README.md
```

---

## Quick Start Examples

### Minimal Activity + Workflow

```python
# activities.py
from temporalio import activity
from dataclasses import dataclass

@dataclass
class GreetingInput:
    name: str

@activity.defn
async def greet(input: GreetingInput) -> str:
    return f"Hello, {input.name}!"
```

```python
# workflows.py
from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import greet, GreetingInput

@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            greet,
            GreetingInput(name=name),
            start_to_close_timeout=timedelta(seconds=30),
        )
```

```python
# worker.py
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from .activities import greet
from .workflows import GreetingWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="greeting-queue",
        workflows=[GreetingWorkflow],
        activities=[greet],
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

```python
# client.py
import asyncio
from temporalio.client import Client
from .workflows import GreetingWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    result = await client.execute_workflow(
        GreetingWorkflow.run,
        "World",
        id="greeting-workflow",
        task_queue="greeting-queue",
    )
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Run It

```bash
# Terminal 1: Start Temporal
temporal server start-dev

# Terminal 2: Start Worker
uv run python -m src.worker

# Terminal 3: Execute Workflow
uv run python -m src.client
# Output: Result: Hello, World!
```

---

## Determinism Rules (Critical!)

Workflows MUST be deterministic. The same inputs must always produce the same outputs.

### DO NOT Use in Workflows

```python
# BAD - These break determinism
import random
random.randint(1, 100)  # Non-deterministic

import datetime
datetime.datetime.now()  # Non-deterministic

import uuid
uuid.uuid4()  # Non-deterministic

import os
os.environ.get("MY_VAR")  # Can change between replays

import requests
requests.get("https://api.example.com")  # Side effect
```

### DO Use These Alternatives

```python
# GOOD - Deterministic alternatives

# For current time
current_time = workflow.now()

# For UUIDs
workflow_uuid = workflow.uuid4()

# For random values, API calls, env vars - use activities
result = await workflow.execute_activity(
    generate_random,
    start_to_close_timeout=timedelta(seconds=5),
)

# For environment variables - pass as workflow input
@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, config: dict) -> dict:
        api_key = config["api_key"]  # Passed as input
```

### Safe Imports

```python
# Use unsafe.imports_passed_through for non-workflow code
with workflow.unsafe.imports_passed_through():
    from .activities import my_activity
    from .models import MyModel
```

---

## Module Reference

### Core Modules
- **temporal-fundamentals.md** - Core concepts, architecture, durable execution
- **temporal-activities.md** - Activity patterns, async, heartbeating, retries
- **temporal-workflows.md** - Workflow patterns from simple to complex
- **temporal-workers.md** - Worker setup, configuration, deployment patterns

### Advanced Modules
- **temporal-signals-queries.md** - Signals, queries, updates, human-in-the-loop patterns
- **temporal-scheduling.md** - Cron, interval, calendar schedules
- **temporal-advanced.md** - Saga pattern, child workflows, continue-as-new, versioning
- **temporal-cli.md** - CLI commands reference
- **temporal-testing.md** - Unit and integration testing with mocking and time-skipping

### Enterprise Modules
- **temporal-security.md** - mTLS, payload encryption, RBAC, secrets management
- **temporal-operations.md** - Backup/restore, MySQL maintenance, health monitoring
- **temporal-cloud.md** - Temporal Cloud connection, namespaces, metrics, migration
- **temporal-performance.md** - Tuning, benchmarking, capacity planning

---

## Common Patterns Quick Reference

### Retry Policies

```python
from temporalio.common import RetryPolicy
from datetime import timedelta

# Conservative retry
conservative = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=1),
    maximum_attempts=3,
)

# Aggressive retry for transient failures
aggressive = RetryPolicy(
    initial_interval=timedelta(milliseconds=100),
    maximum_interval=timedelta(seconds=10),
    maximum_attempts=10,
)

# Unlimited retry for critical operations
unlimited = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=0,  # 0 = unlimited
)

# Skip certain error types
smart = RetryPolicy(
    maximum_attempts=5,
    non_retryable_error_types=["ValueError", "AuthenticationError"],
)
```

### Timeout Configuration

```python
await workflow.execute_activity(
    my_activity,
    input_data,
    # Total time from schedule to completion
    schedule_to_close_timeout=timedelta(minutes=10),
    # Time from start to completion (excludes queue time)
    start_to_close_timeout=timedelta(minutes=5),
    # Time to wait for worker to pick up
    schedule_to_start_timeout=timedelta(minutes=1),
    # Heartbeat timeout for long-running activities
    heartbeat_timeout=timedelta(seconds=30),
)
```

### Signal and Query Patterns

```python
@workflow.defn
class ApprovalWorkflow:
    def __init__(self):
        self._approved = None
        self._status = "pending"
    
    @workflow.run
    async def run(self, request: dict) -> dict:
        await workflow.wait_condition(lambda: self._approved is not None)
        return {"approved": self._approved, "status": self._status}
    
    @workflow.signal
    async def approve(self, approver: str):
        self._approved = True
        self._status = f"approved by {approver}"
    
    @workflow.signal
    async def reject(self, reason: str):
        self._approved = False
        self._status = f"rejected: {reason}"
    
    @workflow.query
    def get_status(self) -> str:
        return self._status
```

---

## CLI Quick Reference

```bash
# Server
temporal server start-dev

# Workflows
temporal workflow list
temporal workflow describe --workflow-id ID
temporal workflow show --workflow-id ID
temporal workflow signal --workflow-id ID --signal-name NAME --input '{}'
temporal workflow query --workflow-id ID --query-type get_status
temporal workflow cancel --workflow-id ID
temporal workflow terminate --workflow-id ID --reason "reason"

# Schedules
temporal schedule list
temporal schedule create --schedule-id ID --cron "0 9 * * *" \
  --workflow-id WF_ID --task-queue QUEUE --workflow-type TYPE
temporal schedule trigger --schedule-id ID
temporal schedule toggle --schedule-id ID --pause
temporal schedule delete --schedule-id ID

# Task Queues
temporal task-queue describe --task-queue QUEUE
```

---

## Best Practices Summary

1. **Always use `uv`** for Python package management (never pip)
2. **Workflows must be deterministic** - no random, datetime.now, external calls
3. **Use activities for side effects** - API calls, database, file I/O
4. **Configure retry policies** - match your error patterns
5. **Set appropriate timeouts** - start_to_close_timeout at minimum
6. **Use heartbeats** for long-running activities
7. **Implement graceful shutdown** - handle SIGTERM properly
8. **Use structured logging** - structlog for observability
9. **Test workflows** - use Temporal's testing utilities
10. **Store secrets securely** - never in workflow/activity code

---

## Installation Quick Start

```bash
# Create project
mkdir temporal-project && cd temporal-project
uv init

# Add dependencies
uv add temporalio pydantic structlog httpx

# Start Temporal
temporal server start-dev

# Create your first workflow
# See templates above

# Run worker
uv run python -m src.worker
```

---

**Next Module:** See **temporal-fundamentals.md** for core concepts and architecture.
