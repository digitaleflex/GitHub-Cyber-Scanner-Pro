# RPA Observability Module

Enterprise observability including structured logging, Prometheus metrics, distributed tracing, and Grafana dashboards.

## Structured Logging

### Structlog Configuration

```python
#!/usr/bin/env python3
"""Structured logging setup - run with: uv run script.py"""

import structlog
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def configure_logging(
    log_level: str = "INFO",
    json_format: bool = True,
    log_file: str = None,
    include_timestamp: bool = True
):
    """Configure structured logging."""
    
    # Processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if include_timestamp:
        processors.insert(0, structlog.processors.TimeStamper(fmt="iso"))
    
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # File handler if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        logging.getLogger().addHandler(file_handler)


class RPALogger:
    """RPA-specific logger with context."""
    
    def __init__(self, workflow_name: str = "unknown"):
        self.log = structlog.get_logger()
        self.workflow_name = workflow_name
        self._bind_context()
    
    def _bind_context(self):
        """Bind workflow context."""
        structlog.contextvars.bind_contextvars(
            workflow=self.workflow_name,
            run_id=datetime.now().strftime("%Y%m%d_%H%M%S")
        )
    
    def step_start(self, step_name: str, **kwargs):
        """Log step start."""
        self.log.info("step_started", step=step_name, **kwargs)
    
    def step_complete(self, step_name: str, duration_ms: float = None, **kwargs):
        """Log step completion."""
        self.log.info("step_completed", step=step_name, duration_ms=duration_ms, **kwargs)
    
    def step_failed(self, step_name: str, error: str, **kwargs):
        """Log step failure."""
        self.log.error("step_failed", step=step_name, error=error, **kwargs)
    
    def data_extracted(self, count: int, source: str = None, **kwargs):
        """Log data extraction."""
        self.log.info("data_extracted", count=count, source=source, **kwargs)
    
    def page_loaded(self, url: str, load_time_ms: float = None, **kwargs):
        """Log page load."""
        self.log.info("page_loaded", url=url, load_time_ms=load_time_ms, **kwargs)
    
    def action_performed(self, action: str, selector: str = None, **kwargs):
        """Log UI action."""
        self.log.debug("action_performed", action=action, selector=selector, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning."""
        self.log.warning(message, **kwargs)
    
    def error(self, message: str, exception: Exception = None, **kwargs):
        """Log error."""
        if exception:
            self.log.exception(message, error=str(exception), **kwargs)
        else:
            self.log.error(message, **kwargs)


# Example usage
if __name__ == "__main__":
    configure_logging(log_level="DEBUG", json_format=True)
    
    logger = RPALogger("data_extraction")
    
    logger.step_start("login")
    logger.page_loaded("https://example.com", load_time_ms=1250)
    logger.action_performed("click", selector="#login-button")
    logger.step_complete("login", duration_ms=3500)
    
    logger.step_start("extract_data")
    logger.data_extracted(count=150, source="table#data")
    logger.step_complete("extract_data", duration_ms=5200)
```

---

## Prometheus Metrics

### Metrics Setup

```python
#!/usr/bin/env python3
"""Prometheus metrics - run with: uv run script.py"""

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    start_http_server, CollectorRegistry, REGISTRY,
    generate_latest
)
from functools import wraps
from typing import Callable
import time


# Metrics registry
METRICS_REGISTRY = REGISTRY

# Workflow metrics
WORKFLOW_RUNS = Counter(
    'rpa_workflow_runs_total',
    'Total workflow runs',
    ['workflow', 'status']
)

WORKFLOW_DURATION = Histogram(
    'rpa_workflow_duration_seconds',
    'Workflow execution duration',
    ['workflow'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]
)

STEP_DURATION = Histogram(
    'rpa_step_duration_seconds',
    'Step execution duration',
    ['workflow', 'step'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60]
)

STEP_ERRORS = Counter(
    'rpa_step_errors_total',
    'Step errors',
    ['workflow', 'step', 'error_type']
)

# Page metrics
PAGE_LOAD_TIME = Histogram(
    'rpa_page_load_seconds',
    'Page load time',
    ['url_pattern'],
    buckets=[0.5, 1, 2, 3, 5, 10, 20, 30]
)

# Data metrics
DATA_EXTRACTED = Counter(
    'rpa_data_extracted_total',
    'Total data records extracted',
    ['workflow', 'source']
)

# Active workflows
ACTIVE_WORKFLOWS = Gauge(
    'rpa_active_workflows',
    'Currently running workflows',
    ['workflow']
)

# System info
SYSTEM_INFO = Info(
    'rpa_system',
    'RPA system information'
)


class MetricsCollector:
    """Collect and expose RPA metrics."""
    
    def __init__(self, workflow_name: str):
        self.workflow = workflow_name
        self._step_start_times: dict[str, float] = {}
        self._workflow_start_time: float = None
    
    def workflow_started(self):
        """Record workflow start."""
        self._workflow_start_time = time.time()
        ACTIVE_WORKFLOWS.labels(workflow=self.workflow).inc()
    
    def workflow_completed(self, success: bool):
        """Record workflow completion."""
        duration = time.time() - self._workflow_start_time
        status = "success" if success else "failure"
        
        WORKFLOW_RUNS.labels(workflow=self.workflow, status=status).inc()
        WORKFLOW_DURATION.labels(workflow=self.workflow).observe(duration)
        ACTIVE_WORKFLOWS.labels(workflow=self.workflow).dec()
    
    def step_started(self, step_name: str):
        """Record step start."""
        self._step_start_times[step_name] = time.time()
    
    def step_completed(self, step_name: str):
        """Record step completion."""
        if step_name in self._step_start_times:
            duration = time.time() - self._step_start_times[step_name]
            STEP_DURATION.labels(
                workflow=self.workflow,
                step=step_name
            ).observe(duration)
    
    def step_failed(self, step_name: str, error_type: str):
        """Record step failure."""
        STEP_ERRORS.labels(
            workflow=self.workflow,
            step=step_name,
            error_type=error_type
        ).inc()
    
    def page_loaded(self, url_pattern: str, load_time: float):
        """Record page load time."""
        PAGE_LOAD_TIME.labels(url_pattern=url_pattern).observe(load_time)
    
    def data_extracted(self, count: int, source: str):
        """Record extracted data count."""
        DATA_EXTRACTED.labels(
            workflow=self.workflow,
            source=source
        ).inc(count)


def track_metrics(workflow: str, step: str = None):
    """Decorator to track function metrics."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            collector = MetricsCollector(workflow)
            
            if step:
                collector.step_started(step)
            else:
                collector.workflow_started()
            
            try:
                result = func(*args, **kwargs)
                
                if step:
                    collector.step_completed(step)
                else:
                    collector.workflow_completed(success=True)
                
                return result
            except Exception as e:
                if step:
                    collector.step_failed(step, type(e).__name__)
                else:
                    collector.workflow_completed(success=False)
                raise
        
        return wrapper
    return decorator


def start_metrics_server(port: int = 8080):
    """Start Prometheus metrics HTTP server."""
    start_http_server(port)
    print(f"Metrics server started on port {port}")


# Example usage
@track_metrics("data_extraction")
def run_workflow():
    """Example workflow with metrics."""
    collector = MetricsCollector("data_extraction")
    
    collector.step_started("login")
    time.sleep(1)  # Simulate work
    collector.step_completed("login")
    
    collector.step_started("extract")
    time.sleep(2)
    collector.data_extracted(100, "table")
    collector.step_completed("extract")


if __name__ == "__main__":
    start_metrics_server(8080)
    
    # Run workflow
    run_workflow()
    
    # Keep server running
    import signal
    signal.pause()
```

---

## OpenTelemetry Tracing

```python
#!/usr/bin/env python3
"""OpenTelemetry distributed tracing - run with: uv run script.py"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentation
from opentelemetry.sdk.resources import Resource
from functools import wraps
from typing import Callable
import time


def configure_tracing(
    service_name: str = "rpa-automation",
    otlp_endpoint: str = "http://localhost:4317"
):
    """Configure OpenTelemetry tracing."""
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
    })
    
    provider = TracerProvider(resource=resource)
    
    # OTLP exporter
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    
    trace.set_tracer_provider(provider)
    
    # Instrument HTTP client
    HTTPXClientInstrumentation().instrument()
    
    return trace.get_tracer(service_name)


class TracedAutomation:
    """Automation with distributed tracing."""
    
    def __init__(self, workflow_name: str, tracer: trace.Tracer = None):
        self.workflow_name = workflow_name
        self.tracer = tracer or trace.get_tracer("rpa")
    
    def trace_step(self, step_name: str):
        """Decorator to trace a step."""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.tracer.start_as_current_span(step_name) as span:
                    span.set_attribute("workflow.name", self.workflow_name)
                    span.set_attribute("step.name", step_name)
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(trace.Status(trace.StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(
                            trace.Status(trace.StatusCode.ERROR, str(e))
                        )
                        span.record_exception(e)
                        raise
            
            return wrapper
        return decorator
    
    def run_traced(self, func: Callable, *args, **kwargs):
        """Run function with tracing."""
        with self.tracer.start_as_current_span(self.workflow_name) as span:
            span.set_attribute("workflow.name", self.workflow_name)
            
            try:
                result = func(*args, **kwargs)
                span.set_status(trace.Status(trace.StatusCode.OK))
                return result
            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def add_event(self, name: str, attributes: dict = None):
        """Add event to current span."""
        span = trace.get_current_span()
        span.add_event(name, attributes=attributes or {})
    
    def set_attribute(self, key: str, value):
        """Set attribute on current span."""
        span = trace.get_current_span()
        span.set_attribute(key, value)


# Example usage
if __name__ == "__main__":
    tracer = configure_tracing(
        service_name="rpa-data-extraction",
        otlp_endpoint="http://localhost:4317"
    )
    
    automation = TracedAutomation("daily_report", tracer)
    
    @automation.trace_step("login")
    def login():
        time.sleep(1)
        return True
    
    @automation.trace_step("extract_data")
    def extract_data():
        time.sleep(2)
        automation.add_event("data_extracted", {"count": 100})
        return [{"id": 1}, {"id": 2}]
    
    def main_workflow():
        login()
        data = extract_data()
        return data
    
    result = automation.run_traced(main_workflow)
    print(f"Result: {result}")
```

---

## Grafana Dashboards

### Dashboard JSON

```json
{
  "dashboard": {
    "title": "RPA Automation Dashboard",
    "uid": "rpa-automation",
    "panels": [
      {
        "title": "Workflow Runs",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "sum(increase(rpa_workflow_runs_total[24h]))",
            "legendFormat": "Total Runs"
          }
        ]
      },
      {
        "title": "Success Rate",
        "type": "gauge",
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
        "targets": [
          {
            "expr": "sum(rpa_workflow_runs_total{status='success'}) / sum(rpa_workflow_runs_total) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "max": 100,
            "min": 0,
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 80},
                {"color": "green", "value": 95}
              ]
            }
          }
        }
      },
      {
        "title": "Active Workflows",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "sum(rpa_active_workflows)"
          }
        ]
      },
      {
        "title": "Workflow Duration (p95)",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(rpa_workflow_duration_seconds_bucket[5m])) by (le, workflow))",
            "legendFormat": "{{workflow}}"
          }
        ]
      },
      {
        "title": "Errors by Step",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
        "targets": [
          {
            "expr": "sum(increase(rpa_step_errors_total[1h])) by (workflow, step)",
            "legendFormat": "{{workflow}}/{{step}}"
          }
        ]
      },
      {
        "title": "Data Extracted",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 12},
        "targets": [
          {
            "expr": "sum(increase(rpa_data_extracted_total[1h])) by (workflow)",
            "legendFormat": "{{workflow}}"
          }
        ]
      },
      {
        "title": "Page Load Times (p95)",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 12},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(rpa_page_load_seconds_bucket[5m])) by (le, url_pattern))",
            "legendFormat": "{{url_pattern}}"
          }
        ]
      }
    ]
  }
}
```

### Prometheus Alerts

```yaml
# prometheus-alerts.yml
groups:
  - name: rpa_alerts
    rules:
      - alert: RPAWorkflowFailureRate
        expr: |
          sum(rate(rpa_workflow_runs_total{status="failure"}[1h])) 
          / sum(rate(rpa_workflow_runs_total[1h])) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High RPA workflow failure rate"
          description: "More than 10% of workflows failing in the last hour"
      
      - alert: RPAWorkflowSlow
        expr: |
          histogram_quantile(0.95, rate(rpa_workflow_duration_seconds_bucket[5m])) > 600
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "RPA workflow running slow"
          description: "95th percentile workflow duration exceeds 10 minutes"
      
      - alert: RPANoDataExtracted
        expr: |
          sum(increase(rpa_data_extracted_total[1h])) == 0
        for: 2h
        labels:
          severity: warning
        annotations:
          summary: "No data extracted"
          description: "No data has been extracted in the last 2 hours"
      
      - alert: RPAHighErrorRate
        expr: |
          sum(rate(rpa_step_errors_total[5m])) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High RPA error rate"
          description: "More than 1 error per second"
```

---

## Health Checks

```python
#!/usr/bin/env python3
"""Health check endpoints - run with: uv run script.py"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
import asyncio
from aiohttp import web
import json


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a component."""
    name: str
    status: HealthStatus
    message: str = ""
    last_check: datetime = None
    details: dict = None


class HealthChecker:
    """Health check manager."""
    
    def __init__(self):
        self.components: dict[str, ComponentHealth] = {}
        self.checks: dict[str, callable] = {}
    
    def register_check(self, name: str, check_func: callable):
        """Register health check function."""
        self.checks[name] = check_func
    
    async def run_checks(self) -> dict:
        """Run all health checks."""
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                
            except Exception as e:
                status = HealthStatus.UNHEALTHY
                result = str(e)
            
            self.components[name] = ComponentHealth(
                name=name,
                status=status,
                message=str(result) if result else "",
                last_check=datetime.now()
            )
            
            results[name] = {
                "status": status.value,
                "message": self.components[name].message
            }
            
            if status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "components": results
        }
    
    def get_status(self) -> dict:
        """Get cached status."""
        components = {}
        overall = HealthStatus.HEALTHY
        
        for name, health in self.components.items():
            components[name] = {
                "status": health.status.value,
                "message": health.message,
                "last_check": health.last_check.isoformat() if health.last_check else None
            }
            
            if health.status == HealthStatus.UNHEALTHY:
                overall = HealthStatus.UNHEALTHY
        
        return {
            "status": overall.value,
            "components": components
        }


# Health check implementations
async def check_browser():
    """Check browser availability."""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        await browser.close()
    return True


async def check_network():
    """Check network connectivity."""
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.get("https://example.com", timeout=10)
        return response.status_code == 200


def check_disk_space():
    """Check disk space."""
    import shutil
    
    total, used, free = shutil.disk_usage("/")
    free_percent = (free / total) * 100
    return free_percent > 10  # At least 10% free


# HTTP Server
async def health_handler(request):
    """Health check endpoint."""
    checker = request.app['health_checker']
    result = await checker.run_checks()
    
    status_code = 200 if result['status'] == 'healthy' else 503
    return web.json_response(result, status=status_code)


async def ready_handler(request):
    """Readiness check endpoint."""
    checker = request.app['health_checker']
    result = checker.get_status()
    
    status_code = 200 if result['status'] == 'healthy' else 503
    return web.json_response(result, status=status_code)


async def live_handler(request):
    """Liveness check endpoint."""
    return web.json_response({"status": "alive"})


def start_health_server(port: int = 8081):
    """Start health check HTTP server."""
    app = web.Application()
    
    checker = HealthChecker()
    checker.register_check("browser", check_browser)
    checker.register_check("network", check_network)
    checker.register_check("disk", check_disk_space)
    
    app['health_checker'] = checker
    
    app.router.add_get("/health", health_handler)
    app.router.add_get("/ready", ready_handler)
    app.router.add_get("/live", live_handler)
    
    web.run_app(app, port=port)


if __name__ == "__main__":
    start_health_server(8081)
```

---

## Alerting Integration

```python
#!/usr/bin/env python3
"""Alert integrations - run with: uv run script.py"""

import httpx
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert message."""
    title: str
    message: str
    severity: AlertSeverity
    workflow: str = None
    step: str = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AlertManager:
    """Manage and send alerts."""
    
    def __init__(self):
        self.handlers = []
    
    def add_handler(self, handler):
        """Add alert handler."""
        self.handlers.append(handler)
    
    def send(self, alert: Alert):
        """Send alert to all handlers."""
        for handler in self.handlers:
            try:
                handler.send(alert)
            except Exception as e:
                print(f"Alert handler failed: {e}")


class SlackHandler:
    """Slack alert handler."""
    
    def __init__(self, webhook_url: str, channel: str = None):
        self.webhook_url = webhook_url
        self.channel = channel
    
    def send(self, alert: Alert):
        """Send alert to Slack."""
        color_map = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffcc00",
            AlertSeverity.ERROR: "#ff6600",
            AlertSeverity.CRITICAL: "#ff0000",
        }
        
        payload = {
            "attachments": [{
                "color": color_map[alert.severity],
                "title": alert.title,
                "text": alert.message,
                "fields": [
                    {"title": "Severity", "value": alert.severity.value, "short": True},
                    {"title": "Workflow", "value": alert.workflow or "N/A", "short": True},
                ],
                "footer": f"RPA Alert | {alert.timestamp.isoformat()}"
            }]
        }
        
        if self.channel:
            payload["channel"] = self.channel
        
        httpx.post(self.webhook_url, json=payload)


class PagerDutyHandler:
    """PagerDuty alert handler."""
    
    def __init__(self, routing_key: str):
        self.routing_key = routing_key
        self.api_url = "https://events.pagerduty.com/v2/enqueue"
    
    def send(self, alert: Alert):
        """Send alert to PagerDuty."""
        if alert.severity not in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
            return  # Only send errors and critical
        
        payload = {
            "routing_key": self.routing_key,
            "event_action": "trigger",
            "payload": {
                "summary": alert.title,
                "severity": "critical" if alert.severity == AlertSeverity.CRITICAL else "error",
                "source": f"rpa-{alert.workflow or 'unknown'}",
                "custom_details": {
                    "message": alert.message,
                    "workflow": alert.workflow,
                    "step": alert.step,
                }
            }
        }
        
        httpx.post(self.api_url, json=payload)


class TelegramHandler:
    """Telegram alert handler."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
    
    def send(self, alert: Alert):
        """Send alert to Telegram."""
        emoji_map = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨",
        }
        
        message = f"{emoji_map[alert.severity]} *{alert.title}*\n\n{alert.message}"
        
        if alert.workflow:
            message += f"\n\nWorkflow: `{alert.workflow}`"
        
        httpx.post(
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            json={
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
        )


# Example usage
if __name__ == "__main__":
    manager = AlertManager()
    
    # Add handlers
    manager.add_handler(SlackHandler(
        webhook_url="https://hooks.slack.com/services/xxx"
    ))
    
    # Send alert
    alert = Alert(
        title="Workflow Failed",
        message="Data extraction failed due to timeout",
        severity=AlertSeverity.ERROR,
        workflow="daily_report",
        step="extract_data"
    )
    
    manager.send(alert)
```

---

## Best Practices

1. **Use structured logging** - JSON format for easy parsing
2. **Track key metrics** - Duration, success rate, data volume
3. **Set up alerts** - Error thresholds and anomaly detection
4. **Implement health checks** - Kubernetes-compatible endpoints
5. **Use distributed tracing** - Track requests across services
6. **Dashboard everything** - Grafana for visualization
7. **Retain logs** - Keep for debugging and compliance

---

**Next Module:** See **rpa-desktop.md** for Windows desktop automation.
