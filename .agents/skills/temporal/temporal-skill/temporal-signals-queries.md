# Temporal Signals, Queries, and Updates

> **Interactive Workflow Communication Patterns**  
> Enable external interaction with running workflows through signals, queries, and updates.

## Overview

Temporal provides three mechanisms for interacting with running workflows:

| Mechanism | Direction | Behavior | Use Case |
|-----------|-----------|----------|----------|
| **Signal** | External → Workflow | Fire-and-forget, async | Trigger actions, send data |
| **Query** | External ← Workflow | Read-only, sync | Get current state |
| **Update** | Bidirectional | Sync with response | Modify state and get result |

---

## Signals

Signals are asynchronous messages sent to running workflows. They trigger workflow code but don't wait for a response.

### Basic Signal Pattern

```python
from temporalio import workflow
from dataclasses import dataclass
from typing import Optional

@dataclass
class ApprovalDecision:
    approved: bool
    approver: str
    comments: Optional[str] = None

@workflow.defn
class ApprovalWorkflow:
    def __init__(self):
        self._decision: Optional[ApprovalDecision] = None
        self._status = "pending"
    
    @workflow.run
    async def run(self, request_id: str) -> dict:
        # Wait for signal
        await workflow.wait_condition(lambda: self._decision is not None)
        
        return {
            "request_id": request_id,
            "approved": self._decision.approved,
            "approver": self._decision.approver,
        }
    
    @workflow.signal
    async def approve(self, approver: str, comments: Optional[str] = None):
        """Signal to approve the request."""
        self._decision = ApprovalDecision(
            approved=True,
            approver=approver,
            comments=comments
        )
        self._status = f"approved by {approver}"
    
    @workflow.signal
    async def reject(self, approver: str, reason: str):
        """Signal to reject the request."""
        self._decision = ApprovalDecision(
            approved=False,
            approver=approver,
            comments=reason
        )
        self._status = f"rejected by {approver}"
```

### Sending Signals from Client

```python
import asyncio
from temporalio.client import Client

async def send_approval():
    client = await Client.connect("localhost:7233")
    
    # Get handle to running workflow
    handle = client.get_workflow_handle("approval-REQ-001")
    
    # Send signal
    await handle.signal(ApprovalWorkflow.approve, "alice", "Looks good!")
    
    # Wait for result
    result = await handle.result()
    print(f"Result: {result}")

asyncio.run(send_approval())
```

### Signal with Start (Start + Signal Atomically)

```python
async def signal_with_start():
    client = await Client.connect("localhost:7233")
    
    # Start workflow and send signal atomically
    handle = await client.start_workflow(
        ApprovalWorkflow.run,
        "REQ-002",
        id="approval-REQ-002",
        task_queue="approval-queue",
        start_signal="approve",  # Signal name
        start_signal_args=["admin", "Auto-approved"],  # Signal arguments
    )
    
    result = await handle.result()
    return result
```

### CLI Signal Commands

```bash
# Send signal to workflow
temporal workflow signal \
  --workflow-id "approval-REQ-001" \
  --signal-name "approve" \
  --input '"alice"' \
  --input '"LGTM!"'

# Signal with JSON object
temporal workflow signal \
  --workflow-id "order-12345" \
  --signal-name "update_status" \
  --input '{"status": "shipped", "tracking": "1Z999"}'
```

---

## Queries

Queries read workflow state synchronously without modifying it. They must be read-only.

### Basic Query Pattern

```python
from temporalio import workflow
from dataclasses import dataclass
from typing import List

@dataclass
class OrderItem:
    sku: str
    quantity: int
    status: str

@workflow.defn
class OrderWorkflow:
    def __init__(self):
        self._status = "pending"
        self._items: List[OrderItem] = []
        self._history: List[str] = []
    
    @workflow.run
    async def run(self, order_id: str) -> dict:
        # ... workflow logic ...
        return {"order_id": order_id, "final_status": self._status}
    
    @workflow.query
    def get_status(self) -> str:
        """Get current order status."""
        return self._status
    
    @workflow.query
    def get_items(self) -> List[dict]:
        """Get all order items."""
        return [
            {"sku": item.sku, "quantity": item.quantity, "status": item.status}
            for item in self._items
        ]
    
    @workflow.query
    def get_history(self) -> List[str]:
        """Get workflow history log."""
        return self._history
    
    @workflow.query
    def get_items_by_status(self, status: str) -> List[dict]:
        """Query with parameter - get items filtered by status."""
        return [
            {"sku": item.sku, "quantity": item.quantity}
            for item in self._items
            if item.status == status
        ]
```

### Executing Queries from Client

```python
import asyncio
from temporalio.client import Client

async def query_workflow():
    client = await Client.connect("localhost:7233")
    
    handle = client.get_workflow_handle("order-12345")
    
    # Simple query
    status = await handle.query(OrderWorkflow.get_status)
    print(f"Status: {status}")
    
    # Query with parameter
    pending_items = await handle.query(OrderWorkflow.get_items_by_status, "pending")
    print(f"Pending items: {pending_items}")
    
    # Query by name (string)
    history = await handle.query("get_history")
    print(f"History: {history}")

asyncio.run(query_workflow())
```

### CLI Query Commands

```bash
# Query workflow status
temporal workflow query \
  --workflow-id "order-12345" \
  --query-type "get_status"

# Query with argument
temporal workflow query \
  --workflow-id "order-12345" \
  --query-type "get_items_by_status" \
  --input '"pending"'

# Query with JSON output
temporal workflow query \
  --workflow-id "order-12345" \
  --query-type "get_items" \
  --output json
```

---

## Updates (Temporal 1.21+)

Updates combine signals and queries - they modify workflow state and return a result synchronously.

### Basic Update Pattern

```python
from temporalio import workflow
from dataclasses import dataclass
from typing import Optional

@workflow.defn
class CartWorkflow:
    def __init__(self):
        self._items: dict = {}
        self._completed = False
    
    @workflow.run
    async def run(self) -> dict:
        # Wait until checkout is complete
        await workflow.wait_condition(lambda: self._completed)
        return {"items": self._items, "total": sum(self._items.values())}
    
    @workflow.update
    async def add_item(self, sku: str, price: float) -> dict:
        """Add item to cart and return updated cart."""
        self._items[sku] = price
        return {
            "added": sku,
            "cart_total": sum(self._items.values()),
            "item_count": len(self._items)
        }
    
    @workflow.update
    async def remove_item(self, sku: str) -> dict:
        """Remove item from cart."""
        if sku in self._items:
            del self._items[sku]
            return {"removed": sku, "cart_total": sum(self._items.values())}
        return {"error": f"Item {sku} not in cart"}
    
    @workflow.update
    async def checkout(self) -> dict:
        """Complete the order."""
        if not self._items:
            return {"error": "Cart is empty"}
        self._completed = True
        return {"status": "completed", "total": sum(self._items.values())}
```

### Update with Validation

```python
@workflow.defn
class InventoryWorkflow:
    def __init__(self):
        self._stock: dict = {}
    
    @workflow.run
    async def run(self, initial_stock: dict) -> dict:
        self._stock = initial_stock
        await workflow.wait_condition(lambda: False)  # Run forever
        return self._stock
    
    @workflow.update
    async def reserve_stock(self, sku: str, quantity: int) -> dict:
        """Reserve stock with validation."""
        current = self._stock.get(sku, 0)
        if quantity > current:
            return {
                "success": False,
                "error": f"Insufficient stock. Available: {current}"
            }
        self._stock[sku] = current - quantity
        return {
            "success": True,
            "reserved": quantity,
            "remaining": self._stock[sku]
        }
    
    @workflow.update_validator
    def validate_reserve_stock(self, sku: str, quantity: int):
        """Validator runs before update - can reject with exception."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if sku not in self._stock:
            raise ValueError(f"Unknown SKU: {sku}")
```

### Executing Updates from Client

```python
import asyncio
from temporalio.client import Client

async def use_updates():
    client = await Client.connect("localhost:7233")
    
    # Start cart workflow
    handle = await client.start_workflow(
        CartWorkflow.run,
        id="cart-user-123",
        task_queue="cart-queue",
    )
    
    # Add items via update
    result1 = await handle.execute_update(
        CartWorkflow.add_item,
        args=["SKU-001", 29.99]
    )
    print(f"After add: {result1}")
    
    result2 = await handle.execute_update(
        CartWorkflow.add_item,
        args=["SKU-002", 49.99]
    )
    print(f"After second add: {result2}")
    
    # Checkout
    final = await handle.execute_update(CartWorkflow.checkout)
    print(f"Checkout result: {final}")
    
    # Wait for workflow to complete
    result = await handle.result()
    print(f"Final result: {result}")

asyncio.run(use_updates())
```

---

## Human-in-the-Loop Patterns

### Multi-Level Approval Chain

```python
from temporalio import workflow
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import timedelta

@dataclass
class ApprovalLevel:
    level: int
    approver: Optional[str] = None
    approved: Optional[bool] = None
    timestamp: Optional[str] = None

@dataclass
class MultiApprovalRequest:
    request_id: str
    requester: str
    amount: float
    required_levels: int
    timeout_minutes: int = 60

@workflow.defn
class MultiLevelApprovalWorkflow:
    """Workflow requiring multiple approval levels."""
    
    def __init__(self):
        self._approvals: List[ApprovalLevel] = []
        self._current_level = 1
        self._status = "pending"
        self._rejected = False
    
    @workflow.run
    async def run(self, request: MultiApprovalRequest) -> dict:
        # Initialize approval levels
        self._approvals = [
            ApprovalLevel(level=i+1) for i in range(request.required_levels)
        ]
        
        # Wait for all approvals or rejection
        for level in range(1, request.required_levels + 1):
            self._current_level = level
            self._status = f"awaiting_level_{level}"
            
            # Notify approver for this level
            await workflow.execute_activity(
                notify_approver,
                {"request_id": request.request_id, "level": level},
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            # Wait for this level's decision with timeout
            try:
                await workflow.wait_condition(
                    lambda: self._get_level_decision(level) is not None,
                    timeout=timedelta(minutes=request.timeout_minutes),
                )
            except TimeoutError:
                self._status = f"timed_out_at_level_{level}"
                return {
                    "request_id": request.request_id,
                    "status": "timed_out",
                    "level": level
                }
            
            # Check if rejected
            if self._rejected:
                self._status = f"rejected_at_level_{level}"
                return {
                    "request_id": request.request_id,
                    "status": "rejected",
                    "level": level,
                    "approvals": [a.__dict__ for a in self._approvals]
                }
        
        self._status = "approved"
        return {
            "request_id": request.request_id,
            "status": "approved",
            "approvals": [a.__dict__ for a in self._approvals]
        }
    
    def _get_level_decision(self, level: int) -> Optional[bool]:
        for a in self._approvals:
            if a.level == level:
                return a.approved
        return None
    
    @workflow.signal
    async def approve_level(self, level: int, approver: str):
        """Approve a specific level."""
        for a in self._approvals:
            if a.level == level and a.approved is None:
                a.approved = True
                a.approver = approver
                a.timestamp = str(workflow.now())
                break
    
    @workflow.signal
    async def reject_level(self, level: int, approver: str, reason: str):
        """Reject at a specific level."""
        for a in self._approvals:
            if a.level == level and a.approved is None:
                a.approved = False
                a.approver = approver
                a.timestamp = str(workflow.now())
                self._rejected = True
                break
    
    @workflow.query
    def get_status(self) -> dict:
        return {
            "status": self._status,
            "current_level": self._current_level,
            "approvals": [a.__dict__ for a in self._approvals]
        }
```

### Approval with Timeout and Reminders

```python
from temporalio import workflow
from datetime import timedelta
from dataclasses import dataclass
from typing import Optional

@dataclass
class ApprovalRequest:
    request_id: str
    requester: str
    action: str
    timeout_minutes: int = 60
    reminder_interval_minutes: int = 15

@workflow.defn
class ApprovalWithRemindersWorkflow:
    """Approval workflow with periodic reminders."""
    
    def __init__(self):
        self._decision: Optional[dict] = None
        self._reminders_sent = 0
    
    @workflow.run
    async def run(self, request: ApprovalRequest) -> dict:
        # Send initial request
        await workflow.execute_activity(
            send_approval_request,
            request,
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        timeout = timedelta(minutes=request.timeout_minutes)
        reminder_interval = timedelta(minutes=request.reminder_interval_minutes)
        deadline = workflow.now() + timeout
        
        while workflow.now() < deadline:
            # Calculate next reminder or deadline
            remaining = deadline - workflow.now()
            wait_time = min(reminder_interval, remaining)
            
            # Wait for decision or reminder interval
            try:
                await workflow.wait_condition(
                    lambda: self._decision is not None,
                    timeout=wait_time,
                )
                # Decision received
                break
            except TimeoutError:
                # No decision yet - send reminder if not at deadline
                if workflow.now() < deadline:
                    self._reminders_sent += 1
                    await workflow.execute_activity(
                        send_reminder,
                        {
                            "request_id": request.request_id,
                            "reminder_number": self._reminders_sent
                        },
                        start_to_close_timeout=timedelta(seconds=30),
                    )
        
        if self._decision is None:
            # Timed out
            return {
                "request_id": request.request_id,
                "status": "timed_out",
                "reminders_sent": self._reminders_sent
            }
        
        return {
            "request_id": request.request_id,
            "status": "approved" if self._decision["approved"] else "rejected",
            "approver": self._decision["approver"],
            "reminders_sent": self._reminders_sent
        }
    
    @workflow.signal
    async def decide(self, approved: bool, approver: str, comments: str = ""):
        self._decision = {
            "approved": approved,
            "approver": approver,
            "comments": comments
        }
    
    @workflow.query
    def get_reminder_count(self) -> int:
        return self._reminders_sent
```

---

## Wait Condition Patterns

### Wait for Multiple Signals

```python
@workflow.defn
class MultiSignalWorkflow:
    def __init__(self):
        self._data_received = False
        self._config_received = False
        self._data = None
        self._config = None
    
    @workflow.run
    async def run(self) -> dict:
        # Wait for BOTH signals
        await workflow.wait_condition(
            lambda: self._data_received and self._config_received
        )
        
        # Process with both inputs
        return await workflow.execute_activity(
            process_with_config,
            {"data": self._data, "config": self._config},
            start_to_close_timeout=timedelta(minutes=5),
        )
    
    @workflow.signal
    async def send_data(self, data: dict):
        self._data = data
        self._data_received = True
    
    @workflow.signal
    async def send_config(self, config: dict):
        self._config = config
        self._config_received = True
```

### Wait for Any of Multiple Conditions

```python
@workflow.defn
class RaceConditionWorkflow:
    def __init__(self):
        self._user_approved = False
        self._auto_approved = False
        self._cancelled = False
    
    @workflow.run
    async def run(self, request_id: str) -> dict:
        # Start auto-approval timer
        auto_approve_task = asyncio.create_task(
            self._auto_approve_after_delay()
        )
        
        # Wait for any condition
        await workflow.wait_condition(
            lambda: self._user_approved or self._auto_approved or self._cancelled
        )
        
        if self._cancelled:
            return {"status": "cancelled"}
        elif self._user_approved:
            return {"status": "user_approved"}
        else:
            return {"status": "auto_approved"}
    
    async def _auto_approve_after_delay(self):
        """Auto-approve after 24 hours of no response."""
        await asyncio.sleep(86400)  # 24 hours
        if not self._user_approved and not self._cancelled:
            self._auto_approved = True
    
    @workflow.signal
    async def approve(self):
        self._user_approved = True
    
    @workflow.signal
    async def cancel(self):
        self._cancelled = True
```

---

## Signal Buffering and Ordering

Signals are processed in order. You can accumulate signals before processing.

```python
from typing import List
from dataclasses import dataclass

@dataclass
class BatchItem:
    id: str
    data: dict

@workflow.defn
class BatchSignalWorkflow:
    """Collect signals and process in batches."""
    
    def __init__(self):
        self._items: List[BatchItem] = []
        self._should_process = False
        self._completed = False
    
    @workflow.run
    async def run(self, batch_size: int = 10) -> dict:
        processed_batches = 0
        total_items = 0
        
        while not self._completed:
            # Wait for batch to fill or explicit trigger
            await workflow.wait_condition(
                lambda: len(self._items) >= batch_size 
                        or self._should_process 
                        or self._completed
            )
            
            if self._completed and not self._items:
                break
            
            # Process current batch
            batch = self._items[:batch_size]
            self._items = self._items[batch_size:]
            self._should_process = False
            
            await workflow.execute_activity(
                process_batch,
                [item.__dict__ for item in batch],
                start_to_close_timeout=timedelta(minutes=5),
            )
            
            processed_batches += 1
            total_items += len(batch)
        
        return {
            "batches_processed": processed_batches,
            "total_items": total_items
        }
    
    @workflow.signal
    async def add_item(self, id: str, data: dict):
        """Add item to current batch."""
        self._items.append(BatchItem(id=id, data=data))
    
    @workflow.signal
    async def process_now(self):
        """Trigger immediate processing of current batch."""
        self._should_process = True
    
    @workflow.signal
    async def complete(self):
        """Signal to complete after processing remaining items."""
        self._completed = True
        self._should_process = True  # Process any remaining
    
    @workflow.query
    def get_pending_count(self) -> int:
        return len(self._items)
```

---

## Dynamic Signal/Query Handlers

Handle signals and queries with dynamic names.

```python
@workflow.defn
class DynamicHandlerWorkflow:
    def __init__(self):
        self._data: dict = {}
    
    @workflow.run
    async def run(self) -> dict:
        # Set up dynamic handlers
        workflow.set_signal_handler("set_*", self._handle_set_signal)
        workflow.set_query_handler("get_*", self._handle_get_query)
        
        await workflow.wait_condition(lambda: self._data.get("done", False))
        return self._data
    
    async def _handle_set_signal(self, signal_name: str, value: any):
        """Handle any signal starting with 'set_'."""
        key = signal_name[4:]  # Remove 'set_' prefix
        self._data[key] = value
    
    def _handle_get_query(self, query_name: str) -> any:
        """Handle any query starting with 'get_'."""
        key = query_name[4:]  # Remove 'get_' prefix
        return self._data.get(key)
```

---

## Best Practices

### Signal Best Practices

1. **Signals are fire-and-forget** - Don't expect immediate response
2. **Make signals idempotent** - Same signal multiple times should be safe
3. **Use wait_condition for coordination** - Not sleep loops
4. **Consider signal ordering** - They're processed in order received

### Query Best Practices

1. **Queries must be read-only** - Never modify state
2. **Keep queries fast** - They block the workflow
3. **Return serializable data** - No complex objects
4. **Handle missing state gracefully** - Return defaults

### Update Best Practices

1. **Use validators** - Reject invalid updates early
2. **Updates can fail** - Handle exceptions properly
3. **Updates are synchronous** - Don't do heavy work
4. **Consider using activities** - For complex operations

---

## CLI Reference

```bash
# Send signal
temporal workflow signal \
  --workflow-id ID \
  --signal-name NAME \
  --input 'arg1' \
  --input 'arg2'

# Query workflow
temporal workflow query \
  --workflow-id ID \
  --query-type QUERY_NAME

# Query with input
temporal workflow query \
  --workflow-id ID \
  --query-type QUERY_NAME \
  --input '"param"'

# List workflow signals (from history)
temporal workflow show --workflow-id ID | grep -i signal

# Stack trace for debugging
temporal workflow stack --workflow-id ID
```

---

**Next:** See **temporal-advanced.md** for saga patterns, child workflows, and continue-as-new.
