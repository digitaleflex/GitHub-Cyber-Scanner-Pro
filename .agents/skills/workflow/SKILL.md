---
description: Create, run, schedule, monitor, and debug Temporal workflows using Python and uv. Expert in activities, workers, signals, queries, saga patterns, child workflows, retry policies, and CLI operations.
name: workflow
---

# Temporal Workflow Skill

You are an expert Temporal workflow specialist. Your role is to help users create, run, schedule, monitor, and debug Temporal workflows using Python and the `uv` package manager.

## When to Use This Skill

- User asks to create a workflow, activity, or worker
- User mentions Temporal, workflow orchestration, or distributed tasks
- User needs to schedule recurring jobs or cron-based workflows
- User wants to implement saga patterns, human-in-the-loop approvals, or multi-step processes
- User asks about signals, queries, or workflow state management
- User needs help debugging failed workflows or understanding event history

## Core Capabilities

| Capability | Description |
|------------|-------------|
| **Create** | Design and implement workflows, activities, workers, and clients |
| **Run** | Execute workflows locally or against a Temporal server |
| **Schedule** | Set up cron, interval, and calendar-based workflow schedules |
| **Monitor** | Check workflow status, query state, read event history |
| **Debug** | Troubleshoot failed workflows, replay events, analyze errors |
| **Optimize** | Apply retry policies, timeouts, and best practices |

## Environment Setup

### Package Manager: uv
Always use `uv` for Python package management.

```bash
# Initialize a new project
uv init temporal-workflows
cd temporal-workflows

# Add core dependencies
uv add temporalio
uv add temporalio[opentelemetry]  # For observability
uv add pydantic                    # For data validation
uv add httpx                       # For async HTTP calls
```

### Temporal Server Setup

```bash
# Option 1: Temporal CLI (Development)
temporal server start-dev

# Option 2: Docker Compose
git clone https://github.com/temporalio/docker-compose.git
cd docker-compose && docker-compose up -d

# Option 3: Temporal Cloud (Production)
export TEMPORAL_ADDRESS="<namespace>.<account>.tmprl.cloud:7233"
export TEMPORAL_NAMESPACE="<namespace>"
export TEMPORAL_TLS_CERT="/path/to/client.pem"
export TEMPORAL_TLS_KEY="/path/to/client.key"
```

## Project Structure

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
│   ├── activities/
│   │   ├── __init__.py
│   │   ├── email.py
│   │   └── payment.py
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── order.py
│   │   └── saga.py
│   ├── models/
│   │   └── schemas.py     # Pydantic models
│   ├── worker.py
│   ├── client.py
│   └── config.py
├── tests/
└── README.md
```

## Code Templates

### Activity Definition
```python
from temporalio import activity
from dataclasses import dataclass

@dataclass
class EmailInput:
    to: str
    subject: str
    body: str

@dataclass
class EmailResult:
    message_id: str
    sent_at: str

@activity.defn
def send_email(input: EmailInput) -> EmailResult:
    """Synchronous activity for sending emails."""
    activity.logger.info(f"Sending email to {input.to}")
    return EmailResult(message_id="msg-12345", sent_at="2024-01-01T00:00:00Z")

@activity.defn
async def call_api(url: str) -> dict:
    """Async activity for API calls."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### Simple Workflow
```python
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import send_email, EmailInput

@workflow.defn
class SendEmailWorkflow:
    @workflow.run
    async def run(self, email_input: EmailInput) -> dict:
        return await workflow.execute_activity(
            send_email,
            email_input,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
```

### Workflow with Signals and Queries
```python
from datetime import timedelta
from temporalio import workflow
from typing import Optional
import asyncio

@workflow.defn
class ApprovalWorkflow:
    def __init__(self):
        self._approved: Optional[bool] = None
        self._status = "pending"
    
    @workflow.run
    async def run(self, request: dict) -> dict:
        # Wait for approval signal (timeout after 7 days)
        try:
            await asyncio.wait_for(
                workflow.wait_condition(lambda: self._approved is not None),
                timeout=timedelta(days=7).total_seconds()
            )
        except asyncio.TimeoutError:
            return {"status": "expired"}
        
        return {"status": "approved" if self._approved else "rejected"}
    
    @workflow.signal
    async def approve(self):
        self._approved = True
        self._status = "approved"
    
    @workflow.signal
    async def reject(self):
        self._approved = False
        self._status = "rejected"
    
    @workflow.query
    def get_status(self) -> str:
        return self._status
```

### Saga Pattern
```python
from temporalio import workflow
from temporalio.exceptions import ActivityError

@workflow.defn
class OrderSagaWorkflow:
    @workflow.run
    async def run(self, order: dict) -> dict:
        try:
            # Step 1: Reserve inventory
            reservation = await workflow.execute_activity(
                reserve_inventory, order,
                start_to_close_timeout=timedelta(minutes=2),
            )
            
            # Step 2: Charge payment
            payment = await workflow.execute_activity(
                charge_payment, order,
                start_to_close_timeout=timedelta(minutes=2),
            )
            
            # Step 3: Create shipment
            shipment = await workflow.execute_activity(
                create_shipment, order,
                start_to_close_timeout=timedelta(minutes=2),
            )
            
            return {"status": "success", "tracking": shipment["tracking_id"]}
            
        except ActivityError as e:
            # Compensate in reverse order
            await self._compensate(order)
            return {"status": "failed", "error": str(e)}
    
    async def _compensate(self, order: dict):
        # Release inventory, refund payment, cancel shipment
        pass
```

### Worker Setup
```python
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from .activities import send_email, call_api
from .workflows import SendEmailWorkflow, ApprovalWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    
    worker = Worker(
        client,
        task_queue="my-task-queue",
        workflows=[SendEmailWorkflow, ApprovalWorkflow],
        activities=[send_email, call_api],
    )
    
    print("Starting worker on task queue 'my-task-queue'")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Client Code
```python
import asyncio
from temporalio.client import Client
from uuid import uuid4

async def start_workflow():
    client = await Client.connect("localhost:7233")
    
    # Execute and wait for result
    result = await client.execute_workflow(
        SendEmailWorkflow.run,
        EmailInput(to="user@example.com", subject="Hello", body="Test"),
        id=f"send-email-{uuid4()}",
        task_queue="my-task-queue",
    )
    print(f"Result: {result}")

async def interact_with_workflow():
    client = await Client.connect("localhost:7233")
    
    # Get existing workflow handle
    handle = client.get_workflow_handle("approval-123")
    
    # Query status
    status = await handle.query(ApprovalWorkflow.get_status)
    print(f"Status: {status}")
    
    # Send signal
    await handle.signal(ApprovalWorkflow.approve)
    
    # Wait for result
    result = await handle.result()
    print(f"Result: {result}")
```

## Scheduling

### Create Schedule via Python
```python
from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
    ScheduleIntervalSpec,
    SchedulePolicy,
    ScheduleOverlapPolicy,
)
from datetime import timedelta

await client.create_schedule(
    "daily-cleanup",
    Schedule(
        action=ScheduleActionStartWorkflow(
            CleanupWorkflow.run,
            {},
            id="cleanup",
            task_queue="maintenance-queue",
        ),
        spec=ScheduleSpec(
            cron_expressions=["0 2 * * *"],  # Daily at 2 AM
        ),
        policy=SchedulePolicy(
            overlap=ScheduleOverlapPolicy.SKIP,
        ),
    ),
)
```

### Cron Expression Reference
| Expression | Description |
|------------|-------------|
| `* * * * *` | Every minute |
| `0 * * * *` | Every hour |
| `0 0 * * *` | Daily at midnight |
| `0 2 * * *` | Daily at 2 AM |
| `0 0 * * 0` | Weekly on Sunday |
| `0 0 1 * *` | Monthly on the 1st |
| `*/15 * * * *` | Every 15 minutes |
| `0 9-17 * * 1-5` | Hourly, 9 AM-5 PM, Mon-Fri |

## Determinism Rules

**Workflows MUST be deterministic.** Never use in workflows:
- `random.randint()` - Use activity instead
- `datetime.now()` - Use `workflow.now()`
- `uuid.uuid4()` - Use `workflow.uuid4()`
- `os.environ.get()` - Pass as workflow input
- Direct API calls - Use activities

```python
# GOOD - Deterministic
current_time = workflow.now()
workflow_uuid = workflow.uuid4()

# Import non-workflow code safely
with workflow.unsafe.imports_passed_through():
    from .activities import my_activity
```

## Retry Policies

```python
from temporalio.common import RetryPolicy
from datetime import timedelta

# Conservative retry
retry = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=1),
    maximum_attempts=3,
    non_retryable_error_types=["ValueError", "AuthenticationError"],
)

# Unlimited retry for critical operations
unlimited = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=0,  # 0 = unlimited
)
```

## Timeout Configuration

```python
await workflow.execute_activity(
    my_activity,
    input_data,
    schedule_to_close_timeout=timedelta(minutes=10),  # Total time
    start_to_close_timeout=timedelta(minutes=5),       # Execution time
    schedule_to_start_timeout=timedelta(minutes=1),    # Queue time
    heartbeat_timeout=timedelta(seconds=30),           # For long-running
)
```

## CLI Commands

### Workflow Operations
```bash
# Start workflow
temporal workflow start \
  --workflow-id "my-workflow" \
  --task-queue "my-queue" \
  --type "MyWorkflow" \
  --input '{"key": "value"}'

# List workflows
temporal workflow list
temporal workflow list --query "ExecutionStatus='Running'"

# Describe workflow
temporal workflow describe --workflow-id "my-workflow"

# Show history
temporal workflow show --workflow-id "my-workflow"

# Query workflow
temporal workflow query \
  --workflow-id "my-workflow" \
  --query-type "get_status"

# Signal workflow
temporal workflow signal \
  --workflow-id "my-workflow" \
  --signal-name "approve" \
  --input '{"approver": "admin"}'

# Cancel/terminate
temporal workflow cancel --workflow-id "my-workflow"
temporal workflow terminate --workflow-id "my-workflow" --reason "Manual"
```

### Schedule Operations
```bash
# Create schedule
temporal schedule create \
  --schedule-id "daily-job" \
  --cron "0 9 * * *" \
  --workflow-id "scheduled-workflow" \
  --task-queue "my-queue" \
  --workflow-type "DailyWorkflow"

# List/describe
temporal schedule list
temporal schedule describe --schedule-id "daily-job"

# Trigger immediately
temporal schedule trigger --schedule-id "daily-job"

# Pause/unpause
temporal schedule toggle --schedule-id "daily-job" --pause
temporal schedule toggle --schedule-id "daily-job" --unpause

# Delete
temporal schedule delete --schedule-id "daily-job"
```

### Server Operations
```bash
# Start development server
temporal server start-dev
temporal server start-dev --namespace custom-ns --port 7233

# Check health
temporal operator cluster health

# Describe task queue
temporal task-queue describe --task-queue "my-queue"
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `WorkflowNotFoundError` | Workflow ID doesn't exist | Check ID spelling and namespace |
| `Non-determinism detected` | Using random/datetime | Use `workflow.uuid4()` and `workflow.now()` |
| `Activity timeout` | Activity too slow | Increase timeout or add heartbeating |
| `Worker not picking up tasks` | Wrong task queue | Verify task queue name matches |
| `Connection refused` | Server not running | Start Temporal server |

### Debug Commands
```bash
# Check server health
temporal operator cluster health

# Check worker pollers
temporal task-queue describe --task-queue "my-queue"

# Get workflow stack trace
temporal workflow stack --workflow-id "my-workflow"

# View detailed history
temporal workflow show --workflow-id "my-workflow" --output json | jq
```

## Quick Reference

```
WORKFLOW LIFECYCLE
  Start:    client.start_workflow(Workflow.run, input, id=...)
  Execute:  client.execute_workflow(Workflow.run, input, id=...)
  Signal:   handle.signal(signal_name, args)
  Query:    handle.query(query_name)
  Cancel:   handle.cancel()
  Result:   handle.result()

ACTIVITY EXECUTION
  await workflow.execute_activity(
      activity_fn,
      args,
      start_to_close_timeout=timedelta(seconds=30),
      retry_policy=RetryPolicy(maximum_attempts=3),
  )

DETERMINISM SAFE
  Time:     workflow.now()
  UUID:     workflow.uuid4()
  Sleep:    await asyncio.sleep(seconds)

CLI ESSENTIALS
  temporal workflow list
  temporal workflow describe --workflow-id ID
  temporal workflow show --workflow-id ID
  temporal workflow signal --workflow-id ID --signal-name NAME
  temporal schedule create --schedule-id ID --cron "0 * * * *"
```

---

**Remember:** Always start with the simplest solution and add complexity only when needed. Temporal handles reliability - focus on your business logic.
