# Temporal Activities

> Activity patterns, async execution, heartbeating, and retry policies

## Overview

Activities are the building blocks of Temporal workflows. They perform the actual work: API calls, database operations, file I/O, and any external interactions.

**Key Principle**: Activities can be non-deterministic. All side effects should happen in activities, not workflows.

---

## Activity Basics

### Synchronous Activity

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
    """Synchronous activity - runs in thread pool."""
    import smtplib
    from datetime import datetime
    
    # Actual email sending logic
    activity.logger.info(f"Sending email to {input.to}")
    
    return EmailResult(
        message_id="msg-12345",
        sent_at=datetime.utcnow().isoformat()
    )
```

### Asynchronous Activity

```python
from temporalio import activity
import httpx
from dataclasses import dataclass
from typing import Optional

@dataclass
class APICallInput:
    url: str
    method: str = "GET"
    payload: Optional[dict] = None
    headers: Optional[dict] = None

@dataclass
class APICallResult:
    status_code: int
    body: dict
    elapsed_ms: float

@activity.defn
async def call_api(input: APICallInput) -> APICallResult:
    """Async activity - preferred for I/O operations."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        activity.logger.info(f"Calling {input.method} {input.url}")
        
        response = await client.request(
            method=input.method,
            url=input.url,
            json=input.payload,
            headers=input.headers or {}
        )
        
        return APICallResult(
            status_code=response.status_code,
            body=response.json() if response.content else {},
            elapsed_ms=response.elapsed.total_seconds() * 1000
        )
```

---

## Heartbeating

For long-running activities, heartbeats:
- Signal the activity is still alive
- Enable cancellation detection
- Store progress for resumption

### Basic Heartbeat

```python
@activity.defn
async def process_large_file(file_path: str) -> dict:
    """Long-running activity with heartbeating."""
    import asyncio
    
    total_size = 100_000_000  # 100MB
    processed = 0
    chunk_size = 1_000_000   # 1MB
    
    while processed < total_size:
        # Heartbeat with progress info
        activity.heartbeat(f"Processed {processed}/{total_size} bytes")
        
        # Simulate processing
        await asyncio.sleep(0.1)
        processed += chunk_size
        
        activity.logger.info(f"Progress: {processed/total_size*100:.1f}%")
    
    return {"processed_bytes": processed}
```

### Heartbeat with Details (Resumable)

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProcessingState:
    last_processed_id: int
    items_completed: int
    checkpoint_data: dict

@activity.defn
async def resumable_batch_process(batch_id: str) -> dict:
    """Activity that can resume from last checkpoint."""
    
    # Check for previous heartbeat details
    heartbeat_details = activity.info().heartbeat_details
    
    if heartbeat_details:
        # Resume from checkpoint
        state = ProcessingState(**heartbeat_details[0])
        start_id = state.last_processed_id
        activity.logger.info(f"Resuming from item {start_id}")
    else:
        # Fresh start
        start_id = 0
    
    items = await fetch_items(batch_id, start_from=start_id)
    
    for i, item in enumerate(items):
        # Process item
        await process_item(item)
        
        # Heartbeat with checkpoint
        state = ProcessingState(
            last_processed_id=item.id,
            items_completed=i + 1,
            checkpoint_data={"batch_id": batch_id}
        )
        activity.heartbeat(state.__dict__)
    
    return {"total_processed": len(items)}
```

---

## Retry Policies

### Retry Policy Options

```python
from temporalio.common import RetryPolicy
from datetime import timedelta

# Full configuration
retry_policy = RetryPolicy(
    # Initial wait before first retry
    initial_interval=timedelta(seconds=1),
    
    # Multiplier for subsequent retries
    backoff_coefficient=2.0,
    
    # Maximum wait between retries
    maximum_interval=timedelta(minutes=1),
    
    # Maximum retry attempts (0 = unlimited)
    maximum_attempts=5,
    
    # Error types that should NOT be retried
    non_retryable_error_types=[
        "ValueError",
        "AuthenticationError",
        "PermissionDeniedError",
    ],
)
```

### Common Retry Patterns

```python
# Conservative - for idempotent operations
conservative = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=1),
    maximum_attempts=3,
)

# Aggressive - for transient failures (network blips)
aggressive = RetryPolicy(
    initial_interval=timedelta(milliseconds=100),
    backoff_coefficient=1.5,
    maximum_interval=timedelta(seconds=10),
    maximum_attempts=10,
)

# Unlimited - for critical operations that must succeed
unlimited = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=0,  # 0 = unlimited
)

# Quick fail - for validation
quick_fail = RetryPolicy(
    maximum_attempts=1,  # No retries
)
```

### Using Retry Policy in Workflow

```python
@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, order: dict) -> dict:
        # Critical payment - unlimited retries
        payment = await workflow.execute_activity(
            process_payment,
            order,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=0,
                maximum_interval=timedelta(minutes=2),
            ),
        )
        
        # Notification - best effort, limited retries
        await workflow.execute_activity(
            send_notification,
            order,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        
        return payment
```

---

## Activity Timeouts

### Timeout Types

```python
await workflow.execute_activity(
    my_activity,
    input_data,
    
    # Time from activity start to completion
    # REQUIRED - at least one timeout must be set
    start_to_close_timeout=timedelta(minutes=5),
    
    # Time from scheduling to completion (includes queue time)
    schedule_to_close_timeout=timedelta(minutes=10),
    
    # Time to wait in queue before starting
    schedule_to_start_timeout=timedelta(minutes=2),
    
    # Time between heartbeats (for long-running activities)
    heartbeat_timeout=timedelta(seconds=30),
)
```

### Timeout Selection Guide

| Scenario | Recommended Timeouts |
|----------|---------------------|
| Quick API call | `start_to_close=30s` |
| Database query | `start_to_close=1m` |
| File processing | `start_to_close=10m, heartbeat=30s` |
| External service call | `start_to_close=5m, schedule_to_close=15m` |
| Long batch job | `start_to_close=1h, heartbeat=1m` |

---

## Error Handling in Activities

### Raising Retryable Errors

```python
from temporalio.exceptions import ApplicationError

@activity.defn
async def call_external_api(url: str) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code >= 500:
            # Server error - will be retried
            raise ApplicationError(
                f"Server error: {e.response.status_code}",
                type="ServerError",
            )
        elif e.response.status_code == 429:
            # Rate limited - will be retried
            raise ApplicationError(
                "Rate limited",
                type="RateLimitError",
            )
        else:
            # Client error (4xx) - don't retry
            raise ApplicationError(
                f"Client error: {e.response.status_code}",
                type="ClientError",
                non_retryable=True,
            )
```

### Non-Retryable Errors

```python
@activity.defn
async def validate_input(data: dict) -> dict:
    if not data.get("email"):
        raise ApplicationError(
            "Email is required",
            type="ValidationError",
            non_retryable=True,  # Don't retry validation failures
        )
    
    if not is_valid_email(data["email"]):
        raise ApplicationError(
            "Invalid email format",
            type="ValidationError",
            non_retryable=True,
        )
    
    return {"valid": True}
```

---

## Activity Context

### Available Activity Information

```python
@activity.defn
async def my_activity(input: dict) -> dict:
    info = activity.info()
    
    # Activity metadata
    activity_id = info.activity_id
    activity_type = info.activity_type
    task_queue = info.task_queue
    
    # Workflow context
    workflow_id = info.workflow_id
    workflow_run_id = info.workflow_run_id
    workflow_type = info.workflow_type
    workflow_namespace = info.workflow_namespace
    
    # Execution details
    attempt = info.attempt  # Current retry attempt (1-based)
    scheduled_time = info.scheduled_time
    started_time = info.started_time
    current_attempt_scheduled_time = info.current_attempt_scheduled_time
    
    # Heartbeat details (from previous attempt)
    heartbeat_details = info.heartbeat_details
    
    # Timeouts
    start_to_close_timeout = info.start_to_close_timeout
    schedule_to_close_timeout = info.schedule_to_close_timeout
    heartbeat_timeout = info.heartbeat_timeout
    
    activity.logger.info(f"Attempt {attempt} of activity {activity_id}")
    
    return {"processed": True}
```

### Activity Logger

```python
@activity.defn
async def logged_activity(data: dict) -> dict:
    # Use activity logger for structured logging
    activity.logger.info("Starting activity", extra={"data_size": len(data)})
    
    try:
        result = await process(data)
        activity.logger.info("Activity completed", extra={"result_id": result["id"]})
        return result
    except Exception as e:
        activity.logger.error("Activity failed", extra={"error": str(e)})
        raise
```

---

## Cancellation Handling

### Detecting Cancellation

```python
import asyncio

@activity.defn
async def cancellable_activity(items: list) -> dict:
    """Activity that handles cancellation gracefully."""
    processed = []
    
    try:
        for item in items:
            # Check for cancellation before each item
            # Heartbeat also checks cancellation
            activity.heartbeat(len(processed))
            
            result = await process_item(item)
            processed.append(result)
            
    except asyncio.CancelledError:
        # Workflow cancelled us - clean up
        activity.logger.info(f"Cancelled after processing {len(processed)} items")
        await cleanup_partial_work(processed)
        raise  # Re-raise to signal cancellation
    
    return {"processed": processed}
```

### Cleanup on Cancellation

```python
@activity.defn
async def activity_with_cleanup():
    """Activity with proper resource cleanup."""
    resource = None
    
    try:
        resource = await acquire_resource()
        
        while True:
            activity.heartbeat()
            await do_work(resource)
            
    except asyncio.CancelledError:
        activity.logger.info("Activity cancelled, cleaning up...")
        raise
    finally:
        # Always cleanup
        if resource:
            await release_resource(resource)
```

---

## Activity Patterns

### Pattern 1: Wrapper for External APIs

```python
from dataclasses import dataclass
from typing import Optional
import httpx

@dataclass
class HTTPRequest:
    url: str
    method: str = "GET"
    headers: Optional[dict] = None
    body: Optional[dict] = None
    timeout: float = 30.0

@dataclass
class HTTPResponse:
    status_code: int
    body: dict
    headers: dict

@activity.defn
async def http_request(request: HTTPRequest) -> HTTPResponse:
    """Generic HTTP activity wrapper."""
    async with httpx.AsyncClient(timeout=request.timeout) as client:
        activity.logger.info(f"{request.method} {request.url}")
        
        response = await client.request(
            method=request.method,
            url=request.url,
            headers=request.headers,
            json=request.body,
        )
        
        return HTTPResponse(
            status_code=response.status_code,
            body=response.json() if response.content else {},
            headers=dict(response.headers),
        )
```

### Pattern 2: Database Operations

```python
from dataclasses import dataclass
from typing import Any, List

@dataclass
class QueryInput:
    query: str
    params: tuple = ()

@dataclass
class QueryResult:
    rows: List[dict]
    row_count: int

@activity.defn
async def execute_query(input: QueryInput) -> QueryResult:
    """Database query activity."""
    import asyncpg
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(input.query, *input.params)
        return QueryResult(
            rows=[dict(row) for row in rows],
            row_count=len(rows),
        )
    finally:
        await conn.close()

@activity.defn
async def execute_command(input: QueryInput) -> int:
    """Database command activity (INSERT, UPDATE, DELETE)."""
    import asyncpg
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        result = await conn.execute(input.query, *input.params)
        # Returns "INSERT 0 5" or similar
        return int(result.split()[-1])
    finally:
        await conn.close()
```

### Pattern 3: File Operations

```python
from pathlib import Path
import aiofiles

@activity.defn
async def read_file(file_path: str) -> str:
    """Read file content."""
    async with aiofiles.open(file_path, 'r') as f:
        return await f.read()

@activity.defn
async def write_file(file_path: str, content: str) -> dict:
    """Write content to file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiofiles.open(file_path, 'w') as f:
        await f.write(content)
    
    return {
        "path": str(path.absolute()),
        "size": len(content),
    }

@activity.defn
async def process_csv_file(input_path: str, output_path: str) -> dict:
    """Process large CSV with heartbeating."""
    import csv
    
    processed = 0
    
    with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
        reader = csv.DictReader(infile)
        writer = None
        
        for row in reader:
            # Process row
            processed_row = transform_row(row)
            
            # Write header on first row
            if writer is None:
                writer = csv.DictWriter(outfile, fieldnames=processed_row.keys())
                writer.writeheader()
            
            writer.writerow(processed_row)
            processed += 1
            
            # Heartbeat every 1000 rows
            if processed % 1000 == 0:
                activity.heartbeat(processed)
    
    return {"rows_processed": processed}
```

### Pattern 4: Notification Activities

```python
@dataclass
class SlackMessage:
    channel: str
    text: str
    blocks: Optional[list] = None

@activity.defn
async def send_slack_message(message: SlackMessage) -> dict:
    """Send Slack notification."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {SLACK_TOKEN}"},
            json={
                "channel": message.channel,
                "text": message.text,
                "blocks": message.blocks,
            },
        )
        result = response.json()
        
        if not result.get("ok"):
            raise ApplicationError(
                f"Slack error: {result.get('error')}",
                type="SlackError",
            )
        
        return {"ts": result["ts"], "channel": result["channel"]}

@dataclass
class TelegramMessage:
    chat_id: str
    text: str
    parse_mode: str = "HTML"

@activity.defn
async def send_telegram_message(message: TelegramMessage) -> dict:
    """Send Telegram notification."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": message.chat_id,
                "text": message.text,
                "parse_mode": message.parse_mode,
            },
        )
        result = response.json()
        
        if not result.get("ok"):
            raise ApplicationError(
                f"Telegram error: {result.get('description')}",
                type="TelegramError",
            )
        
        return {"message_id": result["result"]["message_id"]}
```

---

## Best Practices

### 1. Keep Activities Focused
```python
# GOOD: Single responsibility
@activity.defn
async def fetch_user(user_id: str) -> dict: ...

@activity.defn
async def update_user(user_id: str, data: dict) -> dict: ...

# BAD: Does too much
@activity.defn
async def fetch_and_update_user(user_id: str, data: dict) -> dict: ...
```

### 2. Use Dataclasses for Input/Output
```python
# GOOD: Typed, documented
@dataclass
class ProcessInput:
    item_id: str
    options: dict

@activity.defn
async def process(input: ProcessInput) -> ProcessResult: ...

# BAD: Untyped dict
@activity.defn
async def process(data: dict) -> dict: ...
```

### 3. Always Set Timeouts
```python
# GOOD: Explicit timeout
await workflow.execute_activity(
    my_activity,
    input,
    start_to_close_timeout=timedelta(minutes=5),
)

# BAD: No timeout (will fail)
await workflow.execute_activity(my_activity, input)
```

### 4. Use Heartbeats for Long Operations
```python
@activity.defn
async def long_running(items: list):
    for i, item in enumerate(items):
        activity.heartbeat(i)  # Report progress
        await process(item)
```

### 5. Make Activities Idempotent
```python
@activity.defn
async def create_order(order_id: str, data: dict) -> dict:
    # Check if already exists (idempotent)
    existing = await db.get_order(order_id)
    if existing:
        return existing
    
    # Create new
    return await db.create_order(order_id, data)
```

---

## Next Steps

- **temporal-workflows.md** - Workflow patterns and orchestration
- **temporal-workers.md** - Worker configuration and deployment
