# Temporal Cloud

> **Managed Temporal Service - Connection, Namespaces, and Metrics**  
> Production deployment on Temporal's fully managed cloud platform.

## Overview

Temporal Cloud is a fully managed, scalable Temporal service with:

| Feature | Description |
|---------|-------------|
| **Managed Infrastructure** | No server maintenance required |
| **Multi-Region** | Built-in redundancy and low latency |
| **mTLS by Default** | Secure connections out of the box |
| **Metrics & Observability** | Built-in dashboards and alerts |
| **SLA Guarantees** | Enterprise-grade reliability |

---

## Account Setup

### 1. Create Temporal Cloud Account

1. Visit [cloud.temporal.io](https://cloud.temporal.io)
2. Sign up for an account
3. Create your organization
4. Create a namespace

### 2. Generate Certificates

Temporal Cloud uses mTLS for authentication:

```bash
# Generate CA and client certificates
# Option 1: Use Temporal Cloud UI to generate
# Option 2: Generate your own

# Generate private key
openssl genrsa -out client.key 4096

# Generate certificate signing request
openssl req -new -key client.key -out client.csr \
  -subj "/CN=my-temporal-client/O=MyOrganization"

# Self-sign (or get signed by your CA)
openssl x509 -req -days 365 -in client.csr \
  -signkey client.key -out client.pem

# Upload the certificate to Temporal Cloud via UI
# Settings > Certificates > Add Certificate
```

### 3. Get Connection Details

From Temporal Cloud console:
- **Address**: `<namespace>.<account>.tmprl.cloud:7233`
- **Namespace**: Your namespace name
- **Certificate**: Uploaded client certificate

---

## Python Client Connection

### Basic Connection

```python
# cloud_client.py
import asyncio
from temporalio.client import Client, TLSConfig

async def create_cloud_client() -> Client:
    """Connect to Temporal Cloud."""
    
    # Load certificates
    with open("client.pem", "rb") as f:
        client_cert = f.read()
    with open("client.key", "rb") as f:
        client_key = f.read()
    
    tls_config = TLSConfig(
        client_cert=client_cert,
        client_private_key=client_key,
    )
    
    return await Client.connect(
        "my-namespace.my-account.tmprl.cloud:7233",
        namespace="my-namespace",
        tls=tls_config,
    )

async def main():
    client = await create_cloud_client()
    
    # Execute workflow
    result = await client.execute_workflow(
        MyWorkflow.run,
        {"data": "value"},
        id="cloud-workflow-1",
        task_queue="cloud-queue",
    )
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration-Based Connection

```python
# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class TemporalCloudSettings(BaseSettings):
    """Temporal Cloud configuration."""
    
    # Required
    temporal_cloud_address: str
    temporal_cloud_namespace: str
    temporal_tls_cert_path: str
    temporal_tls_key_path: str
    
    # Optional
    temporal_tls_ca_path: Optional[str] = None
    
    class Config:
        env_prefix = ""
        env_file = ".env"

# cloud_connection.py
from temporalio.client import Client, TLSConfig
from config import TemporalCloudSettings

async def get_cloud_client() -> Client:
    settings = TemporalCloudSettings()
    
    with open(settings.temporal_tls_cert_path, "rb") as f:
        client_cert = f.read()
    with open(settings.temporal_tls_key_path, "rb") as f:
        client_key = f.read()
    
    tls_config = TLSConfig(
        client_cert=client_cert,
        client_private_key=client_key,
    )
    
    return await Client.connect(
        settings.temporal_cloud_address,
        namespace=settings.temporal_cloud_namespace,
        tls=tls_config,
    )
```

```bash
# .env
TEMPORAL_CLOUD_ADDRESS=my-namespace.abc123.tmprl.cloud:7233
TEMPORAL_CLOUD_NAMESPACE=my-namespace
TEMPORAL_TLS_CERT_PATH=/etc/temporal/client.pem
TEMPORAL_TLS_KEY_PATH=/etc/temporal/client.key
```

### API Key Authentication (Alternative)

```python
# api_key_client.py
from temporalio.client import Client
import os

async def create_api_key_client() -> Client:
    """Connect using API key instead of mTLS."""
    
    return await Client.connect(
        "my-namespace.my-account.tmprl.cloud:7233",
        namespace="my-namespace",
        api_key=os.environ["TEMPORAL_API_KEY"],
    )
```

---

## Worker Deployment

### Cloud Worker

```python
# cloud_worker.py
import asyncio
import signal
from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker
from datetime import timedelta

from config import TemporalCloudSettings
from workflows import OrderWorkflow, NotificationWorkflow
from activities import process_order, send_notification

async def run_cloud_worker():
    """Run worker connected to Temporal Cloud."""
    settings = TemporalCloudSettings()
    
    # Load certificates
    with open(settings.temporal_tls_cert_path, "rb") as f:
        client_cert = f.read()
    with open(settings.temporal_tls_key_path, "rb") as f:
        client_key = f.read()
    
    tls_config = TLSConfig(
        client_cert=client_cert,
        client_private_key=client_key,
    )
    
    client = await Client.connect(
        settings.temporal_cloud_address,
        namespace=settings.temporal_cloud_namespace,
        tls=tls_config,
    )
    
    worker = Worker(
        client,
        task_queue="production-queue",
        workflows=[OrderWorkflow, NotificationWorkflow],
        activities=[process_order, send_notification],
        max_concurrent_activities=100,
        graceful_shutdown_timeout=timedelta(seconds=30),
    )
    
    # Handle shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    async with worker:
        await shutdown_event.wait()

if __name__ == "__main__":
    asyncio.run(run_cloud_worker())
```

### Systemd Service for Cloud Worker

```ini
# /etc/systemd/system/temporal-cloud-worker.service
[Unit]
Description=Temporal Cloud Worker
After=network.target

[Service]
Type=simple
User=temporal
Group=temporal
WorkingDirectory=/app

# Environment
EnvironmentFile=/etc/temporal/cloud.env

# Start worker
ExecStart=/app/.venv/bin/python -m src.cloud_worker

# Restart policy
Restart=always
RestartSec=5

# Graceful shutdown
TimeoutStopSec=45
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
```

```bash
# /etc/temporal/cloud.env
TEMPORAL_CLOUD_ADDRESS=my-namespace.abc123.tmprl.cloud:7233
TEMPORAL_CLOUD_NAMESPACE=my-namespace
TEMPORAL_TLS_CERT_PATH=/etc/temporal/client.pem
TEMPORAL_TLS_KEY_PATH=/etc/temporal/client.key
```

---

## Namespace Management

### Multi-Environment Setup

```python
# environments.py
from dataclasses import dataclass
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "dev"
    STAGING = "staging"
    PRODUCTION = "prod"

@dataclass
class TemporalNamespace:
    name: str
    address: str
    cert_path: str
    key_path: str

NAMESPACES = {
    Environment.DEVELOPMENT: TemporalNamespace(
        name="myapp-dev",
        address="myapp-dev.abc123.tmprl.cloud:7233",
        cert_path="/etc/temporal/dev/client.pem",
        key_path="/etc/temporal/dev/client.key",
    ),
    Environment.STAGING: TemporalNamespace(
        name="myapp-staging",
        address="myapp-staging.abc123.tmprl.cloud:7233",
        cert_path="/etc/temporal/staging/client.pem",
        key_path="/etc/temporal/staging/client.key",
    ),
    Environment.PRODUCTION: TemporalNamespace(
        name="myapp-prod",
        address="myapp-prod.abc123.tmprl.cloud:7233",
        cert_path="/etc/temporal/prod/client.pem",
        key_path="/etc/temporal/prod/client.key",
    ),
}

async def get_client_for_env(env: Environment) -> Client:
    ns = NAMESPACES[env]
    
    with open(ns.cert_path, "rb") as f:
        client_cert = f.read()
    with open(ns.key_path, "rb") as f:
        client_key = f.read()
    
    return await Client.connect(
        ns.address,
        namespace=ns.name,
        tls=TLSConfig(
            client_cert=client_cert,
            client_private_key=client_key,
        ),
    )
```

### Namespace Settings via tcld

```bash
# Install Temporal Cloud CLI
brew install temporalio/brew/tcld

# Login
tcld login

# List namespaces
tcld namespace list

# Get namespace info
tcld namespace get --namespace my-namespace

# Update retention
tcld namespace update --namespace my-namespace --retention 30d

# Add certificate
tcld namespace add-certificate \
  --namespace my-namespace \
  --certificate-file client.pem
```

---

## Metrics and Observability

### Prometheus Metrics Export

Temporal Cloud provides Prometheus-compatible metrics endpoint:

```python
# metrics_exporter.py
import httpx
from prometheus_client import start_http_server, Gauge
import asyncio

# Define Prometheus gauges
workflow_count = Gauge('temporal_workflows_total', 'Total workflows', ['status'])
activity_count = Gauge('temporal_activities_total', 'Total activities', ['status'])

async def fetch_cloud_metrics(api_key: str, namespace: str):
    """Fetch metrics from Temporal Cloud API."""
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.cloud.temporal.io/api/v1/namespaces/{namespace}/metrics",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        return response.json()

async def update_metrics():
    """Update Prometheus metrics from Temporal Cloud."""
    api_key = os.environ["TEMPORAL_CLOUD_API_KEY"]
    namespace = os.environ["TEMPORAL_CLOUD_NAMESPACE"]
    
    while True:
        metrics = await fetch_cloud_metrics(api_key, namespace)
        
        # Update gauges
        workflow_count.labels(status='running').set(
            metrics.get('running_workflows', 0)
        )
        workflow_count.labels(status='completed').set(
            metrics.get('completed_workflows', 0)
        )
        
        await asyncio.sleep(60)  # Update every minute

def main():
    # Start Prometheus HTTP server
    start_http_server(9090)
    
    # Run metrics updater
    asyncio.run(update_metrics())

if __name__ == "__main__":
    main()
```

### Datadog Integration

```python
# datadog_metrics.py
from datadog import initialize, statsd
from temporalio.client import Client

# Initialize Datadog
initialize(
    api_key=os.environ["DD_API_KEY"],
    app_key=os.environ["DD_APP_KEY"],
)

async def report_workflow_metrics(client: Client):
    """Report metrics to Datadog."""
    
    # Count running workflows
    running = 0
    async for _ in client.list_workflows(query="ExecutionStatus='Running'"):
        running += 1
    
    statsd.gauge('temporal.workflows.running', running, tags=['env:prod'])
    
    # Count failed in last hour
    failed = 0
    query = "ExecutionStatus='Failed' AND CloseTime > '-1h'"
    async for _ in client.list_workflows(query=query):
        failed += 1
    
    statsd.gauge('temporal.workflows.failed.1h', failed, tags=['env:prod'])
```

### Custom Activity Metrics

```python
# instrumented_activities.py
from temporalio import activity
import time
import structlog

logger = structlog.get_logger()

def timed_activity(fn):
    """Decorator to track activity duration."""
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await fn(*args, **kwargs)
            duration = time.time() - start
            logger.info(
                "activity_completed",
                activity_name=fn.__name__,
                duration_seconds=duration,
                success=True,
            )
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(
                "activity_failed",
                activity_name=fn.__name__,
                duration_seconds=duration,
                error=str(e),
                success=False,
            )
            raise
    
    wrapper.__name__ = fn.__name__
    return activity.defn(wrapper)

@timed_activity
async def process_order(order_id: str) -> dict:
    # Activity logic...
    return {"order_id": order_id, "status": "processed"}
```

---

## Alerting

### Slack Alerts for Failed Workflows

```python
# alerts.py
import asyncio
import httpx
from temporalio.client import Client
from datetime import datetime, timedelta

async def check_and_alert(client: Client, slack_webhook: str):
    """Check for failures and send Slack alerts."""
    
    # Find workflows failed in last 5 minutes
    cutoff = datetime.utcnow() - timedelta(minutes=5)
    query = f"ExecutionStatus='Failed' AND CloseTime > '{cutoff.isoformat()}Z'"
    
    failed_workflows = []
    async for workflow in client.list_workflows(query=query):
        failed_workflows.append({
            "id": workflow.id,
            "type": workflow.workflow_type,
            "close_time": str(workflow.close_time),
        })
    
    if failed_workflows:
        message = {
            "text": f":warning: {len(failed_workflows)} workflow(s) failed in last 5 minutes",
            "attachments": [
                {
                    "color": "danger",
                    "fields": [
                        {"title": "Workflow ID", "value": w["id"], "short": True},
                        {"title": "Type", "value": w["type"], "short": True},
                    ]
                }
                for w in failed_workflows[:5]  # Limit to 5
            ]
        }
        
        async with httpx.AsyncClient() as http:
            await http.post(slack_webhook, json=message)

async def alert_loop():
    client = await get_cloud_client()
    slack_webhook = os.environ["SLACK_WEBHOOK_URL"]
    
    while True:
        await check_and_alert(client, slack_webhook)
        await asyncio.sleep(300)  # Check every 5 minutes
```

### PagerDuty Integration

```python
# pagerduty_alerts.py
import httpx
from datetime import datetime

async def send_pagerduty_alert(
    routing_key: str,
    summary: str,
    severity: str = "error",
    source: str = "temporal-cloud",
):
    """Send alert to PagerDuty."""
    
    payload = {
        "routing_key": routing_key,
        "event_action": "trigger",
        "payload": {
            "summary": summary,
            "severity": severity,
            "source": source,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=payload,
        )
        return response.json()

# Usage
await send_pagerduty_alert(
    routing_key=os.environ["PAGERDUTY_ROUTING_KEY"],
    summary="Temporal: 10+ workflow failures in last hour",
    severity="critical",
)
```

---

## Cost Optimization

### Workflow Design for Cost

```python
# Minimize actions (each activity counts toward billing)

# BAD - Too many activities
@workflow.defn
class ExpensiveWorkflow:
    @workflow.run
    async def run(self, items: list):
        for item in items:
            await workflow.execute_activity(process_item, item, ...)

# GOOD - Batch processing
@workflow.defn
class EfficientWorkflow:
    @workflow.run
    async def run(self, items: list):
        # Process items in batches in single activity
        await workflow.execute_activity(
            process_batch,
            items,
            start_to_close_timeout=timedelta(minutes=10),
        )
```

### Monitor Usage

```bash
# Check namespace usage via tcld
tcld namespace get --namespace my-namespace

# View usage in Temporal Cloud console
# Settings > Usage > View monthly actions
```

---

## Migration: Self-Hosted to Cloud

### 1. Export Workflow Definitions

No code changes needed - same SDK works with Cloud.

### 2. Update Connection Configuration

```python
# Before (self-hosted)
client = await Client.connect("localhost:7233")

# After (Temporal Cloud)
client = await Client.connect(
    "namespace.account.tmprl.cloud:7233",
    namespace="namespace",
    tls=TLSConfig(...),
)
```

### 3. Parallel Running

```python
# Run workers for both during migration
async def run_migration_workers():
    # Old self-hosted
    old_client = await Client.connect("old-server:7233")
    old_worker = Worker(old_client, task_queue="old-queue", ...)
    
    # New cloud
    new_client = await get_cloud_client()
    new_worker = Worker(new_client, task_queue="cloud-queue", ...)
    
    await asyncio.gather(
        old_worker.run(),
        new_worker.run(),
    )
```

### 4. Redirect New Workflows

```python
# Gradually shift traffic
import random

async def start_workflow(input: dict):
    if random.random() < 0.1:  # 10% to cloud
        client = await get_cloud_client()
        task_queue = "cloud-queue"
    else:
        client = await get_old_client()
        task_queue = "old-queue"
    
    return await client.execute_workflow(
        MyWorkflow.run,
        input,
        id=f"workflow-{uuid4()}",
        task_queue=task_queue,
    )
```

---

## CLI Reference (tcld)

```bash
# Login
tcld login

# Namespaces
tcld namespace list
tcld namespace get --namespace NAME
tcld namespace update --namespace NAME --retention 30d

# Certificates
tcld namespace add-certificate --namespace NAME --certificate-file FILE
tcld namespace list-certificates --namespace NAME

# Users
tcld user list
tcld user invite --email user@example.com --namespace-role admin

# API Keys
tcld apikey create --name my-key --namespace NAME
tcld apikey list
```

---

**Next:** See **temporal-performance.md** for tuning and capacity planning.
