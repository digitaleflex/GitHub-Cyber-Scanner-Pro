# Temporal Advanced Patterns

> **Saga Patterns, Child Workflows, Continue-as-New, and Versioning**  
> Production-grade patterns for complex distributed workflows.

## Overview

This module covers advanced Temporal patterns for building enterprise-grade distributed systems:

| Pattern | Use Case | Key Benefit |
|---------|----------|-------------|
| **Saga** | Multi-step transactions with rollback | Guaranteed compensation on failure |
| **Child Workflows** | Parallel/modular workflow execution | Isolation and reusability |
| **Continue-as-New** | Long-running processes | Prevent history growth |
| **Versioning** | Safe workflow updates | Non-breaking changes |

---

## Saga Pattern

The Saga pattern ensures that if any step fails, all previously completed steps are compensated (rolled back).

### Basic Saga Implementation

```python
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError, ApplicationError
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any
from datetime import timedelta

with workflow.unsafe.imports_passed_through():
    from .activities import (
        reserve_inventory, release_inventory,
        charge_payment, refund_payment,
        create_shipment, cancel_shipment,
        send_notification,
    )

@dataclass
class SagaStep:
    """Tracks a saga step and its compensation."""
    name: str
    completed: bool = False
    result: Optional[dict] = None
    compensated: bool = False
    compensation_error: Optional[str] = None

@dataclass
class OrderSagaInput:
    order_id: str
    customer_id: str
    items: List[dict]
    payment_info: dict
    shipping_address: dict

@workflow.defn
class OrderSagaWorkflow:
    """
    Saga pattern for order processing.
    
    Steps:
    1. Reserve inventory
    2. Charge payment
    3. Create shipment
    
    Each step has a compensating action that runs on failure.
    """
    
    def __init__(self):
        self._steps: List[SagaStep] = []
        self._status = "pending"
        self._compensation_errors: List[str] = []
    
    @workflow.run
    async def run(self, order: OrderSagaInput) -> dict:
        try:
            # Step 1: Reserve Inventory
            inventory = await self._execute_step(
                name="reserve_inventory",
                activity=reserve_inventory,
                args={"order_id": order.order_id, "items": order.items},
            )
            
            # Step 2: Charge Payment
            payment = await self._execute_step(
                name="charge_payment",
                activity=charge_payment,
                args={
                    "order_id": order.order_id,
                    "amount": sum(item["price"] * item["qty"] for item in order.items),
                    "payment_info": order.payment_info
                },
            )
            
            # Step 3: Create Shipment
            shipment = await self._execute_step(
                name="create_shipment",
                activity=create_shipment,
                args={
                    "order_id": order.order_id,
                    "items": order.items,
                    "address": order.shipping_address,
                    "reservation_id": inventory["reservation_id"]
                },
            )
            
            # Step 4: Notification (non-critical, no compensation)
            try:
                await workflow.execute_activity(
                    send_notification,
                    {
                        "customer_id": order.customer_id,
                        "message": f"Order {order.order_id} confirmed!"
                    },
                    start_to_close_timeout=timedelta(seconds=30),
                )
            except ActivityError:
                workflow.logger.warning("Notification failed, but order succeeded")
            
            self._status = "completed"
            return {
                "status": "success",
                "order_id": order.order_id,
                "tracking_id": shipment.get("tracking_id"),
                "transaction_id": payment.get("transaction_id"),
            }
        
        except ActivityError as e:
            self._status = "compensating"
            workflow.logger.error(f"Saga failed, starting compensation: {e}")
            
            await self._compensate(order)
            
            self._status = "failed"
            return {
                "status": "failed",
                "order_id": order.order_id,
                "error": str(e),
                "steps_completed": [s.name for s in self._steps if s.completed],
                "steps_compensated": [s.name for s in self._steps if s.compensated],
                "compensation_errors": self._compensation_errors,
            }
    
    async def _execute_step(
        self, 
        name: str, 
        activity: Callable, 
        args: dict,
        timeout: timedelta = timedelta(minutes=2)
    ) -> dict:
        """Execute a saga step and track it."""
        step = SagaStep(name=name)
        self._steps.append(step)
        
        result = await workflow.execute_activity(
            activity,
            args,
            start_to_close_timeout=timeout,
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        
        step.completed = True
        step.result = result
        return result
    
    async def _compensate(self, order: OrderSagaInput):
        """Run compensating actions in reverse order."""
        compensation_map = {
            "create_shipment": (
                cancel_shipment,
                lambda s: {"shipment_id": s.result.get("shipment_id")}
            ),
            "charge_payment": (
                refund_payment,
                lambda s: {"transaction_id": s.result.get("transaction_id")}
            ),
            "reserve_inventory": (
                release_inventory,
                lambda s: {"reservation_id": s.result.get("reservation_id")}
            ),
        }
        
        # Compensate in REVERSE order
        for step in reversed(self._steps):
            if step.completed and not step.compensated:
                if step.name in compensation_map:
                    activity, get_args = compensation_map[step.name]
                    try:
                        await workflow.execute_activity(
                            activity,
                            get_args(step),
                            start_to_close_timeout=timedelta(minutes=2),
                            retry_policy=RetryPolicy(maximum_attempts=5),  # More retries for compensation
                        )
                        step.compensated = True
                        workflow.logger.info(f"Compensated: {step.name}")
                    except ActivityError as e:
                        step.compensation_error = str(e)
                        self._compensation_errors.append(f"{step.name}: {e}")
                        workflow.logger.error(f"Compensation failed for {step.name}: {e}")
    
    @workflow.query
    def get_status(self) -> str:
        return self._status
    
    @workflow.query
    def get_steps(self) -> List[dict]:
        return [
            {
                "name": s.name,
                "completed": s.completed,
                "compensated": s.compensated,
                "compensation_error": s.compensation_error
            }
            for s in self._steps
        ]
```

### Saga with Parallel Steps

```python
import asyncio

@workflow.defn
class ParallelSagaWorkflow:
    """Saga with some steps running in parallel."""
    
    def __init__(self):
        self._completed_steps: dict = {}
    
    @workflow.run
    async def run(self, order: dict) -> dict:
        try:
            # Step 1: Parallel validations
            validation_results = await asyncio.gather(
                workflow.execute_activity(
                    validate_inventory,
                    order,
                    start_to_close_timeout=timedelta(seconds=30),
                ),
                workflow.execute_activity(
                    validate_payment_method,
                    order,
                    start_to_close_timeout=timedelta(seconds=30),
                ),
                workflow.execute_activity(
                    validate_shipping_address,
                    order,
                    start_to_close_timeout=timedelta(seconds=30),
                ),
            )
            
            # All validations passed
            self._completed_steps["validations"] = validation_results
            
            # Step 2: Sequential critical operations
            reserve_result = await workflow.execute_activity(
                reserve_inventory,
                order,
                start_to_close_timeout=timedelta(minutes=1),
            )
            self._completed_steps["reserve"] = reserve_result
            
            payment_result = await workflow.execute_activity(
                process_payment,
                order,
                start_to_close_timeout=timedelta(minutes=1),
            )
            self._completed_steps["payment"] = payment_result
            
            return {"status": "success", "steps": self._completed_steps}
            
        except ActivityError as e:
            await self._compensate()
            raise
    
    async def _compensate(self):
        # Compensate in reverse order of completion
        if "payment" in self._completed_steps:
            await workflow.execute_activity(
                refund_payment,
                self._completed_steps["payment"],
                start_to_close_timeout=timedelta(minutes=2),
            )
        if "reserve" in self._completed_steps:
            await workflow.execute_activity(
                release_inventory,
                self._completed_steps["reserve"],
                start_to_close_timeout=timedelta(minutes=2),
            )
```

---

## Child Workflows

Child workflows provide isolation, reusability, and separate failure domains.

### Starting Child Workflows

```python
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import List

@workflow.defn
class ParentWorkflow:
    @workflow.run
    async def run(self, order_ids: List[str]) -> dict:
        results = []
        
        # Start child workflows sequentially
        for order_id in order_ids:
            result = await workflow.execute_child_workflow(
                OrderProcessingWorkflow.run,
                order_id,
                id=f"order-{order_id}",
                task_queue="order-queue",
                # Child workflow options
                execution_timeout=timedelta(hours=1),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            results.append(result)
        
        return {"processed": len(results), "results": results}
```

### Parallel Child Workflows with Batching

```python
import asyncio
from dataclasses import dataclass
from typing import List

@dataclass
class OrderInput:
    order_id: str
    customer_id: str
    items: List[dict]

@workflow.defn
class BatchOrderWorkflow:
    """Process orders in parallel batches."""
    
    @workflow.run
    async def run(self, orders: List[OrderInput]) -> dict:
        batch_size = 10
        all_results = []
        failed_orders = []
        
        for i in range(0, len(orders), batch_size):
            batch = orders[i:i + batch_size]
            
            # Start all child workflows in batch
            handles = []
            for order in batch:
                handle = await workflow.start_child_workflow(
                    OrderSagaWorkflow.run,
                    order,
                    id=f"order-saga-{order.order_id}",
                    task_queue="order-queue",
                )
                handles.append((order.order_id, handle))
            
            # Wait for all in batch
            batch_results = await asyncio.gather(
                *[h.result() for _, h in handles],
                return_exceptions=True
            )
            
            # Collect results
            for (order_id, _), result in zip(handles, batch_results):
                if isinstance(result, Exception):
                    failed_orders.append({
                        "order_id": order_id,
                        "error": str(result)
                    })
                else:
                    all_results.append(result)
        
        return {
            "total": len(orders),
            "successful": len(all_results),
            "failed": len(failed_orders),
            "failures": failed_orders
        }
```

### Child Workflow with Parent Cancellation

```python
from temporalio.workflow import ParentClosePolicy

@workflow.defn
class ParentWithChildPolicies:
    @workflow.run
    async def run(self, data: dict) -> dict:
        # Child that terminates when parent closes
        critical_handle = await workflow.start_child_workflow(
            CriticalWorkflow.run,
            data,
            id="critical-child",
            parent_close_policy=ParentClosePolicy.TERMINATE,
        )
        
        # Child that continues when parent closes
        background_handle = await workflow.start_child_workflow(
            BackgroundWorkflow.run,
            data,
            id="background-child",
            parent_close_policy=ParentClosePolicy.ABANDON,
        )
        
        # Wait only for critical child
        critical_result = await critical_handle.result()
        
        return {
            "critical_result": critical_result,
            "background_id": background_handle.id
        }
```

### Signaling Child Workflows

```python
@workflow.defn
class CoordinatorWorkflow:
    @workflow.run
    async def run(self, num_workers: int) -> dict:
        # Start worker child workflows
        workers = []
        for i in range(num_workers):
            handle = await workflow.start_child_workflow(
                WorkerWorkflow.run,
                i,
                id=f"worker-{i}",
            )
            workers.append(handle)
        
        # Distribute work via signals
        work_items = await workflow.execute_activity(
            get_work_items,
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        for i, item in enumerate(work_items):
            worker_idx = i % num_workers
            await workers[worker_idx].signal(
                WorkerWorkflow.assign_work,
                item
            )
        
        # Signal all workers to complete
        for worker in workers:
            await worker.signal(WorkerWorkflow.complete)
        
        # Collect results
        results = await asyncio.gather(*[w.result() for w in workers])
        
        return {"workers": num_workers, "results": results}

@workflow.defn
class WorkerWorkflow:
    def __init__(self):
        self._work_items = []
        self._should_complete = False
    
    @workflow.run
    async def run(self, worker_id: int) -> dict:
        await workflow.wait_condition(lambda: self._should_complete)
        
        # Process all assigned work
        results = []
        for item in self._work_items:
            result = await workflow.execute_activity(
                process_work_item,
                item,
                start_to_close_timeout=timedelta(minutes=5),
            )
            results.append(result)
        
        return {"worker_id": worker_id, "processed": len(results)}
    
    @workflow.signal
    async def assign_work(self, item: dict):
        self._work_items.append(item)
    
    @workflow.signal
    async def complete(self):
        self._should_complete = True
```

---

## Continue-as-New

Use continue-as-new to prevent workflow history from growing indefinitely in long-running processes.

### Basic Continue-as-New

```python
@workflow.defn
class LongRunningWorkflow:
    """Workflow that processes items indefinitely."""
    
    def __init__(self):
        self._items_processed = 0
        self._should_stop = False
    
    @workflow.run
    async def run(self, state: dict) -> dict:
        iteration = state.get("iteration", 0)
        total_processed = state.get("total_processed", 0)
        max_iterations = 100  # Limit events per run
        
        for i in range(max_iterations):
            if self._should_stop:
                return {
                    "status": "stopped",
                    "total_processed": total_processed + self._items_processed
                }
            
            # Check for more work
            has_work = await workflow.execute_activity(
                check_for_work,
                start_to_close_timeout=timedelta(seconds=10),
            )
            
            if not has_work:
                # No work, wait and continue
                await asyncio.sleep(60)  # Wait 1 minute
                continue
            
            # Process item
            await workflow.execute_activity(
                process_item,
                start_to_close_timeout=timedelta(minutes=5),
            )
            self._items_processed += 1
        
        # Continue as new to reset history
        workflow.continue_as_new({
            "iteration": iteration + 1,
            "total_processed": total_processed + self._items_processed
        })
    
    @workflow.signal
    async def stop(self):
        self._should_stop = True
    
    @workflow.query
    def get_progress(self) -> dict:
        return {"items_this_run": self._items_processed}
```

### Continue-as-New with State Preservation

```python
from dataclasses import dataclass, asdict
from typing import List, Optional

@dataclass
class WorkflowState:
    iteration: int = 0
    total_processed: int = 0
    cursor: Optional[str] = None
    pending_items: List[str] = None
    
    def __post_init__(self):
        if self.pending_items is None:
            self.pending_items = []

@workflow.defn
class StatefulLongRunningWorkflow:
    """Long-running workflow with preserved state."""
    
    MAX_HISTORY_EVENTS = 1000
    
    @workflow.run
    async def run(self, state_dict: dict) -> dict:
        state = WorkflowState(**state_dict) if state_dict else WorkflowState()
        events_this_run = 0
        
        while True:
            # Check if we need to continue-as-new
            info = workflow.info()
            if info.get_current_history_length() > self.MAX_HISTORY_EVENTS:
                workflow.continue_as_new(asdict(state))
            
            # Fetch next batch
            batch = await workflow.execute_activity(
                fetch_batch,
                {"cursor": state.cursor, "limit": 100},
                start_to_close_timeout=timedelta(minutes=1),
            )
            events_this_run += 1
            
            if not batch["items"]:
                # No more items
                return {
                    "status": "completed",
                    "iterations": state.iteration,
                    "total_processed": state.total_processed
                }
            
            # Process batch
            for item in batch["items"]:
                await workflow.execute_activity(
                    process_item,
                    item,
                    start_to_close_timeout=timedelta(minutes=5),
                )
                state.total_processed += 1
                events_this_run += 1
            
            state.cursor = batch.get("next_cursor")
            state.iteration += 1
```

### Event-Driven Continue-as-New

```python
@workflow.defn
class EventProcessorWorkflow:
    """Process events continuously with automatic continuation."""
    
    def __init__(self):
        self._events: List[dict] = []
        self._shutdown = False
    
    @workflow.run
    async def run(self, state: dict) -> dict:
        processed = state.get("total_processed", 0)
        events_this_run = 0
        max_events = 500
        
        while not self._shutdown and events_this_run < max_events:
            # Wait for events or timeout
            try:
                await workflow.wait_condition(
                    lambda: len(self._events) > 0 or self._shutdown,
                    timeout=timedelta(minutes=5)
                )
            except TimeoutError:
                # Periodic maintenance
                await workflow.execute_activity(
                    heartbeat,
                    start_to_close_timeout=timedelta(seconds=10),
                )
                continue
            
            if self._shutdown:
                break
            
            # Process accumulated events
            while self._events and events_this_run < max_events:
                event = self._events.pop(0)
                await workflow.execute_activity(
                    process_event,
                    event,
                    start_to_close_timeout=timedelta(minutes=1),
                )
                processed += 1
                events_this_run += 1
        
        if self._shutdown:
            return {"status": "shutdown", "total_processed": processed}
        
        # Continue as new
        workflow.continue_as_new({"total_processed": processed})
    
    @workflow.signal
    async def send_event(self, event: dict):
        self._events.append(event)
    
    @workflow.signal
    async def shutdown(self):
        self._shutdown = True
```

---

## Workflow Versioning

Handle workflow code changes safely without breaking running workflows.

### Basic Versioning with workflow.patched

```python
@workflow.defn
class VersionedWorkflow:
    @workflow.run
    async def run(self, order: dict) -> dict:
        # Original logic
        validated = await workflow.execute_activity(
            validate_order,
            order,
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        # Version 2: Added fraud check
        if workflow.patched("add-fraud-check"):
            fraud_result = await workflow.execute_activity(
                check_fraud,
                order,
                start_to_close_timeout=timedelta(seconds=30),
            )
            if fraud_result["is_fraud"]:
                return {"status": "rejected", "reason": "fraud_detected"}
        
        # Continue with processing
        result = await workflow.execute_activity(
            process_order,
            order,
            start_to_close_timeout=timedelta(minutes=2),
        )
        
        # Version 3: Added loyalty points
        if workflow.patched("add-loyalty-points"):
            await workflow.execute_activity(
                award_loyalty_points,
                {"order_id": order["id"], "amount": order["total"]},
                start_to_close_timeout=timedelta(seconds=30),
            )
        
        return result
```

### Using workflow.deprecate_patch

```python
@workflow.defn
class DeprecatedPatchWorkflow:
    @workflow.run
    async def run(self, data: dict) -> dict:
        # Old workflows will skip this check
        # New workflows will always run it
        # Eventually remove when all old workflows complete
        if workflow.deprecate_patch("old-validation"):
            pass  # Old validation removed
        
        # New validation always runs
        await workflow.execute_activity(
            new_validation,
            data,
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        return {"status": "success"}
```

### Versioning with Multiple Changes

```python
@workflow.defn
class MultiVersionWorkflow:
    @workflow.run
    async def run(self, order: dict) -> dict:
        # Version 1: Basic flow
        result = await workflow.execute_activity(
            process_v1,
            order,
            start_to_close_timeout=timedelta(minutes=2),
        )
        
        # Version 2 (2024-01): Added analytics
        if workflow.patched("v2-analytics-2024-01"):
            await workflow.execute_activity(
                send_analytics,
                result,
                start_to_close_timeout=timedelta(seconds=30),
            )
        
        # Version 3 (2024-03): Changed notification logic
        if workflow.patched("v3-notification-2024-03"):
            await workflow.execute_activity(
                send_notification_v2,  # New notification logic
                result,
                start_to_close_timeout=timedelta(seconds=30),
            )
        else:
            await workflow.execute_activity(
                send_notification_v1,  # Original notification
                result,
                start_to_close_timeout=timedelta(seconds=30),
            )
        
        return result
```

---

## Multi-Agent Orchestration

Coordinate multiple AI agents or services using Temporal.

```python
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import timedelta

@dataclass
class AgentTask:
    agent_id: str
    task_type: str
    input_data: dict
    dependencies: List[str] = None

@dataclass
class AgentResult:
    agent_id: str
    output: dict
    success: bool
    error: Optional[str] = None

@workflow.defn
class MultiAgentOrchestrator:
    """Orchestrate multiple AI agents with dependencies."""
    
    def __init__(self):
        self._results: Dict[str, AgentResult] = {}
        self._status = "pending"
    
    @workflow.run
    async def run(self, tasks: List[AgentTask]) -> dict:
        self._status = "running"
        
        # Build dependency graph
        pending = {t.agent_id: t for t in tasks}
        completed = set()
        
        while pending:
            # Find tasks with satisfied dependencies
            ready = [
                task for task in pending.values()
                if not task.dependencies or all(d in completed for d in task.dependencies)
            ]
            
            if not ready:
                raise ApplicationError("Circular dependency detected")
            
            # Execute ready tasks in parallel
            handles = []
            for task in ready:
                # Enrich input with dependency outputs
                enriched_input = self._enrich_input(task)
                
                handle = await workflow.start_child_workflow(
                    AgentExecutorWorkflow.run,
                    {"agent_id": task.agent_id, "task_type": task.task_type, "input": enriched_input},
                    id=f"agent-{task.agent_id}-{workflow.uuid4()}",
                    task_queue=f"agent-{task.agent_id}-queue",
                )
                handles.append((task.agent_id, handle))
            
            # Wait for all ready tasks
            results = await asyncio.gather(
                *[h.result() for _, h in handles],
                return_exceptions=True
            )
            
            # Process results
            for (agent_id, _), result in zip(handles, results):
                if isinstance(result, Exception):
                    self._results[agent_id] = AgentResult(
                        agent_id=agent_id,
                        output={},
                        success=False,
                        error=str(result)
                    )
                else:
                    self._results[agent_id] = AgentResult(
                        agent_id=agent_id,
                        output=result,
                        success=True
                    )
                
                completed.add(agent_id)
                del pending[agent_id]
        
        self._status = "completed"
        return {
            "status": "completed",
            "results": {k: v.__dict__ for k, v in self._results.items()}
        }
    
    def _enrich_input(self, task: AgentTask) -> dict:
        """Add dependency outputs to task input."""
        enriched = dict(task.input_data)
        if task.dependencies:
            enriched["dependency_outputs"] = {
                dep: self._results[dep].output
                for dep in task.dependencies
                if dep in self._results
            }
        return enriched
    
    @workflow.query
    def get_status(self) -> dict:
        return {
            "status": self._status,
            "completed_agents": list(self._results.keys())
        }

@workflow.defn
class AgentExecutorWorkflow:
    """Execute a single agent task."""
    
    @workflow.run
    async def run(self, task: dict) -> dict:
        agent_id = task["agent_id"]
        task_type = task["task_type"]
        input_data = task["input"]
        
        # Route to appropriate agent activity
        if task_type == "analyze":
            return await workflow.execute_activity(
                run_analysis_agent,
                {"agent_id": agent_id, "input": input_data},
                start_to_close_timeout=timedelta(minutes=10),
                heartbeat_timeout=timedelta(seconds=30),
            )
        elif task_type == "generate":
            return await workflow.execute_activity(
                run_generation_agent,
                {"agent_id": agent_id, "input": input_data},
                start_to_close_timeout=timedelta(minutes=15),
                heartbeat_timeout=timedelta(seconds=30),
            )
        else:
            return await workflow.execute_activity(
                run_generic_agent,
                {"agent_id": agent_id, "type": task_type, "input": input_data},
                start_to_close_timeout=timedelta(minutes=5),
            )
```

---

## Determinism Rules

Workflows MUST be deterministic. These rules are critical for replay.

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
os.environ.get("MY_VAR")  # Can change

import requests
requests.get("https://api.example.com")  # Side effect

threading.Thread(...)  # Don't use threads
multiprocessing.Process(...)  # Don't use multiprocessing
```

### DO Use These Alternatives

```python
# GOOD - Deterministic alternatives

# Current time
current_time = workflow.now()

# UUIDs
my_uuid = workflow.uuid4()

# Random values - use activity
random_val = await workflow.execute_activity(
    generate_random,
    start_to_close_timeout=timedelta(seconds=5),
)

# API calls - use activity
result = await workflow.execute_activity(
    call_api,
    {"url": "https://api.example.com"},
    start_to_close_timeout=timedelta(seconds=30),
)

# Environment variables - pass as workflow input
@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, config: dict) -> dict:
        api_key = config["api_key"]  # From input
```

### Safe Imports

```python
# Import non-workflow modules safely
with workflow.unsafe.imports_passed_through():
    from .activities import my_activity
    from .models import MyDataClass
    from pydantic import BaseModel
```

---

## Error Handling Patterns

### Comprehensive Error Handling

```python
from temporalio.exceptions import (
    ApplicationError,
    ActivityError,
    ChildWorkflowError,
    CancelledError,
)

@workflow.defn
class RobustWorkflow:
    @workflow.run
    async def run(self, input: dict) -> dict:
        try:
            result = await workflow.execute_activity(
                risky_activity,
                input,
                start_to_close_timeout=timedelta(minutes=5),
            )
            return {"status": "success", "result": result}
            
        except ActivityError as e:
            # Activity failed after all retries
            workflow.logger.error(f"Activity failed: {e}")
            
            # Check specific error types
            if e.cause and isinstance(e.cause, ApplicationError):
                if e.cause.type == "InsufficientFundsError":
                    return {"status": "insufficient_funds"}
                elif e.cause.type == "InvalidInputError":
                    return {"status": "invalid_input", "error": str(e.cause)}
            
            # Alert on unexpected failures
            await workflow.execute_activity(
                send_alert,
                {"error": str(e), "workflow_id": workflow.info().workflow_id},
                start_to_close_timeout=timedelta(seconds=30),
            )
            raise
            
        except CancelledError:
            workflow.logger.info("Workflow cancelled")
            await self._cleanup()
            raise
            
        except Exception as e:
            workflow.logger.error(f"Unexpected error: {e}")
            raise ApplicationError(
                f"Workflow failed: {str(e)}",
                type="UnexpectedError",
                non_retryable=True,
            )
```

---

## CLI Reference

```bash
# Child workflow operations
temporal workflow list --query "ParentWorkflowId='parent-123'"

# Check workflow history size
temporal workflow show --workflow-id ID --output json | jq '.events | length'

# Reset stuck workflow
temporal workflow reset \
  --workflow-id ID \
  --event-id 10 \
  --reason "Reset after fix"

# Terminate workflow tree
temporal workflow terminate --workflow-id parent-123 --reason "Cleanup"
```

---

**Next:** See **temporal-testing.md** for unit and integration testing patterns.
