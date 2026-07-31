# Temporal Workflow Orchestration Skill

> **Build reliable, fault-tolerant distributed applications with Temporal and Python**

## Quick Start

```bash
# 1. Create project
mkdir my-temporal-project && cd my-temporal-project
uv init
uv add temporalio

# 2. Start Temporal server
temporal server start-dev

# 3. Create your first workflow (see examples below)

# 4. Run worker
uv run python -m src.worker

# 5. Execute workflow
uv run python -m src.client
```

---

## Module Reference

### Core Modules
| Module | Description |
|--------|-------------|
| **SKILL.md** | Main skill definition, core concepts, quick reference |
| **temporal-fundamentals.md** | Core concepts, architecture, durable execution model |
| **temporal-activities.md** | Activity patterns, async, heartbeating, retries |
| **temporal-workflows.md** | Workflow patterns from simple to complex |
| **temporal-workers.md** | Worker setup, configuration, deployment patterns |

### Advanced Modules
| Module | Description |
|--------|-------------|
| **temporal-scheduling.md** | Cron, interval, calendar schedules |
| **temporal-cli.md** | CLI commands reference |
| **temporal-signals-queries.md** | Signals, queries, updates, human-in-the-loop |
| **temporal-advanced.md** | Saga pattern, child workflows, continue-as-new |
| **temporal-testing.md** | Unit and integration testing patterns |

### Enterprise Modules
| Module | Description |
|--------|-------------|
| **temporal-security.md** | mTLS, payload encryption, RBAC, secrets management |
| **temporal-operations.md** | Backup/restore, MySQL maintenance, health monitoring |
| **temporal-cloud.md** | Temporal Cloud connection, namespaces, metrics |
| **temporal-performance.md** | Tuning, benchmarking, capacity planning |

---

## Minimal Example

### Activity

```python
# src/activities.py
from temporalio import activity
from dataclasses import dataclass

@dataclass
class GreetingInput:
    name: str

@activity.defn
async def greet(input: GreetingInput) -> str:
    return f"Hello, {input.name}!"
```

### Workflow

```python
# src/workflows.py
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

### Worker

```python
# src/worker.py
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

### Client

```python
# src/client.py
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

---

## Common Patterns

### Retry Policy

```python
from temporalio.common import RetryPolicy
from datetime import timedelta

retry = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=1),
    maximum_attempts=5,
)

await workflow.execute_activity(
    my_activity,
    args,
    start_to_close_timeout=timedelta(minutes=5),
    retry_policy=retry,
)
```

### Signal and Query

```python
@workflow.defn
class ApprovalWorkflow:
    def __init__(self):
        self._approved = None
    
    @workflow.run
    async def run(self, request: dict) -> dict:
        await workflow.wait_condition(lambda: self._approved is not None)
        return {"approved": self._approved}
    
    @workflow.signal
    async def approve(self):
        self._approved = True
    
    @workflow.query
    def get_status(self) -> str:
        return "approved" if self._approved else "pending"
```

### Schedule

```python
# CLI
temporal schedule create \
  --schedule-id "daily-job" \
  --cron "0 9 * * *" \
  --workflow-id "daily-workflow" \
  --task-queue "my-queue" \
  --workflow-type "DailyWorkflow"
```

---

## CLI Quick Reference

```bash
# Server
temporal server start-dev

# Workflows
temporal workflow list
temporal workflow describe --workflow-id ID
temporal workflow signal --workflow-id ID --signal-name approve
temporal workflow query --workflow-id ID --query-type get_status
temporal workflow cancel --workflow-id ID

# Schedules
temporal schedule list
temporal schedule trigger --schedule-id ID
temporal schedule toggle --schedule-id ID --pause

# Debug
temporal workflow show --workflow-id ID
temporal workflow stack --workflow-id ID
```

---

## Project Structure

```
temporal-project/
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── activities.py      # Activity definitions
│   ├── workflows.py       # Workflow definitions
│   ├── worker.py          # Worker process
│   └── client.py          # Client to start workflows
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_activities.py
│   └── test_workflows.py
└── README.md
```

---

## Critical Rules

1. **Always use `uv`** for Python package management (never pip)
2. **Workflows must be deterministic** - no random, datetime.now(), external calls
3. **Use activities for side effects** - API calls, database, file I/O
4. **Use `workflow.now()`** instead of `datetime.now()`
5. **Use `workflow.uuid4()`** instead of `uuid.uuid4()`
6. **Set timeouts** - at minimum `start_to_close_timeout`

---

## Dependencies

```bash
# Core
uv add temporalio

# Recommended
uv add temporalio[opentelemetry]  # Observability
uv add pydantic pydantic-settings  # Data validation
uv add structlog                    # Structured logging
uv add httpx                        # Async HTTP

# Testing
uv add --dev pytest pytest-asyncio
```

---

## Links

- [Temporal Documentation](https://docs.temporal.io/)
- [Temporal Python SDK](https://github.com/temporalio/sdk-python)
- [Temporal Cloud](https://temporal.io/cloud)

---

**Version:** 1.0  
**Stack:** temporalio + python + uv + temporal-cli
