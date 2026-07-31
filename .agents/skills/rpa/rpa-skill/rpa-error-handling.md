# RPA Error Handling Module

Comprehensive error handling patterns including retry mechanisms, circuit breakers, recovery strategies, and monitoring.

## Retry Patterns

### Exponential Backoff Retry

```python
#!/usr/bin/env python3
"""Retry patterns - run with: uv run script.py"""

import asyncio
from functools import wraps
from typing import Callable, Type, Tuple, Any
from datetime import datetime
import time
import random
import structlog

log = structlog.get_logger()


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable = None
):
    """Retry decorator with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        actual_delay = min(current_delay, max_delay)
                        if jitter:
                            actual_delay *= (0.5 + random.random())
                        
                        log.warning(
                            "retry_attempt",
                            function=func.__name__,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=actual_delay,
                            error=str(e)
                        )
                        
                        if on_retry:
                            on_retry(attempt, e, actual_delay)
                        
                        time.sleep(actual_delay)
                        current_delay *= backoff
            
            log.error("retry_exhausted", function=func.__name__, error=str(last_exception))
            raise last_exception
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        actual_delay = min(current_delay, max_delay)
                        if jitter:
                            actual_delay *= (0.5 + random.random())
                        
                        log.warning(
                            "retry_attempt",
                            function=func.__name__,
                            attempt=attempt,
                            delay=actual_delay
                        )
                        
                        if on_retry:
                            on_retry(attempt, e, actual_delay)
                        
                        await asyncio.sleep(actual_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class RetryHandler:
    """Configurable retry handler."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff: float = 2.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff = backoff
        self.attempt = 0
    
    def reset(self):
        """Reset retry counter."""
        self.attempt = 0
    
    def should_retry(self, exception: Exception) -> bool:
        """Check if should retry."""
        self.attempt += 1
        return self.attempt < self.max_attempts
    
    def get_delay(self) -> float:
        """Get delay for current attempt."""
        delay = self.base_delay * (self.backoff ** (self.attempt - 1))
        delay = min(delay, self.max_delay)
        delay *= (0.5 + random.random())  # Jitter
        return delay
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry."""
        self.reset()
        
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if self.should_retry(e):
                    delay = self.get_delay()
                    log.warning("retrying", attempt=self.attempt, delay=delay)
                    time.sleep(delay)
                else:
                    raise


# Example usage
@retry(max_attempts=3, delay=1.0, backoff=2.0)
def flaky_operation():
    """Operation that might fail."""
    if random.random() < 0.7:
        raise ConnectionError("Simulated failure")
    return "Success!"
```

---

## Circuit Breaker

```python
#!/usr/bin/env python3
"""Circuit breaker pattern - run with: uv run script.py"""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any
import threading
import structlog

log = structlog.get_logger()


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: int = 30
    half_open_max_calls: int = 3


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime = None
        self.half_open_calls = 0
        self._lock = threading.Lock()
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to new state."""
        old_state = self.state
        self.state = new_state
        
        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.half_open_calls = 0
            self.success_count = 0
        
        log.info("circuit_state_change", name=self.name, old=old_state.value, new=new_state.value)
    
    def _record_success(self):
        """Record successful call."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0
    
    def _record_failure(self):
        """Record failed call."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
    
    def _should_allow_request(self) -> bool:
        """Check if request should be allowed."""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.OPEN:
                if self.last_failure_time:
                    elapsed = datetime.now() - self.last_failure_time
                    if elapsed.total_seconds() >= self.config.timeout_seconds:
                        self._transition_to(CircuitState.HALF_OPEN)
                        return True
                return False
            
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls < self.config.half_open_max_calls:
                    self.half_open_calls += 1
                    return True
                return False
        
        return False
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker."""
        if not self._should_allow_request():
            raise CircuitBreakerOpenError(f"Circuit '{self.name}' is open")
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def get_state(self) -> dict:
        """Get current state."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit is open."""
    pass


def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Circuit breaker decorator."""
    breaker = CircuitBreaker(name, config)
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


# Example
@circuit_breaker("external_api", CircuitBreakerConfig(failure_threshold=3, timeout_seconds=10))
def call_external_api():
    """Call external API with circuit breaker."""
    import httpx
    response = httpx.get("https://api.example.com/data", timeout=5)
    response.raise_for_status()
    return response.json()
```

---

## Recovery Strategies

```python
#!/usr/bin/env python3
"""Recovery strategies - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from dataclasses import dataclass
from typing import Callable, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import structlog

log = structlog.get_logger()


@dataclass
class RecoveryContext:
    """Context for recovery actions."""
    error: Exception
    page: Optional[Page]
    attempt: int
    workflow_state: dict
    screenshot_path: Optional[str] = None


class RecoveryStrategy:
    """Base recovery strategy."""
    
    def can_recover(self, context: RecoveryContext) -> bool:
        """Check if this strategy can handle the error."""
        return True
    
    def recover(self, context: RecoveryContext) -> bool:
        """Attempt recovery. Return True if successful."""
        raise NotImplementedError


class RefreshPageRecovery(RecoveryStrategy):
    """Recover by refreshing the page."""
    
    def can_recover(self, context: RecoveryContext) -> bool:
        return context.page is not None
    
    def recover(self, context: RecoveryContext) -> bool:
        log.info("recovery_refresh_page")
        context.page.reload()
        context.page.wait_for_load_state("networkidle")
        return True


class NavigateToURLRecovery(RecoveryStrategy):
    """Recover by navigating to specific URL."""
    
    def __init__(self, url: str):
        self.url = url
    
    def can_recover(self, context: RecoveryContext) -> bool:
        return context.page is not None
    
    def recover(self, context: RecoveryContext) -> bool:
        log.info("recovery_navigate", url=self.url)
        context.page.goto(self.url)
        context.page.wait_for_load_state("networkidle")
        return True


class ClearCookiesRecovery(RecoveryStrategy):
    """Recover by clearing cookies and re-authenticating."""
    
    def __init__(self, login_func: Callable):
        self.login_func = login_func
    
    def can_recover(self, context: RecoveryContext) -> bool:
        return context.page is not None
    
    def recover(self, context: RecoveryContext) -> bool:
        log.info("recovery_clear_cookies")
        context.page.context.clear_cookies()
        self.login_func(context.page)
        return True


class RestoreCheckpointRecovery(RecoveryStrategy):
    """Recover from saved checkpoint."""
    
    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = Path(checkpoint_dir)
    
    def can_recover(self, context: RecoveryContext) -> bool:
        checkpoint_file = self.checkpoint_dir / "latest.json"
        return checkpoint_file.exists()
    
    def recover(self, context: RecoveryContext) -> bool:
        checkpoint_file = self.checkpoint_dir / "latest.json"
        
        with open(checkpoint_file) as f:
            checkpoint = json.load(f)
        
        log.info("recovery_restore_checkpoint", checkpoint=checkpoint)
        
        # Restore cookies
        if "cookies" in checkpoint and context.page:
            context.page.context.add_cookies(checkpoint["cookies"])
        
        # Restore state
        context.workflow_state.update(checkpoint.get("state", {}))
        
        # Navigate to last URL
        if "url" in checkpoint and context.page:
            context.page.goto(checkpoint["url"])
        
        return True


class RecoveryManager:
    """Manage multiple recovery strategies."""
    
    def __init__(self):
        self.strategies: list[RecoveryStrategy] = []
        self.error_handlers: dict[type, RecoveryStrategy] = {}
    
    def add_strategy(self, strategy: RecoveryStrategy):
        """Add recovery strategy."""
        self.strategies.append(strategy)
    
    def add_error_handler(self, error_type: type, strategy: RecoveryStrategy):
        """Add handler for specific error type."""
        self.error_handlers[error_type] = strategy
    
    def attempt_recovery(self, context: RecoveryContext) -> bool:
        """Attempt recovery using available strategies."""
        # First try specific error handler
        error_type = type(context.error)
        if error_type in self.error_handlers:
            strategy = self.error_handlers[error_type]
            if strategy.can_recover(context):
                try:
                    if strategy.recover(context):
                        log.info("recovery_success", strategy=type(strategy).__name__)
                        return True
                except Exception as e:
                    log.warning("recovery_failed", strategy=type(strategy).__name__, error=str(e))
        
        # Try general strategies
        for strategy in self.strategies:
            if strategy.can_recover(context):
                try:
                    if strategy.recover(context):
                        log.info("recovery_success", strategy=type(strategy).__name__)
                        return True
                except Exception as e:
                    log.warning("recovery_failed", strategy=type(strategy).__name__, error=str(e))
        
        log.error("recovery_exhausted")
        return False


class RobustAutomator:
    """Automator with built-in error recovery."""
    
    def __init__(self, page: Page):
        self.page = page
        self.recovery_manager = RecoveryManager()
        self.workflow_state = {}
        self.screenshot_on_error = True
        self.screenshot_dir = Path("./error_screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        
        # Add default strategies
        self.recovery_manager.add_strategy(RefreshPageRecovery())
    
    def _capture_error_context(self, error: Exception, attempt: int) -> RecoveryContext:
        """Capture context on error."""
        screenshot_path = None
        
        if self.screenshot_on_error:
            screenshot_path = str(
                self.screenshot_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            try:
                self.page.screenshot(path=screenshot_path, full_page=True)
            except:
                screenshot_path = None
        
        return RecoveryContext(
            error=error,
            page=self.page,
            attempt=attempt,
            workflow_state=self.workflow_state,
            screenshot_path=screenshot_path
        )
    
    def execute_with_recovery(
        self,
        action: Callable,
        max_attempts: int = 3,
        *args,
        **kwargs
    ) -> Any:
        """Execute action with automatic recovery."""
        for attempt in range(1, max_attempts + 1):
            try:
                return action(*args, **kwargs)
            except Exception as e:
                log.warning("action_failed", attempt=attempt, error=str(e))
                
                if attempt < max_attempts:
                    context = self._capture_error_context(e, attempt)
                    
                    if self.recovery_manager.attempt_recovery(context):
                        continue  # Retry after recovery
                
                raise


def example_recovery():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        automator = RobustAutomator(page)
        
        # Add custom recovery strategy
        automator.recovery_manager.add_strategy(
            NavigateToURLRecovery("https://example.com")
        )
        
        def flaky_action():
            page.goto("https://example.com/maybe-broken")
            page.click("#button")
        
        try:
            automator.execute_with_recovery(flaky_action, max_attempts=3)
        except Exception as e:
            print(f"Failed after all recovery attempts: {e}")
        
        browser.close()


if __name__ == "__main__":
    example_recovery()
```

---

## Error Monitoring and Alerting

```python
#!/usr/bin/env python3
"""Error monitoring - run with: uv run script.py"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional
from collections import deque
import threading
import json
import httpx


@dataclass
class ErrorEvent:
    """Error event record."""
    timestamp: datetime
    error_type: str
    message: str
    workflow: str
    step: str
    stack_trace: Optional[str] = None
    screenshot_path: Optional[str] = None


class ErrorMonitor:
    """Monitor and alert on errors."""
    
    def __init__(
        self,
        error_threshold: int = 5,
        time_window_minutes: int = 10,
        alert_cooldown_minutes: int = 30
    ):
        self.error_threshold = error_threshold
        self.time_window = timedelta(minutes=time_window_minutes)
        self.alert_cooldown = timedelta(minutes=alert_cooldown_minutes)
        
        self.errors: deque[ErrorEvent] = deque(maxlen=1000)
        self.alert_handlers: list[Callable[[list[ErrorEvent]], None]] = []
        self.last_alert_time: Optional[datetime] = None
        self._lock = threading.Lock()
    
    def record_error(
        self,
        error: Exception,
        workflow: str = "unknown",
        step: str = "unknown",
        screenshot_path: str = None
    ):
        """Record error event."""
        import traceback
        
        event = ErrorEvent(
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            message=str(error),
            workflow=workflow,
            step=step,
            stack_trace=traceback.format_exc(),
            screenshot_path=screenshot_path
        )
        
        with self._lock:
            self.errors.append(event)
            self._check_threshold()
    
    def _check_threshold(self):
        """Check if error threshold exceeded."""
        cutoff = datetime.now() - self.time_window
        recent_errors = [e for e in self.errors if e.timestamp > cutoff]
        
        if len(recent_errors) >= self.error_threshold:
            if self._should_alert():
                self._send_alerts(recent_errors)
    
    def _should_alert(self) -> bool:
        """Check if should send alert (cooldown)."""
        if self.last_alert_time is None:
            return True
        
        return datetime.now() - self.last_alert_time > self.alert_cooldown
    
    def _send_alerts(self, errors: list[ErrorEvent]):
        """Send alerts to all handlers."""
        self.last_alert_time = datetime.now()
        
        for handler in self.alert_handlers:
            try:
                handler(errors)
            except Exception as e:
                print(f"Alert handler failed: {e}")
    
    def add_alert_handler(self, handler: Callable[[list[ErrorEvent]], None]):
        """Add alert handler."""
        self.alert_handlers.append(handler)
    
    def get_error_summary(self) -> dict:
        """Get error summary."""
        cutoff = datetime.now() - self.time_window
        recent = [e for e in self.errors if e.timestamp > cutoff]
        
        by_type = {}
        for e in recent:
            by_type[e.error_type] = by_type.get(e.error_type, 0) + 1
        
        by_workflow = {}
        for e in recent:
            by_workflow[e.workflow] = by_workflow.get(e.workflow, 0) + 1
        
        return {
            "total_errors": len(self.errors),
            "recent_errors": len(recent),
            "by_type": by_type,
            "by_workflow": by_workflow,
            "time_window_minutes": self.time_window.total_seconds() / 60
        }


def slack_alert_handler(webhook_url: str):
    """Create Slack alert handler."""
    def handler(errors: list[ErrorEvent]):
        error_summary = {}
        for e in errors:
            key = f"{e.error_type}: {e.message[:50]}"
            error_summary[key] = error_summary.get(key, 0) + 1
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "RPA Error Alert"}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{len(errors)} errors* in the last 10 minutes"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n".join([f"• {k}: {v}" for k, v in error_summary.items()])
                }
            }
        ]
        
        httpx.post(webhook_url, json={"blocks": blocks})
    
    return handler


def telegram_alert_handler(bot_token: str, chat_id: str):
    """Create Telegram alert handler."""
    def handler(errors: list[ErrorEvent]):
        message = f"🚨 *RPA Error Alert*\n\n{len(errors)} errors detected:\n"
        
        for e in errors[:5]:
            message += f"\n• {e.error_type}: {e.message[:100]}"
        
        if len(errors) > 5:
            message += f"\n\n...and {len(errors) - 5} more"
        
        httpx.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        )
    
    return handler


# Global monitor instance
error_monitor = ErrorMonitor()


def monitor_errors(workflow: str = "unknown"):
    """Decorator to monitor function errors."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_monitor.record_error(
                    error=e,
                    workflow=workflow,
                    step=func.__name__
                )
                raise
        return wrapper
    return decorator


if __name__ == "__main__":
    # Example usage
    monitor = ErrorMonitor(error_threshold=3, time_window_minutes=5)
    
    # Add console alert
    monitor.add_alert_handler(
        lambda errors: print(f"ALERT: {len(errors)} errors!")
    )
    
    # Simulate errors
    for i in range(5):
        monitor.record_error(
            ValueError(f"Test error {i}"),
            workflow="test_workflow",
            step="test_step"
        )
    
    print(json.dumps(monitor.get_error_summary(), indent=2))
```

---

## Best Practices

1. **Retry with backoff** - Exponential backoff with jitter
2. **Use circuit breakers** - Protect against cascading failures
3. **Capture context** - Screenshots and state on errors
4. **Monitor trends** - Track error rates over time
5. **Alert appropriately** - Avoid alert fatigue with cooldowns
6. **Log extensively** - Include enough context for debugging
7. **Graceful degradation** - Have fallback behavior when possible

---

**Next Module:** See **rpa-file-handling.md** for upload/download automation.
