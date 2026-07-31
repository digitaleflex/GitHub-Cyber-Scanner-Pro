# Temporal Workers

> Worker setup, configuration, graceful shutdown, and deployment patterns

## Overview

Workers are processes that execute workflows and activities. They poll Temporal server for tasks, execute the work, and report results back.

---

## Basic Worker Setup

### Minimal Worker

```python
# worker.py
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from .activities import send_email, process_payment
from .workflows import OrderWorkflow, NotificationWorkflow

async def main():
    # Connect to Temporal
    client = await Client.connect("localhost:7233")
    
    # Create worker
    worker = Worker(
        client,
        task_queue="my-task-queue",
        workflows=[
            OrderWorkflow,
            NotificationWorkflow,
        ],
        activities=[
            send_email,
            process_payment,
        ],
    )
    
    # Run worker (blocks until shutdown)
    print("Worker starting...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Run with uv

```bash
uv run python -m src.worker
# or
uv run python src/worker.py
```

---

## Production Worker

### Full Configuration

```python
# worker.py
import asyncio
import logging
import signal
from datetime import timedelta

from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker

from .config import Settings
from .activities import (
    send_email,
    process_payment,
    notify_customer,
    validate_order,
)
from .workflows import (
    OrderWorkflow,
    ApprovalWorkflow,
    BatchProcessingWorkflow,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Handle graceful shutdown signals."""
    
    def __init__(self):
        self.shutdown_event = asyncio.Event()
    
    def signal_handler(self, sig, frame):
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        self.shutdown_event.set()


async def create_client(settings: Settings) -> Client:
    """Create Temporal client with optional TLS."""
    
    # Temporal Cloud or TLS connection
    if settings.temporal_tls_cert and settings.temporal_tls_key:
        with open(settings.temporal_tls_cert, "rb") as f:
            client_cert = f.read()
        with open(settings.temporal_tls_key, "rb") as f:
            client_key = f.read()
        
        tls_config = TLSConfig(
            client_cert=client_cert,
            client_private_key=client_key,
        )
        
        return await Client.connect(
            settings.temporal_address,
            namespace=settings.temporal_namespace,
            tls=tls_config,
        )
    
    # Local/non-TLS connection
    return await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
    )


async def main():
    settings = Settings()
    shutdown = GracefulShutdown()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, shutdown.signal_handler)
    signal.signal(signal.SIGTERM, shutdown.signal_handler)
    
    # Connect to Temporal
    client = await create_client(settings)
    logger.info(f"Connected to Temporal at {settings.temporal_address}")
    
    # Create worker with production configuration
    worker = Worker(
        client,
        task_queue=settings.task_queue,
        
        # Workflows
        workflows=[
            OrderWorkflow,
            ApprovalWorkflow,
            BatchProcessingWorkflow,
        ],
        
        # Activities
        activities=[
            send_email,
            process_payment,
            notify_customer,
            validate_order,
        ],
        
        # Concurrency limits
        max_concurrent_activities=settings.max_concurrent_activities,
        max_concurrent_workflow_tasks=settings.max_concurrent_workflow_tasks,
        max_cached_workflows=settings.max_cached_workflows,
        
        # Graceful shutdown timeout
        graceful_shutdown_timeout=timedelta(seconds=30),
    )
    
    logger.info(f"Starting worker on task queue '{settings.task_queue}'")
    
    # Run worker until shutdown signal
    async with worker:
        await shutdown.shutdown_event.wait()
        logger.info("Shutting down worker...")
    
    logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration with Pydantic

```python
# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Temporal connection
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_tls_cert: Optional[str] = None
    temporal_tls_key: Optional[str] = None
    
    # Worker configuration
    task_queue: str = "my-task-queue"
    max_concurrent_activities: int = 100
    max_concurrent_workflow_tasks: int = 100
    max_cached_workflows: int = 1000
    
    # Application settings
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_prefix = "APP_"
```

### Environment Variables

```bash
# .env
APP_TEMPORAL_ADDRESS=localhost:7233
APP_TEMPORAL_NAMESPACE=default
APP_TASK_QUEUE=my-task-queue
APP_MAX_CONCURRENT_ACTIVITIES=100
APP_MAX_CONCURRENT_WORKFLOW_TASKS=100
APP_LOG_LEVEL=INFO

# For Temporal Cloud
APP_TEMPORAL_ADDRESS=namespace.account.tmprl.cloud:7233
APP_TEMPORAL_TLS_CERT=/path/to/client.pem
APP_TEMPORAL_TLS_KEY=/path/to/client.key
```

---

## Worker Configuration Options

### Concurrency Limits

```python
worker = Worker(
    client,
    task_queue="my-queue",
    workflows=[...],
    activities=[...],
    
    # Maximum concurrent activity executions
    max_concurrent_activities=100,
    
    # Maximum concurrent workflow task executions
    max_concurrent_workflow_tasks=100,
    
    # Maximum cached workflows (for sticky execution)
    max_cached_workflows=1000,
    
    # Maximum concurrent local activities
    max_concurrent_local_activities=100,
)
```

### Activity Execution

```python
from concurrent.futures import ThreadPoolExecutor

worker = Worker(
    client,
    task_queue="my-queue",
    workflows=[...],
    activities=[...],
    
    # Custom thread pool for sync activities
    activity_executor=ThreadPoolExecutor(max_workers=50),
    
    # Disable worker-level activity caching
    # (activities run fresh each time)
    # This is rarely needed
)
```

### Graceful Shutdown

```python
worker = Worker(
    client,
    task_queue="my-queue",
    workflows=[...],
    activities=[...],
    
    # Time to wait for in-progress work to complete
    graceful_shutdown_timeout=timedelta(seconds=30),
)
```

---

## Multiple Task Queues

### Separate Workers by Function

```python
# order_worker.py
async def run_order_worker():
    client = await Client.connect("localhost:7233")
    
    worker = Worker(
        client,
        task_queue="order-processing",
        workflows=[OrderWorkflow, RefundWorkflow],
        activities=[validate_order, process_payment, refund_payment],
    )
    
    await worker.run()

# notification_worker.py
async def run_notification_worker():
    client = await Client.connect("localhost:7233")
    
    worker = Worker(
        client,
        task_queue="notifications",
        workflows=[NotificationWorkflow],
        activities=[send_email, send_sms, send_push],
    )
    
    await worker.run()
```

### Single Worker, Multiple Queues

```python
async def run_multi_queue_worker():
    client = await Client.connect("localhost:7233")
    
    # Create multiple workers sharing same client
    workers = [
        Worker(
            client,
            task_queue="orders",
            workflows=[OrderWorkflow],
            activities=[process_order],
        ),
        Worker(
            client,
            task_queue="notifications",
            workflows=[NotificationWorkflow],
            activities=[send_notification],
        ),
    ]
    
    # Run all workers concurrently
    await asyncio.gather(*[w.run() for w in workers])
```

---

## Deployment Patterns

### Development (Temporal CLI)

```bash
# Start Temporal server in development mode
temporal server start-dev

# Start with persistent storage
temporal server start-dev --db-filename ./temporal.db

# Start with custom namespace and ports
temporal server start-dev \
  --namespace my-namespace \
  --port 7233 \
  --ui-port 8233

# Run worker in another terminal
uv run python -m src.worker
```

### Production with MySQL

For production deployments, use Temporal CLI with MySQL backend:

```bash
# Install Temporal CLI
brew install temporal  # macOS
# or
curl -sSf https://temporal.download/cli.sh | sh

# Start Temporal server with MySQL
temporal server start-dev \
  --db-filename "" \
  --sql-plugin mysql \
  --sql-host localhost \
  --sql-port 3306 \
  --sql-user temporal \
  --sql-password temporal123 \
  --sql-database temporal

# MySQL database setup (run once)
mysql -u root -p <<EOF
CREATE DATABASE temporal;
CREATE DATABASE temporal_visibility;
CREATE USER 'temporal'@'%' IDENTIFIED BY 'temporal123';
GRANT ALL PRIVILEGES ON temporal.* TO 'temporal'@'%';
GRANT ALL PRIVILEGES ON temporal_visibility.* TO 'temporal'@'%';
FLUSH PRIVILEGES;
EOF
```

### Production Configuration Script

```bash
#!/bin/bash
# start-temporal-production.sh

export SQL_PLUGIN=mysql
export SQL_HOST=${SQL_HOST:-localhost}
export SQL_PORT=${SQL_PORT:-3306}
export SQL_USER=${SQL_USER:-temporal}
export SQL_PASSWORD=${SQL_PASSWORD:-temporal123}
export SQL_DATABASE=${SQL_DATABASE:-temporal}

temporal server start-dev \
  --db-filename "" \
  --sql-plugin $SQL_PLUGIN \
  --sql-host $SQL_HOST \
  --sql-port $SQL_PORT \
  --sql-user $SQL_USER \
  --sql-password $SQL_PASSWORD \
  --sql-database $SQL_DATABASE \
  --log-level info
```

### Systemd (Temporal Server with MySQL)

```ini
# /etc/systemd/system/temporal-server.service
[Unit]
Description=Temporal Server
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=simple
User=temporal
Group=temporal
ExecStart=/usr/local/bin/temporal server start-dev \
    --db-filename "" \
    --sql-plugin mysql \
    --sql-host localhost \
    --sql-port 3306 \
    --sql-user temporal \
    --sql-password temporal123 \
    --sql-database temporal
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Systemd (Worker)

```ini
# /etc/systemd/system/temporal-worker.service
[Unit]
Description=Temporal Worker
After=network.target temporal-server.service

[Service]
Type=simple
User=app
Group=app
WorkingDirectory=/app
Environment=APP_TEMPORAL_ADDRESS=localhost:7233
Environment=APP_TASK_QUEUE=my-queue
ExecStart=/app/.venv/bin/python -m src.worker
Restart=always
RestartSec=5
# Graceful shutdown
TimeoutStopSec=45

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable temporal-server temporal-worker
sudo systemctl start temporal-server
sudo systemctl start temporal-worker

# View logs
sudo journalctl -u temporal-server -f
sudo journalctl -u temporal-worker -f
```

### macOS LaunchAgent

```xml
<!-- ~/Library/LaunchAgents/com.myapp.temporal-worker.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.myapp.temporal-worker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/me/.local/bin/uv</string>
        <string>run</string>
        <string>python</string>
        <string>-m</string>
        <string>src.worker</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/me/projects/my-temporal-app</string>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/me/logs/temporal-worker.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/me/logs/temporal-worker.error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>APP_TEMPORAL_ADDRESS</key>
        <string>localhost:7233</string>
        <key>APP_TASK_QUEUE</key>
        <string>my-queue</string>
    </dict>
</dict>
</plist>
```

```bash
# Install
launchctl load ~/Library/LaunchAgents/com.myapp.temporal-worker.plist

# Uninstall
launchctl unload ~/Library/LaunchAgents/com.myapp.temporal-worker.plist

# Check status
launchctl list | grep temporal
```

---

## Health Checks

### HTTP Health Endpoint

```python
# worker.py
import asyncio
from aiohttp import web

async def health_check(request):
    return web.json_response({"status": "healthy"})

async def run_health_server(port: int = 8080):
    app = web.Application()
    app.router.add_get("/health", health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    return runner

async def main():
    settings = Settings()
    
    # Start health check server
    health_runner = await run_health_server(8080)
    
    # Connect and run worker
    client = await Client.connect(settings.temporal_address)
    worker = Worker(...)
    
    try:
        await worker.run()
    finally:
        await health_runner.cleanup()
```

---

## Observability

### Structured Logging

```python
import structlog
from temporalio import activity, workflow

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

@activity.defn
async def my_activity(data: dict) -> dict:
    logger.info("activity_started", data=data)
    result = await process(data)
    logger.info("activity_completed", result_id=result["id"])
    return result
```

### OpenTelemetry Integration

```python
from temporalio.contrib.opentelemetry import TracingInterceptor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Configure OpenTelemetry
provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317"))
)
trace.set_tracer_provider(provider)

# Create client with tracing
client = await Client.connect(
    "localhost:7233",
    interceptors=[TracingInterceptor()],
)

# Worker automatically traces workflows and activities
worker = Worker(
    client,
    task_queue="my-queue",
    workflows=[...],
    activities=[...],
)
```

---

## Scaling Strategies

### Horizontal Scaling

```bash
# Run multiple worker instances
for i in {1..5}; do
    APP_WORKER_ID=$i uv run python -m src.worker &
done
```

### Task Queue Isolation

```python
# High-priority queue with more workers
# low-priority queue with fewer workers

# high_priority_worker.py (10 instances)
worker = Worker(
    client,
    task_queue="high-priority",
    max_concurrent_activities=200,
    ...
)

# low_priority_worker.py (2 instances)
worker = Worker(
    client,
    task_queue="low-priority",
    max_concurrent_activities=50,
    ...
)
```

### Multiple Worker Instances

```bash
# Run multiple workers with different IDs
for i in {1..5}; do
    APP_WORKER_ID=$i uv run python -m src.worker &
done

# Or use a process manager like supervisord
```

---

## Best Practices

1. **Use graceful shutdown** - Handle SIGTERM properly
2. **Set concurrency limits** - Match your infrastructure
3. **Separate by function** - Different queues for different workloads
4. **Add health checks** - For orchestration platforms
5. **Enable structured logging** - For observability
6. **Use connection pooling** - Share client across activities
7. **Monitor queue depth** - Scale based on backlog
8. **Version workers carefully** - Use task queue versioning

---

## Next Steps

- **temporal-scheduling.md** - Cron and interval schedules
- **temporal-cli.md** - CLI commands for worker management
- **temporal-production.md** - Production deployment guide
