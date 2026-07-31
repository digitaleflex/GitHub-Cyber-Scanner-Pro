# Temporal Workflows

> Workflow patterns from simple to complex, orchestration strategies

## Overview

Workflows are durable functions that orchestrate activities and other workflows. They must be deterministic - the same input always produces the same output.

---

## Simple Patterns

### Single Activity Workflow

```python
from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import send_email, EmailInput

@workflow.defn
class SendEmailWorkflow:
    """Simplest workflow - single activity."""
    
    @workflow.run
    async def run(self, email_input: EmailInput) -> dict:
        return await workflow.execute_activity(
            send_email,
            email_input,
            start_to_close_timeout=timedelta(seconds=30),
        )
```

### Sequential Activities

```python
@workflow.defn
class OrderProcessingWorkflow:
    """Execute activities in sequence."""
    
    @workflow.run
    async def run(self, order: dict) -> dict:
        # Step 1: Validate
        validation = await workflow.execute_activity(
            validate_order,
            order,
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        if not validation["valid"]:
            return {"status": "invalid", "errors": validation["errors"]}
        
        # Step 2: Process payment
        payment = await workflow.execute_activity(
            process_payment,
            order,
            start_to_close_timeout=timedelta(minutes=2),
        )
        
        # Step 3: Fulfill order
        fulfillment = await workflow.execute_activity(
            fulfill_order,
            {"order": order, "payment_id": payment["id"]},
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        return {
            "status": "completed",
            "order_id": order["id"],
            "tracking": fulfillment["tracking_number"],
        }
```

### Parallel Activities

```python
import asyncio

@workflow.defn
class ParallelProcessingWorkflow:
    """Execute activities in parallel."""
    
    @workflow.run
    async def run(self, items: list[str]) -> list[dict]:
        # Execute all in parallel
        results = await asyncio.gather(*[
            workflow.execute_activity(
                process_item,
                item,
                start_to_close_timeout=timedelta(seconds=30),
            )
            for item in items
        ])
        
        return results
```

### Parallel with Batching

```python
@workflow.defn
class BatchedParallelWorkflow:
    """Process items in parallel batches."""
    
    @workflow.run
    async def run(self, items: list[str], batch_size: int = 10) -> list[dict]:
        all_results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Process batch in parallel
            batch_results = await asyncio.gather(*[
                workflow.execute_activity(
                    process_item,
                    item,
                    start_to_close_timeout=timedelta(seconds=30),
                )
                for item in batch
            ])
            
            all_results.extend(batch_results)
            workflow.logger.info(f"Completed batch {i // batch_size + 1}")
        
        return all_results
```

---

## Intermediate Patterns

### Workflow with Retry Policy

```python
from temporalio.common import RetryPolicy

@workflow.defn
class RobustWorkflow:
    """Workflow with custom retry policies."""
    
    @workflow.run
    async def run(self, data: dict) -> dict:
        # Critical operation - aggressive retry
        result = await workflow.execute_activity(
            critical_operation,
            data,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(minutes=1),
                maximum_attempts=10,
                non_retryable_error_types=["ValidationError"],
            ),
        )
        
        # Notification - best effort
        try:
            await workflow.execute_activity(
                send_notification,
                result,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
        except Exception:
            workflow.logger.warning("Notification failed, continuing")
        
        return result
```

### Workflow with State

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class WorkflowState:
    status: str = "pending"
    steps_completed: List[str] = field(default_factory=list)
    current_step: Optional[str] = None
    error: Optional[str] = None

@workflow.defn
class StatefulWorkflow:
    """Workflow that tracks its state."""
    
    def __init__(self):
        self._state = WorkflowState()
    
    @workflow.run
    async def run(self, input: dict) -> dict:
        try:
            # Step 1
            self._state.current_step = "validation"
            await workflow.execute_activity(validate, input, ...)
            self._state.steps_completed.append("validation")
            
            # Step 2
            self._state.current_step = "processing"
            result = await workflow.execute_activity(process, input, ...)
            self._state.steps_completed.append("processing")
            
            # Step 3
            self._state.current_step = "notification"
            await workflow.execute_activity(notify, result, ...)
            self._state.steps_completed.append("notification")
            
            self._state.status = "completed"
            self._state.current_step = None
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            self._state.status = "failed"
            self._state.error = str(e)
            raise
    
    @workflow.query
    def get_state(self) -> dict:
        return self._state.__dict__
```

### Timer-Based Workflow

```python
import asyncio
from datetime import timedelta

@workflow.defn
class DelayedActionWorkflow:
    """Workflow with built-in delays."""
    
    @workflow.run
    async def run(self, action: dict) -> dict:
        # Schedule action
        await workflow.execute_activity(
            schedule_action,
            action,
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        # Wait for specified duration (durable timer)
        delay_seconds = action.get("delay_seconds", 3600)
        await asyncio.sleep(delay_seconds)
        
        # Execute delayed action
        result = await workflow.execute_activity(
            execute_action,
            action,
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        return result
```

### Polling Workflow

```python
@workflow.defn
class PollingWorkflow:
    """Poll until condition is met."""
    
    @workflow.run
    async def run(self, resource_id: str) -> dict:
        max_attempts = 60
        poll_interval = timedelta(seconds=10)
        
        for attempt in range(max_attempts):
            status = await workflow.execute_activity(
                check_resource_status,
                resource_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
            
            if status["ready"]:
                return {"status": "ready", "data": status}
            
            if status["failed"]:
                raise ApplicationError(f"Resource failed: {status['error']}")
            
            workflow.logger.info(f"Attempt {attempt + 1}: not ready, waiting...")
            await asyncio.sleep(poll_interval.total_seconds())
        
        raise ApplicationError(
            f"Resource {resource_id} not ready after {max_attempts} attempts",
            type="TimeoutError",
        )
```

---

## Advanced Patterns

### Signals and Queries

```python
from typing import Optional, List

@workflow.defn
class ApprovalWorkflow:
    """Human-in-the-loop approval workflow."""
    
    def __init__(self):
        self._decision: Optional[bool] = None
        self._approver: Optional[str] = None
        self._comments: List[str] = []
        self._status = "pending"
    
    @workflow.run
    async def run(self, request: dict) -> dict:
        # Send approval request
        await workflow.execute_activity(
            send_approval_request,
            request,
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        # Wait for decision (with timeout)
        timeout_hours = request.get("timeout_hours", 24)
        
        try:
            await asyncio.wait_for(
                workflow.wait_condition(lambda: self._decision is not None),
                timeout=timeout_hours * 3600,
            )
        except asyncio.TimeoutError:
            self._status = "expired"
            await workflow.execute_activity(
                notify_timeout,
                request,
                start_to_close_timeout=timedelta(seconds=30),
            )
            return {"status": "expired", "request_id": request["id"]}
        
        # Process decision
        if self._decision:
            self._status = "approved"
            result = await workflow.execute_activity(
                execute_approved_action,
                request,
                start_to_close_timeout=timedelta(minutes=5),
            )
            return {
                "status": "approved",
                "approver": self._approver,
                "result": result,
            }
        else:
            self._status = "rejected"
            return {
                "status": "rejected",
                "approver": self._approver,
                "reason": self._comments[-1] if self._comments else None,
            }
    
    @workflow.signal
    async def approve(self, approver: str, comment: Optional[str] = None):
        """Signal to approve the request."""
        self._decision = True
        self._approver = approver
        if comment:
            self._comments.append(comment)
    
    @workflow.signal
    async def reject(self, approver: str, reason: str):
        """Signal to reject the request."""
        self._decision = False
        self._approver = approver
        self._comments.append(reason)
    
    @workflow.signal
    async def add_comment(self, author: str, comment: str):
        """Add a comment without deciding."""
        self._comments.append(f"{author}: {comment}")
    
    @workflow.query
    def get_status(self) -> str:
        return self._status
    
    @workflow.query
    def get_comments(self) -> List[str]:
        return self._comments
    
    @workflow.query
    def get_decision(self) -> Optional[dict]:
        if self._decision is not None:
            return {
                "approved": self._decision,
                "approver": self._approver,
            }
        return None
```

### Child Workflows

```python
@workflow.defn
class ParentWorkflow:
    """Orchestrate child workflows."""
    
    @workflow.run
    async def run(self, orders: List[dict]) -> dict:
        results = []
        
        # Start child workflows in parallel
        handles = []
        for order in orders:
            handle = await workflow.start_child_workflow(
                OrderWorkflow.run,
                order,
                id=f"order-{order['id']}",
                task_queue="order-queue",
            )
            handles.append(handle)
        
        # Wait for all to complete
        for handle in handles:
            try:
                result = await handle.result()
                results.append({"order_id": handle.id, "status": "success", "result": result})
            except Exception as e:
                results.append({"order_id": handle.id, "status": "failed", "error": str(e)})
        
        successful = sum(1 for r in results if r["status"] == "success")
        
        return {
            "total": len(orders),
            "successful": successful,
            "failed": len(orders) - successful,
            "results": results,
        }


@workflow.defn
class OrderWorkflow:
    """Child workflow for individual order."""
    
    @workflow.run
    async def run(self, order: dict) -> dict:
        # Process single order
        await workflow.execute_activity(
            validate_order,
            order,
            start_to_close_timeout=timedelta(minutes=1),
        )
        
        await workflow.execute_activity(
            process_order,
            order,
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        return {"order_id": order["id"], "status": "completed"}
```

### Continue-As-New (Long-Running Workflows)

```python
@workflow.defn
class LongRunningMonitorWorkflow:
    """Monitor workflow that uses continue-as-new to avoid history bloat."""
    
    def __init__(self):
        self._should_stop = False
        self._iterations = 0
    
    @workflow.run
    async def run(self, state: dict) -> dict:
        # Restore state from previous run
        processed_ids = set(state.get("processed_ids", []))
        total_processed = state.get("total_processed", 0)
        iteration = state.get("iteration", 0)
        
        MAX_ITERATIONS = 100  # Continue-as-new after 100 iterations
        
        while self._iterations < MAX_ITERATIONS and not self._should_stop:
            # Poll for new items
            new_items = await workflow.execute_activity(
                fetch_new_items,
                list(processed_ids),
                start_to_close_timeout=timedelta(minutes=1),
            )
            
            for item in new_items:
                if item["id"] not in processed_ids:
                    # Process item
                    await workflow.execute_activity(
                        process_item,
                        item,
                        start_to_close_timeout=timedelta(minutes=5),
                    )
                    processed_ids.add(item["id"])
                    total_processed += 1
            
            self._iterations += 1
            
            # Wait before next poll
            await asyncio.sleep(60)
        
        if self._should_stop:
            return {
                "status": "stopped",
                "total_processed": total_processed,
            }
        
        # Continue-as-new with current state
        workflow.continue_as_new({
            "processed_ids": list(processed_ids)[-1000],  # Keep last 1000
            "total_processed": total_processed,
            "iteration": iteration + 1,
        })
    
    @workflow.signal
    async def stop(self):
        """Signal to stop the monitor."""
        self._should_stop = True
    
    @workflow.query
    def get_stats(self) -> dict:
        return {
            "iterations": self._iterations,
            "should_stop": self._should_stop,
        }
```

---

## Saga Pattern

### Saga with Compensation

```python
from dataclasses import dataclass
from typing import List, Tuple, Callable

@dataclass
class SagaStep:
    name: str
    completed: bool = False
    result: Optional[dict] = None
    compensated: bool = False

@workflow.defn
class OrderSagaWorkflow:
    """Saga pattern with automatic compensation on failure."""
    
    def __init__(self):
        self._steps: List[SagaStep] = []
        self._status = "pending"
    
    @workflow.run
    async def run(self, order: dict) -> dict:
        compensations: List[Tuple[str, dict]] = []
        
        try:
            # Step 1: Reserve Inventory
            inventory = await self._execute_step(
                "reserve_inventory",
                reserve_inventory,
                order,
            )
            compensations.append(("release_inventory", {"reservation_id": inventory["id"]}))
            
            # Step 2: Charge Payment
            payment = await self._execute_step(
                "charge_payment",
                charge_payment,
                {"order": order, "amount": order["total"]},
            )
            compensations.append(("refund_payment", {"transaction_id": payment["id"]}))
            
            # Step 3: Create Shipment
            shipment = await self._execute_step(
                "create_shipment",
                create_shipment,
                {"order": order, "inventory": inventory},
            )
            compensations.append(("cancel_shipment", {"shipment_id": shipment["id"]}))
            
            self._status = "completed"
            
            return {
                "status": "success",
                "order_id": order["id"],
                "tracking": shipment["tracking_number"],
            }
            
        except Exception as e:
            self._status = "compensating"
            workflow.logger.error(f"Saga failed: {e}, running compensations")
            
            # Run compensations in reverse order
            await self._compensate(compensations)
            
            self._status = "failed"
            return {
                "status": "failed",
                "order_id": order["id"],
                "error": str(e),
            }
    
    async def _execute_step(self, name: str, activity, args) -> dict:
        """Execute a saga step and track it."""
        step = SagaStep(name=name)
        self._steps.append(step)
        
        result = await workflow.execute_activity(
            activity,
            args,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        
        step.completed = True
        step.result = result
        return result
    
    async def _compensate(self, compensations: List[Tuple[str, dict]]):
        """Run compensation actions in reverse order."""
        compensation_activities = {
            "release_inventory": release_inventory,
            "refund_payment": refund_payment,
            "cancel_shipment": cancel_shipment,
        }
        
        for name, args in reversed(compensations):
            activity = compensation_activities.get(name)
            if activity:
                try:
                    await workflow.execute_activity(
                        activity,
                        args,
                        start_to_close_timeout=timedelta(minutes=5),
                        retry_policy=RetryPolicy(maximum_attempts=5),
                    )
                    workflow.logger.info(f"Compensated: {name}")
                except Exception as e:
                    workflow.logger.error(f"Compensation failed: {name}: {e}")
    
    @workflow.query
    def get_steps(self) -> List[dict]:
        return [
            {"name": s.name, "completed": s.completed, "compensated": s.compensated}
            for s in self._steps
        ]
```

---

## Update Handlers (Temporal 1.21+)

```python
@workflow.defn
class UpdateWorkflow:
    """Workflow with synchronous updates."""
    
    def __init__(self):
        self._data = {}
        self._complete = False
    
    @workflow.run
    async def run(self) -> dict:
        # Wait until marked complete
        await workflow.wait_condition(lambda: self._complete)
        return self._data
    
    @workflow.update
    async def update_data(self, key: str, value: str) -> dict:
        """Synchronous update - returns immediately with result."""
        self._data[key] = value
        return {"updated": key, "current": self._data}
    
    @workflow.update
    async def complete(self) -> dict:
        """Mark workflow as complete."""
        self._complete = True
        return {"status": "completing", "data": self._data}
```

---

## Error Handling

### Handling Activity Errors

```python
from temporalio.exceptions import ActivityError, ApplicationError

@workflow.defn
class ErrorHandlingWorkflow:
    @workflow.run
    async def run(self, data: dict) -> dict:
        try:
            result = await workflow.execute_activity(
                risky_activity,
                data,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            return {"status": "success", "result": result}
            
        except ActivityError as e:
            workflow.logger.error(f"Activity failed: {e}")
            
            # Check specific error type
            if e.cause and isinstance(e.cause, ApplicationError):
                error_type = e.cause.type
                
                if error_type == "ValidationError":
                    return {"status": "invalid", "error": e.cause.message}
                
                if error_type == "NotFoundError":
                    return {"status": "not_found", "error": e.cause.message}
            
            # Default: re-raise
            raise
```

### Workflow-Level Timeout

```python
@workflow.defn
class TimeoutWorkflow:
    @workflow.run
    async def run(self, data: dict) -> dict:
        try:
            result = await asyncio.wait_for(
                self._do_work(data),
                timeout=3600,  # 1 hour timeout
            )
            return {"status": "success", "result": result}
            
        except asyncio.TimeoutError:
            workflow.logger.error("Workflow timed out")
            return {"status": "timeout"}
    
    async def _do_work(self, data: dict) -> dict:
        # Multiple activities...
        pass
```

---

## Best Practices

### 1. Keep Workflows Simple
```python
# GOOD: Orchestration only
@workflow.defn
class GoodWorkflow:
    @workflow.run
    async def run(self, data: dict):
        result = await workflow.execute_activity(process, data, ...)
        return result

# BAD: Business logic in workflow
@workflow.defn
class BadWorkflow:
    @workflow.run
    async def run(self, data: dict):
        # Don't do complex logic here
        transformed = complex_transformation(data)  # BAD
        return transformed
```

### 2. Use Typed Inputs/Outputs
```python
# GOOD: Strongly typed
@dataclass
class OrderInput:
    order_id: str
    items: List[dict]
    customer_id: str

@workflow.defn
class TypedWorkflow:
    @workflow.run
    async def run(self, input: OrderInput) -> OrderResult:
        ...

# BAD: Untyped dicts
@workflow.defn
class UntypedWorkflow:
    @workflow.run
    async def run(self, data: dict) -> dict:
        ...
```

### 3. Track State for Observability
```python
@workflow.defn
class ObservableWorkflow:
    def __init__(self):
        self._status = "starting"
        self._progress = 0
    
    @workflow.run
    async def run(self, data: dict):
        self._status = "processing"
        # ... do work, update _progress
        self._status = "completed"
    
    @workflow.query
    def status(self) -> dict:
        return {"status": self._status, "progress": self._progress}
```

---

## Next Steps

- **temporal-signals-queries.md** - Deep dive into signals and queries
- **temporal-advanced.md** - Saga patterns, child workflows, continue-as-new
- **temporal-workers.md** - Worker configuration and deployment
