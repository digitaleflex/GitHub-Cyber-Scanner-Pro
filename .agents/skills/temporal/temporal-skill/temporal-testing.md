# Temporal Testing Patterns

> **Unit and Integration Testing for Workflows and Activities**  
> Test your Temporal code with confidence using time-skipping and activity mocking.

## Overview

Temporal provides powerful testing utilities that enable:

| Feature | Description |
|---------|-------------|
| **Time Skipping** | Instantly skip timers and sleeps |
| **Activity Mocking** | Replace activities with test doubles |
| **Workflow Testing** | Test complete workflow execution |
| **Determinism Checks** | Verify workflow replay safety |

---

## Setup

### Project Dependencies

```bash
# Add testing dependencies
uv add --dev pytest pytest-asyncio

# Project structure
temporal-project/
├── src/
│   ├── __init__.py
│   ├── activities.py
│   ├── workflows.py
│   └── worker.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_activities.py
│   └── test_workflows.py
└── pyproject.toml
```

### pytest Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

### Test Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

@pytest.fixture
async def workflow_environment():
    """Create a time-skipping workflow environment."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env

@pytest.fixture
async def local_environment():
    """Create a local test environment (no time skipping)."""
    async with await WorkflowEnvironment.start_local() as env:
        yield env
```

---

## Testing Activities

Activities are regular Python functions - test them like any other code.

### Basic Activity Tests

```python
# tests/test_activities.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.activities import (
    send_email, EmailInput,
    call_api, APICallInput,
    process_payment, PaymentInput,
)

class TestSendEmailActivity:
    """Tests for send_email activity."""
    
    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """Test successful email sending."""
        input_data = EmailInput(
            to="user@example.com",
            subject="Test",
            body="Hello"
        )
        
        with patch("src.activities.smtp_client") as mock_smtp:
            mock_smtp.send.return_value = {"message_id": "123"}
            
            result = await send_email(input_data)
            
            assert result.message_id == "123"
            mock_smtp.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_invalid_recipient(self):
        """Test email with invalid recipient."""
        input_data = EmailInput(
            to="invalid-email",
            subject="Test",
            body="Hello"
        )
        
        with pytest.raises(ValueError, match="Invalid email"):
            await send_email(input_data)


class TestAPICallActivity:
    """Tests for call_api activity."""
    
    @pytest.mark.asyncio
    async def test_api_call_success(self):
        """Test successful API call."""
        input_data = APICallInput(
            url="https://api.example.com/data",
            method="GET"
        )
        
        with patch("src.activities.httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": "test"}
            mock_response.elapsed.total_seconds.return_value = 0.1
            
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            result = await call_api(input_data)
            
            assert result.status_code == 200
            assert result.body == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_api_call_timeout(self):
        """Test API call timeout handling."""
        import httpx
        
        input_data = APICallInput(
            url="https://slow-api.example.com",
            method="GET"
        )
        
        with patch("src.activities.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )
            
            with pytest.raises(httpx.TimeoutException):
                await call_api(input_data)
```

### Testing Activities with Heartbeating

```python
# tests/test_activities.py
import pytest
from unittest.mock import patch, MagicMock
from temporalio import activity
from src.activities import process_large_file, FileProcessInput

class TestLongRunningActivity:
    """Tests for activities with heartbeating."""
    
    @pytest.mark.asyncio
    async def test_process_large_file_with_heartbeat(self):
        """Test that heartbeating is called during processing."""
        input_data = FileProcessInput(
            file_path="/tmp/large_file.dat",
            chunk_size=1024
        )
        
        heartbeat_calls = []
        
        def mock_heartbeat(details=None):
            heartbeat_calls.append(details)
        
        with patch.object(activity, "heartbeat", mock_heartbeat):
            with patch("src.activities.read_file_chunks") as mock_read:
                mock_read.return_value = [b"chunk1", b"chunk2", b"chunk3"]
                
                result = await process_large_file(input_data)
                
                assert result.total_chunks == 3
                assert len(heartbeat_calls) >= 3  # At least one heartbeat per chunk
    
    @pytest.mark.asyncio
    async def test_activity_cancellation_cleanup(self):
        """Test that activity cleans up on cancellation."""
        import asyncio
        from src.activities import cancellable_activity
        
        cleanup_called = False
        
        async def mock_cleanup():
            nonlocal cleanup_called
            cleanup_called = True
        
        with patch("src.activities.cleanup", mock_cleanup):
            task = asyncio.create_task(cancellable_activity({}))
            await asyncio.sleep(0.1)
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            assert cleanup_called
```

---

## Testing Workflows

Use Temporal's testing utilities for workflow tests.

### Basic Workflow Tests

```python
# tests/test_workflows.py
import pytest
from datetime import timedelta
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio.client import Client

from src.workflows import GreetingWorkflow
from src.activities import greet, GreetingInput

class TestGreetingWorkflow:
    """Tests for simple GreetingWorkflow."""
    
    @pytest.mark.asyncio
    async def test_greeting_workflow_success(self, workflow_environment):
        """Test basic workflow execution."""
        async with Worker(
            workflow_environment.client,
            task_queue="test-queue",
            workflows=[GreetingWorkflow],
            activities=[greet],
        ):
            result = await workflow_environment.client.execute_workflow(
                GreetingWorkflow.run,
                "World",
                id="test-greeting",
                task_queue="test-queue",
            )
            
            assert result == "Hello, World!"
    
    @pytest.mark.asyncio
    async def test_greeting_workflow_empty_name(self, workflow_environment):
        """Test workflow with empty name."""
        async with Worker(
            workflow_environment.client,
            task_queue="test-queue",
            workflows=[GreetingWorkflow],
            activities=[greet],
        ):
            result = await workflow_environment.client.execute_workflow(
                GreetingWorkflow.run,
                "",
                id="test-greeting-empty",
                task_queue="test-queue",
            )
            
            assert result == "Hello, !"
```

### Testing with Activity Mocking

```python
# tests/test_workflows.py
import pytest
from datetime import timedelta
from temporalio.testing import WorkflowEnvironment, ActivityEnvironment
from temporalio.worker import Worker
from temporalio import activity

from src.workflows import OrderWorkflow
from src.activities import (
    validate_order,
    process_payment,
    send_confirmation,
)

class TestOrderWorkflow:
    """Tests for OrderWorkflow with mocked activities."""
    
    @pytest.mark.asyncio
    async def test_order_workflow_success(self, workflow_environment):
        """Test successful order processing."""
        
        # Mock activities
        @activity.defn(name="validate_order")
        async def mock_validate(order: dict) -> dict:
            return {"is_valid": True}
        
        @activity.defn(name="process_payment")
        async def mock_payment(payment: dict) -> dict:
            return {"transaction_id": "TXN-123", "status": "success"}
        
        @activity.defn(name="send_confirmation")
        async def mock_confirm(data: dict) -> bool:
            return True
        
        async with Worker(
            workflow_environment.client,
            task_queue="test-queue",
            workflows=[OrderWorkflow],
            activities=[mock_validate, mock_payment, mock_confirm],
        ):
            result = await workflow_environment.client.execute_workflow(
                OrderWorkflow.run,
                {"order_id": "ORD-001", "amount": 99.99},
                id="test-order",
                task_queue="test-queue",
            )
            
            assert result["status"] == "completed"
            assert result["transaction_id"] == "TXN-123"
    
    @pytest.mark.asyncio
    async def test_order_workflow_validation_failure(self, workflow_environment):
        """Test order workflow when validation fails."""
        
        @activity.defn(name="validate_order")
        async def mock_validate(order: dict) -> dict:
            return {"is_valid": False, "reason": "Invalid items"}
        
        async with Worker(
            workflow_environment.client,
            task_queue="test-queue",
            workflows=[OrderWorkflow],
            activities=[mock_validate],
        ):
            result = await workflow_environment.client.execute_workflow(
                OrderWorkflow.run,
                {"order_id": "ORD-002", "amount": 0},
                id="test-order-invalid",
                task_queue="test-queue",
            )
            
            assert result["status"] == "failed"
            assert "Invalid items" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_order_workflow_payment_failure(self, workflow_environment):
        """Test order workflow when payment fails."""
        from temporalio.exceptions import ApplicationError
        
        @activity.defn(name="validate_order")
        async def mock_validate(order: dict) -> dict:
            return {"is_valid": True}
        
        @activity.defn(name="process_payment")
        async def mock_payment_fail(payment: dict) -> dict:
            raise ApplicationError("Insufficient funds", type="PaymentError")
        
        async with Worker(
            workflow_environment.client,
            task_queue="test-queue",
            workflows=[OrderWorkflow],
            activities=[mock_validate, mock_payment_fail],
        ):
            with pytest.raises(Exception) as exc_info:
                await workflow_environment.client.execute_workflow(
                    OrderWorkflow.run,
                    {"order_id": "ORD-003", "amount": 999999},
                    id="test-order-payment-fail",
                    task_queue="test-queue",
                )
            
            assert "Insufficient funds" in str(exc_info.value)
```

---

## Testing with Time Skipping

Test workflows with timers without waiting in real-time.

### Timer and Sleep Tests

```python
# tests/test_workflows.py
import pytest
from datetime import timedelta
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio import activity

from src.workflows import ScheduledRemindersWorkflow

class TestTimerWorkflows:
    """Tests for workflows with timers."""
    
    @pytest.mark.asyncio
    async def test_reminder_workflow_sends_reminders(self):
        """Test that reminders are sent after delays."""
        reminders_sent = []
        
        @activity.defn(name="send_reminder")
        async def mock_send_reminder(data: dict) -> bool:
            reminders_sent.append(data)
            return True
        
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[ScheduledRemindersWorkflow],
                activities=[mock_send_reminder],
            ):
                # Start workflow that sends reminders at 1h, 24h, 72h
                handle = await env.client.start_workflow(
                    ScheduledRemindersWorkflow.run,
                    {"user_id": "user-123", "message": "Complete your profile"},
                    id="test-reminders",
                    task_queue="test-queue",
                )
                
                # Wait for workflow to complete (time is skipped)
                result = await handle.result()
                
                assert len(reminders_sent) == 3
                assert result["reminders_sent"] == 3
    
    @pytest.mark.asyncio
    async def test_approval_workflow_timeout(self):
        """Test approval workflow times out correctly."""
        
        @activity.defn(name="send_approval_request")
        async def mock_send_request(data: dict) -> bool:
            return True
        
        @activity.defn(name="handle_timeout")
        async def mock_timeout(data: dict) -> dict:
            return {"action": "escalated"}
        
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[ApprovalWorkflow],
                activities=[mock_send_request, mock_timeout],
            ):
                result = await env.client.execute_workflow(
                    ApprovalWorkflow.run,
                    {"request_id": "REQ-001", "timeout_hours": 24},
                    id="test-approval-timeout",
                    task_queue="test-queue",
                )
                
                # Workflow should timeout (no approval signal sent)
                assert result["status"] == "timed_out"
```

### Testing Signals and Queries

```python
# tests/test_workflows.py
import pytest
import asyncio
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio import activity

from src.workflows import ApprovalWorkflow

class TestSignalsAndQueries:
    """Tests for workflow signals and queries."""
    
    @pytest.mark.asyncio
    async def test_approval_signal(self):
        """Test sending approval signal."""
        
        @activity.defn(name="send_approval_request")
        async def mock_request(data: dict) -> bool:
            return True
        
        @activity.defn(name="execute_approved_action")
        async def mock_execute(data: dict) -> dict:
            return {"executed": True}
        
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[ApprovalWorkflow],
                activities=[mock_request, mock_execute],
            ):
                # Start workflow
                handle = await env.client.start_workflow(
                    ApprovalWorkflow.run,
                    {"request_id": "REQ-002", "timeout_hours": 24},
                    id="test-approval-signal",
                    task_queue="test-queue",
                )
                
                # Query status
                status = await handle.query(ApprovalWorkflow.get_status)
                assert status == "pending"
                
                # Send approval signal
                await handle.signal(ApprovalWorkflow.approve, "admin", "Looks good")
                
                # Wait for result
                result = await handle.result()
                
                assert result["status"] == "approved"
                assert result["approver"] == "admin"
    
    @pytest.mark.asyncio
    async def test_rejection_signal(self):
        """Test sending rejection signal."""
        
        @activity.defn(name="send_approval_request")
        async def mock_request(data: dict) -> bool:
            return True
        
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[ApprovalWorkflow],
                activities=[mock_request],
            ):
                handle = await env.client.start_workflow(
                    ApprovalWorkflow.run,
                    {"request_id": "REQ-003", "timeout_hours": 24},
                    id="test-rejection-signal",
                    task_queue="test-queue",
                )
                
                # Send rejection signal
                await handle.signal(
                    ApprovalWorkflow.reject,
                    "manager",
                    "Budget not approved"
                )
                
                result = await handle.result()
                
                assert result["status"] == "rejected"
                assert "Budget not approved" in result["reason"]
```

---

## Testing Saga Patterns

### Saga Success Test

```python
# tests/test_workflows.py
import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio import activity

from src.workflows import OrderSagaWorkflow, OrderSagaInput

class TestSagaWorkflow:
    """Tests for saga pattern workflow."""
    
    @pytest.fixture
    def order_input(self):
        return OrderSagaInput(
            order_id="ORD-001",
            customer_id="CUST-001",
            items=[{"sku": "ITEM-1", "qty": 2, "price": 29.99}],
            payment_info={"card": "****1234"},
            shipping_address={"city": "Lagos"}
        )
    
    @pytest.mark.asyncio
    async def test_saga_success(self, order_input):
        """Test saga completes successfully."""
        
        @activity.defn(name="reserve_inventory")
        async def mock_reserve(data: dict) -> dict:
            return {"reservation_id": "RES-001"}
        
        @activity.defn(name="charge_payment")
        async def mock_charge(data: dict) -> dict:
            return {"transaction_id": "TXN-001"}
        
        @activity.defn(name="create_shipment")
        async def mock_ship(data: dict) -> dict:
            return {"shipment_id": "SHIP-001", "tracking_id": "TRACK-001"}
        
        @activity.defn(name="send_notification")
        async def mock_notify(data: dict) -> bool:
            return True
        
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[OrderSagaWorkflow],
                activities=[mock_reserve, mock_charge, mock_ship, mock_notify],
            ):
                result = await env.client.execute_workflow(
                    OrderSagaWorkflow.run,
                    order_input,
                    id="test-saga-success",
                    task_queue="test-queue",
                )
                
                assert result["status"] == "success"
                assert result["tracking_id"] == "TRACK-001"
    
    @pytest.mark.asyncio
    async def test_saga_compensation_on_payment_failure(self, order_input):
        """Test saga compensates when payment fails."""
        from temporalio.exceptions import ApplicationError
        
        compensation_calls = []
        
        @activity.defn(name="reserve_inventory")
        async def mock_reserve(data: dict) -> dict:
            return {"reservation_id": "RES-001"}
        
        @activity.defn(name="charge_payment")
        async def mock_charge_fail(data: dict) -> dict:
            raise ApplicationError("Card declined", type="PaymentError")
        
        @activity.defn(name="release_inventory")
        async def mock_release(data: dict) -> bool:
            compensation_calls.append("release_inventory")
            return True
        
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[OrderSagaWorkflow],
                activities=[mock_reserve, mock_charge_fail, mock_release],
            ):
                result = await env.client.execute_workflow(
                    OrderSagaWorkflow.run,
                    order_input,
                    id="test-saga-compensation",
                    task_queue="test-queue",
                )
                
                assert result["status"] == "failed"
                assert "release_inventory" in compensation_calls
    
    @pytest.mark.asyncio
    async def test_saga_compensation_on_shipment_failure(self, order_input):
        """Test saga compensates all steps when shipment fails."""
        from temporalio.exceptions import ApplicationError
        
        compensation_calls = []
        
        @activity.defn(name="reserve_inventory")
        async def mock_reserve(data: dict) -> dict:
            return {"reservation_id": "RES-001"}
        
        @activity.defn(name="charge_payment")
        async def mock_charge(data: dict) -> dict:
            return {"transaction_id": "TXN-001"}
        
        @activity.defn(name="create_shipment")
        async def mock_ship_fail(data: dict) -> dict:
            raise ApplicationError("No carriers available", type="ShipmentError")
        
        @activity.defn(name="refund_payment")
        async def mock_refund(data: dict) -> bool:
            compensation_calls.append("refund_payment")
            return True
        
        @activity.defn(name="release_inventory")
        async def mock_release(data: dict) -> bool:
            compensation_calls.append("release_inventory")
            return True
        
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[OrderSagaWorkflow],
                activities=[
                    mock_reserve, mock_charge, mock_ship_fail,
                    mock_refund, mock_release
                ],
            ):
                result = await env.client.execute_workflow(
                    OrderSagaWorkflow.run,
                    order_input,
                    id="test-saga-full-compensation",
                    task_queue="test-queue",
                )
                
                assert result["status"] == "failed"
                assert "refund_payment" in compensation_calls
                assert "release_inventory" in compensation_calls
```

---

## Testing Child Workflows

```python
# tests/test_workflows.py
import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio import activity

from src.workflows import ParentWorkflow, ChildWorkflow

class TestChildWorkflows:
    """Tests for parent/child workflow patterns."""
    
    @pytest.mark.asyncio
    async def test_parent_child_workflow(self):
        """Test parent workflow orchestrating children."""
        
        @activity.defn(name="child_activity")
        async def mock_child_activity(data: dict) -> dict:
            return {"processed": data["id"]}
        
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[ParentWorkflow, ChildWorkflow],
                activities=[mock_child_activity],
            ):
                result = await env.client.execute_workflow(
                    ParentWorkflow.run,
                    {"items": ["a", "b", "c"]},
                    id="test-parent",
                    task_queue="test-queue",
                )
                
                assert result["total_processed"] == 3
    
    @pytest.mark.asyncio
    async def test_parallel_child_workflows(self):
        """Test parallel child workflow execution."""
        processed_ids = []
        
        @activity.defn(name="process_item")
        async def mock_process(data: dict) -> dict:
            processed_ids.append(data["id"])
            return {"id": data["id"], "status": "done"}
        
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[BatchParentWorkflow, ItemWorkflow],
                activities=[mock_process],
            ):
                result = await env.client.execute_workflow(
                    BatchParentWorkflow.run,
                    {"batch_size": 5, "item_ids": list(range(10))},
                    id="test-batch-parent",
                    task_queue="test-queue",
                )
                
                assert len(processed_ids) == 10
                assert result["batches_completed"] == 2
```

---

## Integration Testing

Test against a real Temporal server.

### Local Environment Tests

```python
# tests/test_integration.py
import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from src.workflows import RealWorkflow
from src.activities import real_activity

@pytest.fixture
async def local_env():
    """Use local environment for integration tests."""
    async with await WorkflowEnvironment.start_local() as env:
        yield env

class TestIntegration:
    """Integration tests with real activities."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_workflow_integration(self, local_env):
        """Test workflow with real activities."""
        async with Worker(
            local_env.client,
            task_queue="integration-queue",
            workflows=[RealWorkflow],
            activities=[real_activity],
        ):
            result = await local_env.client.execute_workflow(
                RealWorkflow.run,
                {"test": True},
                id="integration-test",
                task_queue="integration-queue",
            )
            
            assert result["status"] == "success"
```

### Testing Against External Server

```python
# tests/test_e2e.py
import pytest
import os
from temporalio.client import Client
from temporalio.worker import Worker

from src.workflows import ProductionWorkflow
from src.activities import production_activity

@pytest.fixture
async def temporal_client():
    """Connect to external Temporal server."""
    client = await Client.connect(
        os.getenv("TEMPORAL_ADDRESS", "localhost:7233"),
        namespace=os.getenv("TEMPORAL_NAMESPACE", "default"),
    )
    yield client

class TestE2E:
    """End-to-end tests against real server."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_e2e_workflow(self, temporal_client):
        """Full end-to-end test."""
        async with Worker(
            temporal_client,
            task_queue="e2e-queue",
            workflows=[ProductionWorkflow],
            activities=[production_activity],
        ):
            result = await temporal_client.execute_workflow(
                ProductionWorkflow.run,
                {"mode": "test"},
                id=f"e2e-test-{uuid4()}",
                task_queue="e2e-queue",
            )
            
            assert result["completed"] is True
```

---

## Test Organization

### Markers and Categories

```python
# conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run only unit tests
uv run pytest -m unit

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_workflows.py

# Run specific test
uv run pytest tests/test_workflows.py::TestOrderWorkflow::test_order_workflow_success

# Verbose output
uv run pytest -v

# Run in parallel
uv run pytest -n auto
```

---

## Best Practices

### Testing Guidelines

1. **Use time-skipping environment** for workflows with timers
2. **Mock activities** to isolate workflow logic
3. **Test compensation paths** for saga patterns
4. **Verify query results** at different workflow states
5. **Test signal handling** with various timing
6. **Use fixtures** for common setup

### Test Structure

```python
class TestMyWorkflow:
    """Tests for MyWorkflow."""
    
    # Fixtures for common data
    @pytest.fixture
    def valid_input(self):
        return MyInput(...)
    
    # Happy path tests
    @pytest.mark.asyncio
    async def test_success_path(self, workflow_environment, valid_input):
        ...
    
    # Error handling tests
    @pytest.mark.asyncio
    async def test_activity_failure_handling(self, workflow_environment):
        ...
    
    # Edge case tests
    @pytest.mark.asyncio
    async def test_empty_input(self, workflow_environment):
        ...
    
    # Signal/Query tests
    @pytest.mark.asyncio
    async def test_query_returns_correct_status(self, workflow_environment):
        ...
```

---

## CLI Test Commands

```bash
# Run pytest with temporal test output
uv run pytest -v --tb=short

# Run with specific markers
uv run pytest -m "not slow"

# Generate test coverage report
uv run pytest --cov=src --cov-report=term-missing

# Run tests in watch mode (requires pytest-watch)
uv run ptw tests/
```

---

**Next:** Return to **SKILL.md** for the complete skill reference.
