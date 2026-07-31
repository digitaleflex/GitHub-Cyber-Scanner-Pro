# Temporal Fundamentals

> Core concepts, architecture, and durable execution model

## Overview

Temporal is a **durable execution platform** that ensures your code completes successfully regardless of failures. It provides:

- **Durability**: Workflow state survives any failure
- **Reliability**: Exactly-once execution semantics
- **Visibility**: Complete audit trail of all actions
- **Scalability**: Handle millions of concurrent workflows

---

## Core Concepts

### 1. Workflows

**Definition**: A workflow is a durable function that orchestrates activities and other workflows.

**Key Properties**:
- **Deterministic**: Same input always produces same output
- **Long-running**: Can run for seconds, hours, days, or years
- **Fault-tolerant**: Automatically resumes after failures
- **Queryable**: State can be inspected at any time

```python
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> dict:
        # This entire execution is durable
        result = await workflow.execute_activity(
            process_order,
            order_id,
            start_to_close_timeout=timedelta(minutes=5),
        )
        return result
```

### 2. Activities

**Definition**: Activities are the building blocks that perform actual work (API calls, database operations, file I/O).

**Key Properties**:
- **Non-deterministic allowed**: Can make external calls
- **Retryable**: Automatic retry with configurable policies
- **Heartbeatable**: Long-running activities report progress
- **Cancellable**: Can be cancelled gracefully

```python
from temporalio import activity
import httpx

@activity.defn
async def process_order(order_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/orders",
            json={"order_id": order_id}
        )
        return response.json()
```

### 3. Workers

**Definition**: Workers are processes that execute workflows and activities.

**Key Properties**:
- **Stateless**: Can be scaled horizontally
- **Long-polling**: Efficiently wait for tasks
- **Multi-tasking**: Handle multiple concurrent executions
- **Graceful shutdown**: Complete in-flight work before stopping

```python
from temporalio.worker import Worker
from temporalio.client import Client

async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="my-queue",
        workflows=[OrderWorkflow],
        activities=[process_order],
    )
    await worker.run()
```

### 4. Task Queues

**Definition**: Task queues are named queues that route workflow and activity tasks to workers.

**Key Properties**:
- **Named**: Workflows specify which queue to use
- **Partitioned**: Tasks distributed across workers
- **Sticky**: Workflow tasks prefer same worker for cache efficiency

```python
# Client specifies task queue when starting workflow
await client.execute_workflow(
    OrderWorkflow.run,
    "order-123",
    id="order-workflow-123",
    task_queue="order-processing-queue",  # <-- Task queue
)

# Worker polls specific task queue
worker = Worker(
    client,
    task_queue="order-processing-queue",  # <-- Same queue
    workflows=[OrderWorkflow],
    activities=[process_order],
)
```

---

## Architecture

### Temporal Server Components

```
┌─────────────────────────────────────────────────────────────────┐
│                       TEMPORAL SERVER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Frontend   │  │   History    │  │   Matching   │           │
│  │   Service    │  │   Service    │  │   Service    │           │
│  │   (gRPC)     │  │  (State)     │  │  (Queues)    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Database (PostgreSQL)                    │ │
│  │                 Stores workflow state & history             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ gRPC (Long Polling)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         WORKERS                                  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │    Worker 1     │  │    Worker 2     │  │    Worker N     │  │
│  │  - Workflows    │  │  - Workflows    │  │  - Workflows    │  │
│  │  - Activities   │  │  - Activities   │  │  - Activities   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
1. Client starts workflow
        │
        ▼
2. Frontend receives request
        │
        ▼
3. History creates workflow execution
        │
        ▼
4. Matching adds task to queue
        │
        ▼
5. Worker polls and receives task
        │
        ▼
6. Worker executes workflow code
        │
        ▼
7. Workflow schedules activities
        │
        ▼
8. Matching adds activity tasks
        │
        ▼
9. Worker executes activities
        │
        ▼
10. Results stored in history
        │
        ▼
11. Workflow continues until complete
```

---

## Durable Execution Model

### Event Sourcing

Every action in a workflow is recorded as an event:

```
Event ID │ Event Type                  │ Data
─────────┼────────────────────────────┼──────────────────
   1     │ WorkflowExecutionStarted   │ {input: {...}}
   2     │ WorkflowTaskScheduled      │ {}
   3     │ WorkflowTaskStarted        │ {worker: "w1"}
   4     │ WorkflowTaskCompleted      │ {}
   5     │ ActivityTaskScheduled      │ {activity: "process"}
   6     │ ActivityTaskStarted        │ {worker: "w1"}
   7     │ ActivityTaskCompleted      │ {result: {...}}
   8     │ WorkflowExecutionCompleted │ {result: {...}}
```

### Replay on Failure

When a worker crashes:

```
ORIGINAL EXECUTION:
┌─────────────────────────────────────────────────────────────┐
│  Step 1 ──► Step 2 ──► Step 3 ──► [CRASH] ──► ???          │
│     ✓          ✓          ✓                                 │
└─────────────────────────────────────────────────────────────┘

RECOVERY (Different Worker):
┌─────────────────────────────────────────────────────────────┐
│  Replay    Replay    Replay    Continue                     │
│  Step 1 ──► Step 2 ──► Step 3 ──► Step 4 ──► Complete      │
│  (cached)  (cached)  (cached)    (new)       (new)          │
└─────────────────────────────────────────────────────────────┘

The new worker:
1. Fetches event history from server
2. Replays workflow code (without re-executing activities)
3. Continues from exactly where it left off
4. Activities are NOT re-executed (results cached)
```

### Why Determinism Matters

```python
@workflow.defn
class BadWorkflow:
    @workflow.run
    async def run(self):
        # BAD: This breaks on replay!
        import random
        if random.random() > 0.5:
            await workflow.execute_activity(action_a, ...)
        else:
            await workflow.execute_activity(action_b, ...)
        
        # On replay, random() returns different value
        # Workflow takes different path = NON-DETERMINISM ERROR

@workflow.defn
class GoodWorkflow:
    @workflow.run
    async def run(self):
        # GOOD: Use activity for non-deterministic logic
        choice = await workflow.execute_activity(
            make_random_choice, ...
        )
        if choice == "a":
            await workflow.execute_activity(action_a, ...)
        else:
            await workflow.execute_activity(action_b, ...)
        
        # On replay, activity result is cached
        # Same path taken = DETERMINISTIC
```

---

## Workflow Identifiers

### Workflow ID

- **Unique identifier** for a workflow execution
- **Client-specified** when starting workflow
- **Deduplication key** - prevents duplicate workflows
- **Human-readable** - use meaningful IDs

```python
# Good: Meaningful, predictable IDs
await client.start_workflow(
    OrderWorkflow.run,
    order_data,
    id=f"order-{order_id}",  # order-12345
    task_queue="orders",
)

# Also good: Include timestamp for uniqueness
await client.start_workflow(
    ReportWorkflow.run,
    report_config,
    id=f"daily-report-{date.today().isoformat()}",  # daily-report-2024-01-15
    task_queue="reports",
)
```

### Run ID

- **Unique identifier** for a specific run
- **Server-generated** automatically
- **Changes** with retries, resets, continue-as-new
- **Use for** distinguishing runs of same workflow ID

```python
# Get both IDs from handle
handle = await client.start_workflow(...)
print(f"Workflow ID: {handle.id}")       # order-12345
print(f"Run ID: {handle.result_run_id}") # 8f9e3c2a-...
```

---

## Namespaces

Namespaces provide isolation:

```python
# Development namespace
dev_client = await Client.connect(
    "localhost:7233",
    namespace="development",
)

# Production namespace  
prod_client = await Client.connect(
    "temporal.example.com:7233",
    namespace="production",
)

# Workflows in different namespaces are completely isolated
```

### Common Namespace Patterns

```
production    - Live production workloads
staging       - Pre-production testing
development   - Developer testing
team-payments - Team-specific namespace
```

---

## Signals and Queries

### Signals (Write)

Signals send data TO a running workflow:

```python
@workflow.defn
class ApprovalWorkflow:
    def __init__(self):
        self._approved = None
    
    @workflow.signal
    async def approve(self, approver: str):
        self._approved = True
    
    @workflow.run
    async def run(self):
        await workflow.wait_condition(lambda: self._approved is not None)
        return {"approved": self._approved}

# Send signal from client
handle = client.get_workflow_handle("approval-123")
await handle.signal(ApprovalWorkflow.approve, "manager@example.com")
```

### Queries (Read)

Queries read state FROM a running workflow:

```python
@workflow.defn
class ProgressWorkflow:
    def __init__(self):
        self._progress = 0
    
    @workflow.query
    def get_progress(self) -> int:
        return self._progress
    
    @workflow.run
    async def run(self):
        for i in range(100):
            self._progress = i
            await workflow.execute_activity(...)

# Query from client (synchronous, doesn't affect workflow)
handle = client.get_workflow_handle("progress-123")
progress = await handle.query(ProgressWorkflow.get_progress)
print(f"Progress: {progress}%")
```

---

## Error Handling

### Activity Errors

```python
from temporalio.exceptions import ActivityError, ApplicationError

@workflow.defn
class RobustWorkflow:
    @workflow.run
    async def run(self):
        try:
            await workflow.execute_activity(
                risky_activity,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
        except ActivityError as e:
            # Activity failed after all retries
            workflow.logger.error(f"Activity failed: {e}")
            
            # Check specific error type
            if e.cause and isinstance(e.cause, ApplicationError):
                if e.cause.type == "InsufficientFundsError":
                    # Handle specific case
                    return {"status": "insufficient_funds"}
            
            # Re-raise or handle
            raise
```

### Workflow-Level Errors

```python
from temporalio.exceptions import ApplicationError

@activity.defn
async def validate_input(data: dict):
    if not data.get("required_field"):
        # Non-retryable error
        raise ApplicationError(
            "Missing required field",
            type="ValidationError",
            non_retryable=True,  # Don't retry this
        )
```

---

## Timeouts Summary

| Timeout | Description | Typical Value |
|---------|-------------|---------------|
| `start_to_close_timeout` | Max time from activity start to completion | 5-30 min |
| `schedule_to_close_timeout` | Max time from schedule to completion (includes queue) | 10-60 min |
| `schedule_to_start_timeout` | Max time waiting in queue | 1-5 min |
| `heartbeat_timeout` | Max time between heartbeats | 30-60 sec |
| `execution_timeout` | Max workflow execution time | Hours/days |
| `run_timeout` | Max single run time (before continue-as-new) | 1 hour |

---

## Next Steps

- **temporal-activities.md** - Deep dive into activity patterns
- **temporal-workflows.md** - Workflow patterns and best practices
- **temporal-workers.md** - Worker configuration and deployment
