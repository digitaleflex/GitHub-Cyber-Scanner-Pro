# RPA Workflow Orchestration Module

Multi-step workflow orchestration with state management, checkpoints, parallel execution, and integration with workflow engines like Prefect and Temporal.

## Workflow Patterns

### Sequential Workflow

```python
#!/usr/bin/env python3
"""Sequential workflow automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
from datetime import datetime
import json
import structlog

log = structlog.get_logger()


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"


@dataclass
class WorkflowStep:
    """Single workflow step."""
    name: str
    action: Callable
    depends_on: list[str] = field(default_factory=list)
    retry_count: int = 3
    timeout_seconds: int = 300
    skip_on_failure: bool = False
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class WorkflowContext:
    """Shared context between steps."""
    data: dict = field(default_factory=dict)
    page: Optional[Page] = None
    
    def set(self, key: str, value: Any):
        self.data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


class SequentialWorkflow:
    """Execute steps in sequence."""
    
    def __init__(self, name: str):
        self.name = name
        self.steps: list[WorkflowStep] = []
        self.context = WorkflowContext()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
    
    def add_step(
        self,
        name: str,
        action: Callable,
        depends_on: list[str] = None,
        retry_count: int = 3,
        timeout_seconds: int = 300,
        skip_on_failure: bool = False
    ) -> "SequentialWorkflow":
        """Add step to workflow."""
        step = WorkflowStep(
            name=name,
            action=action,
            depends_on=depends_on or [],
            retry_count=retry_count,
            timeout_seconds=timeout_seconds,
            skip_on_failure=skip_on_failure
        )
        self.steps.append(step)
        return self
    
    def _run_step(self, step: WorkflowStep) -> bool:
        """Execute single step with retry."""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        for attempt in range(1, step.retry_count + 1):
            try:
                log.info("step_running", step=step.name, attempt=attempt)
                step.result = step.action(self.context)
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now()
                log.info("step_completed", step=step.name)
                return True
            except Exception as e:
                step.error = str(e)
                log.warning("step_failed", step=step.name, attempt=attempt, error=str(e))
                
                if attempt < step.retry_count:
                    step.status = StepStatus.RETRY
                else:
                    step.status = StepStatus.FAILED
                    step.completed_at = datetime.now()
                    return False
        
        return False
    
    def run(self, page: Page = None) -> bool:
        """Execute workflow."""
        self.context.page = page
        self.started_at = datetime.now()
        log.info("workflow_started", name=self.name)
        
        success = True
        
        for step in self.steps:
            # Check dependencies
            deps_met = all(
                self._get_step(d).status == StepStatus.COMPLETED
                for d in step.depends_on
            )
            
            if not deps_met:
                step.status = StepStatus.SKIPPED
                log.warning("step_skipped", step=step.name, reason="dependencies not met")
                continue
            
            if not self._run_step(step):
                if step.skip_on_failure:
                    log.warning("step_failed_skipping", step=step.name)
                    continue
                else:
                    success = False
                    break
        
        self.completed_at = datetime.now()
        duration = self.completed_at - self.started_at
        
        if success:
            log.info("workflow_completed", name=self.name, duration=str(duration))
        else:
            log.error("workflow_failed", name=self.name, duration=str(duration))
        
        return success
    
    def _get_step(self, name: str) -> Optional[WorkflowStep]:
        for step in self.steps:
            if step.name == name:
                return step
        return None
    
    def get_report(self) -> dict:
        """Get workflow execution report."""
        return {
            "name": self.name,
            "status": "completed" if all(s.status == StepStatus.COMPLETED for s in self.steps) else "failed",
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": str(self.completed_at - self.started_at) if self.completed_at and self.started_at else None,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "error": s.error,
                    "duration": str(s.completed_at - s.started_at) if s.completed_at and s.started_at else None
                }
                for s in self.steps
            ]
        }


def example_sequential_workflow():
    """Example: Data extraction workflow."""
    
    def login(ctx: WorkflowContext):
        page = ctx.page
        page.goto("https://example.com/login")
        page.fill("#username", ctx.get("username", "demo"))
        page.fill("#password", ctx.get("password", "demo"))
        page.click("button[type=submit]")
        page.wait_for_url("**/dashboard**")
        return True
    
    def extract_data(ctx: WorkflowContext):
        page = ctx.page
        page.click("a[href='/reports']")
        page.wait_for_selector(".reports-table")
        
        data = []
        for row in page.locator(".reports-table tbody tr").all():
            data.append({
                "name": row.locator("td:nth-child(1)").text_content(),
                "value": row.locator("td:nth-child(2)").text_content(),
            })
        
        ctx.set("extracted_data", data)
        return len(data)
    
    def save_data(ctx: WorkflowContext):
        data = ctx.get("extracted_data", [])
        with open("output.json", "w") as f:
            json.dump(data, f, indent=2)
        return f"Saved {len(data)} records"
    
    def logout(ctx: WorkflowContext):
        ctx.page.click("#logout")
        return True
    
    workflow = SequentialWorkflow("Data Extraction")
    workflow.context.set("username", "demo")
    workflow.context.set("password", "demo")
    
    workflow.add_step("login", login)
    workflow.add_step("extract_data", extract_data, depends_on=["login"])
    workflow.add_step("save_data", save_data, depends_on=["extract_data"])
    workflow.add_step("logout", logout, depends_on=["save_data"], skip_on_failure=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        success = workflow.run(page)
        report = workflow.get_report()
        print(json.dumps(report, indent=2))
        
        browser.close()


if __name__ == "__main__":
    example_sequential_workflow()
```

---

## State Machine Workflow

```python
#!/usr/bin/env python3
"""State machine workflow - run with: uv run script.py"""

from playwright.sync_api import Page
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Any, Optional
import json


class ProcessState(Enum):
    """Order processing states."""
    INIT = auto()
    LOGIN = auto()
    SEARCH = auto()
    ADD_TO_CART = auto()
    CHECKOUT = auto()
    PAYMENT = auto()
    CONFIRMATION = auto()
    COMPLETE = auto()
    ERROR = auto()


@dataclass
class Transition:
    """State transition definition."""
    from_state: ProcessState
    to_state: ProcessState
    action: Callable
    condition: Optional[Callable] = None


class StateMachineWorkflow:
    """State machine based workflow."""
    
    def __init__(self, name: str, initial_state: ProcessState):
        self.name = name
        self.current_state = initial_state
        self.transitions: list[Transition] = []
        self.state_history: list[ProcessState] = [initial_state]
        self.context: dict = {}
        self.page: Optional[Page] = None
    
    def add_transition(
        self,
        from_state: ProcessState,
        to_state: ProcessState,
        action: Callable,
        condition: Callable = None
    ) -> "StateMachineWorkflow":
        """Add state transition."""
        self.transitions.append(Transition(from_state, to_state, action, condition))
        return self
    
    def can_transition(self, to_state: ProcessState) -> bool:
        """Check if transition is possible."""
        for t in self.transitions:
            if t.from_state == self.current_state and t.to_state == to_state:
                if t.condition is None or t.condition(self.context):
                    return True
        return False
    
    def transition_to(self, to_state: ProcessState) -> bool:
        """Execute transition to new state."""
        for t in self.transitions:
            if t.from_state == self.current_state and t.to_state == to_state:
                if t.condition and not t.condition(self.context):
                    continue
                
                try:
                    result = t.action(self.page, self.context)
                    self.context["last_result"] = result
                    self.current_state = to_state
                    self.state_history.append(to_state)
                    return True
                except Exception as e:
                    self.context["last_error"] = str(e)
                    self.current_state = ProcessState.ERROR
                    self.state_history.append(ProcessState.ERROR)
                    return False
        
        return False
    
    def get_available_transitions(self) -> list[ProcessState]:
        """Get available next states."""
        available = []
        for t in self.transitions:
            if t.from_state == self.current_state:
                if t.condition is None or t.condition(self.context):
                    available.append(t.to_state)
        return available
    
    def run_to_completion(self, page: Page, target_state: ProcessState) -> bool:
        """Run workflow until target state reached."""
        self.page = page
        
        while self.current_state != target_state:
            if self.current_state == ProcessState.ERROR:
                return False
            
            available = self.get_available_transitions()
            if not available:
                return False
            
            # Take first available transition
            if not self.transition_to(available[0]):
                return False
        
        return True
    
    def get_state_history(self) -> list[str]:
        return [s.name for s in self.state_history]


def create_order_workflow():
    """Create order processing workflow."""
    
    def do_login(page: Page, ctx: dict) -> bool:
        page.goto("https://example.com/login")
        page.fill("#email", ctx.get("email", "user@example.com"))
        page.fill("#password", ctx.get("password", "password"))
        page.click("button[type=submit]")
        page.wait_for_url("**/dashboard**")
        return True
    
    def do_search(page: Page, ctx: dict) -> str:
        search_term = ctx.get("search_term", "product")
        page.fill("#search", search_term)
        page.click("#search-button")
        page.wait_for_selector(".product-results")
        return search_term
    
    def do_add_to_cart(page: Page, ctx: dict) -> int:
        page.click(".product-item:first-child .add-to-cart")
        page.wait_for_selector(".cart-count:has-text('1')")
        return 1
    
    def do_checkout(page: Page, ctx: dict) -> bool:
        page.click("#checkout-button")
        page.wait_for_url("**/checkout**")
        page.fill("#shipping-address", ctx.get("address", "123 Main St"))
        return True
    
    def do_payment(page: Page, ctx: dict) -> str:
        page.fill("#card-number", ctx.get("card", "4111111111111111"))
        page.fill("#expiry", ctx.get("expiry", "12/25"))
        page.fill("#cvv", ctx.get("cvv", "123"))
        page.click("#pay-button")
        return "payment_submitted"
    
    def do_confirmation(page: Page, ctx: dict) -> str:
        page.wait_for_selector(".order-confirmation")
        order_id = page.locator(".order-id").text_content()
        ctx["order_id"] = order_id
        return order_id
    
    workflow = StateMachineWorkflow("Order Process", ProcessState.INIT)
    
    workflow.add_transition(ProcessState.INIT, ProcessState.LOGIN, do_login)
    workflow.add_transition(ProcessState.LOGIN, ProcessState.SEARCH, do_search)
    workflow.add_transition(ProcessState.SEARCH, ProcessState.ADD_TO_CART, do_add_to_cart)
    workflow.add_transition(ProcessState.ADD_TO_CART, ProcessState.CHECKOUT, do_checkout)
    workflow.add_transition(ProcessState.CHECKOUT, ProcessState.PAYMENT, do_payment)
    workflow.add_transition(ProcessState.PAYMENT, ProcessState.CONFIRMATION, do_confirmation)
    workflow.add_transition(ProcessState.CONFIRMATION, ProcessState.COMPLETE, lambda p, c: True)
    
    return workflow
```

---

## Checkpoint and Recovery

```python
#!/usr/bin/env python3
"""Checkpoint and recovery - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
import json


@dataclass
class Checkpoint:
    """Workflow checkpoint."""
    workflow_name: str
    step_name: str
    step_index: int
    context_data: dict
    page_url: str
    cookies: list[dict]
    timestamp: str
    
    def save(self, filepath: str):
        """Save checkpoint to file."""
        with open(filepath, "w") as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> "Checkpoint":
        """Load checkpoint from file."""
        with open(filepath) as f:
            data = json.load(f)
        return cls(**data)


class CheckpointedWorkflow:
    """Workflow with checkpoint and recovery support."""
    
    def __init__(self, name: str, checkpoint_dir: str = "./checkpoints"):
        self.name = name
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.steps: list[tuple[str, callable]] = []
        self.context: dict = {}
        self.current_step_index: int = 0
        self.page: Optional[Page] = None
    
    def add_step(self, name: str, action: callable) -> "CheckpointedWorkflow":
        """Add step to workflow."""
        self.steps.append((name, action))
        return self
    
    def _checkpoint_path(self) -> Path:
        """Get checkpoint file path."""
        return self.checkpoint_dir / f"{self.name}_checkpoint.json"
    
    def create_checkpoint(self, step_name: str, step_index: int):
        """Create checkpoint at current state."""
        if not self.page:
            return
        
        checkpoint = Checkpoint(
            workflow_name=self.name,
            step_name=step_name,
            step_index=step_index,
            context_data=self.context.copy(),
            page_url=self.page.url,
            cookies=self.page.context.cookies(),
            timestamp=datetime.now().isoformat()
        )
        
        checkpoint.save(str(self._checkpoint_path()))
        print(f"Checkpoint created: {step_name} (step {step_index})")
    
    def has_checkpoint(self) -> bool:
        """Check if checkpoint exists."""
        return self._checkpoint_path().exists()
    
    def load_checkpoint(self) -> Optional[Checkpoint]:
        """Load existing checkpoint."""
        if self.has_checkpoint():
            return Checkpoint.load(str(self._checkpoint_path()))
        return None
    
    def clear_checkpoint(self):
        """Remove checkpoint file."""
        if self.has_checkpoint():
            self._checkpoint_path().unlink()
    
    def restore_from_checkpoint(self, checkpoint: Checkpoint):
        """Restore workflow state from checkpoint."""
        self.context = checkpoint.context_data.copy()
        self.current_step_index = checkpoint.step_index
        
        # Restore cookies
        self.page.context.add_cookies(checkpoint.cookies)
        
        # Navigate to saved URL
        self.page.goto(checkpoint.page_url)
        
        print(f"Restored from checkpoint: {checkpoint.step_name}")
    
    def run(self, page: Page, resume: bool = True) -> bool:
        """Run workflow with checkpoint support."""
        self.page = page
        start_index = 0
        
        # Check for existing checkpoint
        if resume and self.has_checkpoint():
            checkpoint = self.load_checkpoint()
            if checkpoint:
                self.restore_from_checkpoint(checkpoint)
                start_index = checkpoint.step_index + 1
                print(f"Resuming from step {start_index}")
        
        # Execute steps
        for i in range(start_index, len(self.steps)):
            step_name, action = self.steps[i]
            self.current_step_index = i
            
            try:
                print(f"Executing step {i}: {step_name}")
                result = action(self.page, self.context)
                self.context[f"step_{step_name}_result"] = result
                
                # Create checkpoint after each successful step
                self.create_checkpoint(step_name, i)
                
            except Exception as e:
                print(f"Step {step_name} failed: {e}")
                # Checkpoint is already saved from previous step
                return False
        
        # Workflow complete - clear checkpoint
        self.clear_checkpoint()
        print("Workflow completed successfully")
        return True


def example_checkpointed_workflow():
    """Long-running workflow with checkpoint support."""
    
    def step_login(page: Page, ctx: dict):
        page.goto("https://example.com/login")
        page.fill("#email", "user@example.com")
        page.fill("#password", "password")
        page.click("button[type=submit]")
        page.wait_for_url("**/dashboard**")
        return True
    
    def step_process_page_1(page: Page, ctx: dict):
        page.goto("https://example.com/page1")
        data = page.locator(".data-item").all_text_contents()
        ctx["page1_data"] = data
        return len(data)
    
    def step_process_page_2(page: Page, ctx: dict):
        page.goto("https://example.com/page2")
        data = page.locator(".data-item").all_text_contents()
        ctx["page2_data"] = data
        return len(data)
    
    def step_save_results(page: Page, ctx: dict):
        all_data = ctx.get("page1_data", []) + ctx.get("page2_data", [])
        with open("results.json", "w") as f:
            json.dump(all_data, f)
        return len(all_data)
    
    workflow = CheckpointedWorkflow("long_process")
    workflow.add_step("login", step_login)
    workflow.add_step("process_page_1", step_process_page_1)
    workflow.add_step("process_page_2", step_process_page_2)
    workflow.add_step("save_results", step_save_results)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Run with resume capability
        success = workflow.run(page, resume=True)
        print(f"Workflow completed: {success}")
        
        browser.close()


if __name__ == "__main__":
    example_checkpointed_workflow()
```

---

## Parallel Workflow Execution

```python
#!/usr/bin/env python3
"""Parallel workflow execution - run with: uv run script.py"""

import asyncio
from playwright.async_api import async_playwright, Page, Browser
from dataclasses import dataclass
from typing import Callable, Any, Awaitable
from datetime import datetime
import structlog

log = structlog.get_logger()


@dataclass
class ParallelTask:
    """Task for parallel execution."""
    name: str
    action: Callable[[Page, dict], Awaitable[Any]]
    context: dict = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class TaskResult:
    """Result of parallel task."""
    name: str
    success: bool
    result: Any = None
    error: str = None
    duration_seconds: float = 0


class ParallelWorkflow:
    """Execute multiple workflows in parallel."""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.browser: Browser = None
    
    async def execute_task(
        self,
        task: ParallelTask,
        semaphore: asyncio.Semaphore
    ) -> TaskResult:
        """Execute single task."""
        async with semaphore:
            start = datetime.now()
            context = await self.browser.new_context()
            page = await context.new_page()
            
            try:
                log.info("task_started", task=task.name)
                result = await task.action(page, task.context)
                duration = (datetime.now() - start).total_seconds()
                
                return TaskResult(
                    name=task.name,
                    success=True,
                    result=result,
                    duration_seconds=duration
                )
            except Exception as e:
                duration = (datetime.now() - start).total_seconds()
                log.error("task_failed", task=task.name, error=str(e))
                
                return TaskResult(
                    name=task.name,
                    success=False,
                    error=str(e),
                    duration_seconds=duration
                )
            finally:
                await context.close()
    
    async def run(self, tasks: list[ParallelTask]) -> list[TaskResult]:
        """Run all tasks in parallel."""
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=True)
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            coroutines = [
                self.execute_task(task, semaphore)
                for task in tasks
            ]
            
            results = await asyncio.gather(*coroutines)
            await self.browser.close()
            
            return results


async def example_parallel_workflow():
    """Process multiple URLs in parallel."""
    
    async def scrape_url(page: Page, ctx: dict) -> dict:
        url = ctx["url"]
        await page.goto(url, wait_until="networkidle")
        title = await page.title()
        return {"url": url, "title": title}
    
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://quotes.toscrape.com",
        "https://books.toscrape.com",
    ]
    
    tasks = [
        ParallelTask(
            name=f"scrape_{i}",
            action=scrape_url,
            context={"url": url}
        )
        for i, url in enumerate(urls)
    ]
    
    workflow = ParallelWorkflow(max_concurrent=3)
    results = await workflow.run(tasks)
    
    for result in results:
        if result.success:
            log.info("result", name=result.name, data=result.result)
        else:
            log.error("result", name=result.name, error=result.error)


if __name__ == "__main__":
    asyncio.run(example_parallel_workflow())
```

---

## Prefect Integration

```python
#!/usr/bin/env python3
"""Prefect workflow integration - run with: uv run script.py"""

from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from playwright.sync_api import sync_playwright
from datetime import timedelta
from typing import Any
import json


@task(
    name="Login",
    retries=3,
    retry_delay_seconds=10,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1)
)
def login_task(url: str, username: str, password: str) -> dict:
    """Login and return session cookies."""
    logger = get_run_logger()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        logger.info(f"Logging in to {url}")
        page.goto(url)
        page.fill("#username", username)
        page.fill("#password", password)
        page.click("button[type=submit]")
        page.wait_for_url("**/dashboard**")
        
        cookies = page.context.cookies()
        browser.close()
        
        logger.info("Login successful")
        return {"cookies": cookies, "url": page.url}


@task(
    name="Extract Data",
    retries=2,
    retry_delay_seconds=5
)
def extract_data_task(cookies: list[dict], url: str) -> list[dict]:
    """Extract data from authenticated page."""
    logger = get_run_logger()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()
        
        logger.info(f"Extracting data from {url}")
        page.goto(url)
        page.wait_for_selector(".data-table")
        
        data = []
        for row in page.locator(".data-table tbody tr").all():
            data.append({
                "name": row.locator("td:nth-child(1)").text_content(),
                "value": row.locator("td:nth-child(2)").text_content(),
            })
        
        browser.close()
        logger.info(f"Extracted {len(data)} records")
        return data


@task(name="Transform Data")
def transform_data_task(data: list[dict]) -> list[dict]:
    """Transform extracted data."""
    logger = get_run_logger()
    
    transformed = []
    for item in data:
        transformed.append({
            "name": item["name"].strip().upper(),
            "value": float(item["value"].replace(",", "")) if item["value"] else 0,
        })
    
    logger.info(f"Transformed {len(transformed)} records")
    return transformed


@task(name="Save Data")
def save_data_task(data: list[dict], output_path: str) -> str:
    """Save data to file."""
    logger = get_run_logger()
    
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved data to {output_path}")
    return output_path


@flow(
    name="Web Scraping Pipeline",
    description="Extract, transform, and load data from web application"
)
def web_scraping_flow(
    login_url: str,
    data_url: str,
    username: str,
    password: str,
    output_path: str = "output.json"
) -> dict:
    """Complete web scraping workflow."""
    logger = get_run_logger()
    
    # Step 1: Login
    login_result = login_task(login_url, username, password)
    
    # Step 2: Extract data
    raw_data = extract_data_task(login_result["cookies"], data_url)
    
    # Step 3: Transform data
    transformed_data = transform_data_task(raw_data)
    
    # Step 4: Save data
    saved_path = save_data_task(transformed_data, output_path)
    
    return {
        "records_processed": len(transformed_data),
        "output_file": saved_path
    }


@flow(name="Parallel Scraping Flow")
def parallel_scraping_flow(urls: list[str]) -> list[dict]:
    """Scrape multiple URLs in parallel."""
    
    @task
    def scrape_url(url: str) -> dict:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            title = page.title()
            browser.close()
            return {"url": url, "title": title}
    
    # Submit all tasks concurrently
    results = scrape_url.map(urls)
    return results


if __name__ == "__main__":
    # Run the flow
    result = web_scraping_flow(
        login_url="https://example.com/login",
        data_url="https://example.com/data",
        username="demo",
        password="demo",
        output_path="scraped_data.json"
    )
    print(f"Flow result: {result}")
```

---

## Temporal Integration

```python
#!/usr/bin/env python3
"""Temporal workflow integration - run with: uv run script.py"""

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from playwright.sync_api import sync_playwright
from datetime import timedelta
from dataclasses import dataclass
import asyncio
import json


@dataclass
class ScrapingInput:
    """Input for scraping activity."""
    url: str
    selector: str


@dataclass
class ScrapingResult:
    """Result from scraping activity."""
    url: str
    data: list[str]
    success: bool
    error: str = None


@activity.defn
async def scrape_page(input: ScrapingInput) -> ScrapingResult:
    """Scrape page activity."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(input.url, wait_until="networkidle")
            page.wait_for_selector(input.selector)
            
            data = page.locator(input.selector).all_text_contents()
            browser.close()
            
            return ScrapingResult(
                url=input.url,
                data=data,
                success=True
            )
    except Exception as e:
        return ScrapingResult(
            url=input.url,
            data=[],
            success=False,
            error=str(e)
        )


@activity.defn
async def save_results(data: list[dict], filepath: str) -> str:
    """Save results to file."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    return filepath


@workflow.defn
class WebScrapingWorkflow:
    """Temporal workflow for web scraping."""
    
    @workflow.run
    async def run(self, urls: list[str], selector: str) -> dict:
        """Execute scraping workflow."""
        
        # Scrape all URLs
        results = []
        for url in urls:
            result = await workflow.execute_activity(
                scrape_page,
                ScrapingInput(url=url, selector=selector),
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=workflow.RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0,
                )
            )
            results.append({
                "url": result.url,
                "data": result.data,
                "success": result.success,
                "error": result.error
            })
        
        # Save results
        filepath = await workflow.execute_activity(
            save_results,
            args=[results, "temporal_results.json"],
            start_to_close_timeout=timedelta(minutes=1)
        )
        
        return {
            "total_urls": len(urls),
            "successful": sum(1 for r in results if r["success"]),
            "output_file": filepath
        }


async def run_temporal_workflow():
    """Run Temporal workflow."""
    # Connect to Temporal server
    client = await Client.connect("localhost:7233")
    
    # Run the workflow
    result = await client.execute_workflow(
        WebScrapingWorkflow.run,
        args=[
            ["https://example.com", "https://httpbin.org/html"],
            ".content"
        ],
        id="web-scraping-001",
        task_queue="scraping-queue",
    )
    
    print(f"Workflow result: {result}")


async def start_worker():
    """Start Temporal worker."""
    client = await Client.connect("localhost:7233")
    
    worker = Worker(
        client,
        task_queue="scraping-queue",
        workflows=[WebScrapingWorkflow],
        activities=[scrape_page, save_results],
    )
    
    print("Worker started, waiting for tasks...")
    await worker.run()


if __name__ == "__main__":
    # Start worker in one terminal: uv run script.py worker
    # Run workflow in another: uv run script.py run
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        asyncio.run(start_worker())
    else:
        asyncio.run(run_temporal_workflow())
```

---

## Workflow Monitoring

```python
#!/usr/bin/env python3
"""Workflow monitoring and alerting - run with: uv run script.py"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional
from enum import Enum
import json
import httpx


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class WorkflowMetrics:
    """Workflow execution metrics."""
    workflow_name: str
    start_time: datetime = None
    end_time: datetime = None
    steps_total: int = 0
    steps_completed: int = 0
    steps_failed: int = 0
    current_step: str = ""
    errors: list[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0
    
    @property
    def success_rate(self) -> float:
        if self.steps_total == 0:
            return 0
        return self.steps_completed / self.steps_total


class WorkflowMonitor:
    """Monitor workflow execution and send alerts."""
    
    def __init__(self, workflow_name: str):
        self.workflow_name = workflow_name
        self.metrics = WorkflowMetrics(workflow_name=workflow_name)
        self.alert_handlers: list[Callable] = []
    
    def add_alert_handler(self, handler: Callable):
        """Add alert handler."""
        self.alert_handlers.append(handler)
    
    def start_workflow(self, total_steps: int):
        """Mark workflow start."""
        self.metrics.start_time = datetime.now()
        self.metrics.steps_total = total_steps
    
    def step_started(self, step_name: str):
        """Mark step start."""
        self.metrics.current_step = step_name
    
    def step_completed(self, step_name: str):
        """Mark step completion."""
        self.metrics.steps_completed += 1
    
    def step_failed(self, step_name: str, error: str):
        """Mark step failure."""
        self.metrics.steps_failed += 1
        self.metrics.errors.append(f"{step_name}: {error}")
        self._send_alert(AlertLevel.ERROR, f"Step '{step_name}' failed: {error}")
    
    def end_workflow(self, success: bool):
        """Mark workflow end."""
        self.metrics.end_time = datetime.now()
        
        if success:
            self._send_alert(AlertLevel.INFO, f"Workflow completed successfully in {self.metrics.duration_seconds:.2f}s")
        else:
            self._send_alert(AlertLevel.CRITICAL, f"Workflow failed after {self.metrics.duration_seconds:.2f}s")
    
    def _send_alert(self, level: AlertLevel, message: str):
        """Send alert to all handlers."""
        for handler in self.alert_handlers:
            try:
                handler(level, message, self.metrics)
            except Exception as e:
                print(f"Alert handler error: {e}")
    
    def get_metrics(self) -> dict:
        """Get current metrics."""
        return {
            "workflow_name": self.metrics.workflow_name,
            "start_time": self.metrics.start_time.isoformat() if self.metrics.start_time else None,
            "end_time": self.metrics.end_time.isoformat() if self.metrics.end_time else None,
            "duration_seconds": self.metrics.duration_seconds,
            "steps_total": self.metrics.steps_total,
            "steps_completed": self.metrics.steps_completed,
            "steps_failed": self.metrics.steps_failed,
            "success_rate": self.metrics.success_rate,
            "current_step": self.metrics.current_step,
            "errors": self.metrics.errors,
        }


def slack_alert_handler(webhook_url: str):
    """Create Slack alert handler."""
    def handler(level: AlertLevel, message: str, metrics: WorkflowMetrics):
        color_map = {
            AlertLevel.INFO: "#36a64f",
            AlertLevel.WARNING: "#ffcc00",
            AlertLevel.ERROR: "#ff6600",
            AlertLevel.CRITICAL: "#ff0000",
        }
        
        payload = {
            "attachments": [{
                "color": color_map.get(level, "#808080"),
                "title": f"[{level.value.upper()}] {metrics.workflow_name}",
                "text": message,
                "fields": [
                    {"title": "Progress", "value": f"{metrics.steps_completed}/{metrics.steps_total}", "short": True},
                    {"title": "Success Rate", "value": f"{metrics.success_rate:.1%}", "short": True},
                ],
                "footer": f"Duration: {metrics.duration_seconds:.2f}s"
            }]
        }
        
        httpx.post(webhook_url, json=payload)
    
    return handler


def telegram_alert_handler(bot_token: str, chat_id: str):
    """Create Telegram alert handler."""
    def handler(level: AlertLevel, message: str, metrics: WorkflowMetrics):
        emoji_map = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨",
        }
        
        text = f"{emoji_map.get(level, '')} *{metrics.workflow_name}*\n\n{message}\n\nProgress: {metrics.steps_completed}/{metrics.steps_total}"
        
        httpx.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        )
    
    return handler


# Example usage
def example_monitored_workflow():
    from playwright.sync_api import sync_playwright
    
    monitor = WorkflowMonitor("Data Extraction Workflow")
    
    # Add alerting
    # monitor.add_alert_handler(slack_alert_handler("https://hooks.slack.com/..."))
    
    def log_alert(level, message, metrics):
        print(f"[{level.value}] {message}")
    
    monitor.add_alert_handler(log_alert)
    
    steps = ["login", "navigate", "extract", "save"]
    monitor.start_workflow(len(steps))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            for step in steps:
                monitor.step_started(step)
                # ... do step work
                monitor.step_completed(step)
            
            monitor.end_workflow(success=True)
        except Exception as e:
            monitor.step_failed(monitor.metrics.current_step, str(e))
            monitor.end_workflow(success=False)
        finally:
            browser.close()
    
    print(json.dumps(monitor.get_metrics(), indent=2))


if __name__ == "__main__":
    example_monitored_workflow()
```

---

## Best Practices

1. **Use checkpoints** - Save state after each critical step
2. **Implement retries** - Handle transient failures gracefully
3. **Monitor progress** - Track metrics and send alerts
4. **Handle dependencies** - Ensure steps execute in correct order
5. **Parallelize when possible** - Speed up independent operations
6. **Log extensively** - Capture all relevant information
7. **Test recovery** - Verify workflows can resume from any point

---

**Next Module:** See **rpa-authentication.md** for login automation patterns.
