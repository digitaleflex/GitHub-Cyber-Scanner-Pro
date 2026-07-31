# Temporal Performance

> **Tuning, Benchmarking, and Capacity Planning**  
> Optimize Temporal for high-throughput production workloads.

## Overview

| Area | Focus |
|------|-------|
| **Worker Tuning** | Concurrency, caching, resource allocation |
| **Activity Optimization** | Timeout, batching, heartbeat strategies |
| **Workflow Optimization** | History size, continue-as-new, child workflows |
| **MySQL Tuning** | Connection pooling, query optimization |
| **Capacity Planning** | Scaling formulas, resource estimation |

---

## Worker Tuning

### Concurrency Configuration

```python
from temporalio.worker import Worker
from datetime import timedelta

worker = Worker(
    client,
    task_queue="high-throughput-queue",
    workflows=[...],
    activities=[...],
    
    # === Concurrency Limits ===
    
    # Maximum concurrent workflow task executions
    # Higher = more workflows in parallel
    # Default: 100
    max_concurrent_workflow_tasks=200,
    
    # Maximum concurrent activity executions
    # Higher = more activities in parallel
    # Default: 100
    max_concurrent_activities=500,
    
    # Maximum concurrent local activities
    # Default: 100
    max_concurrent_local_activities=100,
    
    # === Caching ===
    
    # Maximum cached workflows (for sticky execution)
    # Higher = less replay, more memory
    # Default: 1000
    max_cached_workflows=2000,
    
    # === Shutdown ===
    
    # Time to wait for in-flight work
    graceful_shutdown_timeout=timedelta(seconds=60),
)
```

### Memory-Based Tuning

```python
import psutil

def calculate_worker_limits() -> dict:
    """Calculate worker limits based on available memory."""
    
    # Get available memory in MB
    available_mb = psutil.virtual_memory().available / 1024 / 1024
    
    # Estimate memory per workflow (1-5 MB typical)
    mb_per_workflow = 3
    
    # Estimate memory per activity (varies by activity)
    mb_per_activity = 10
    
    # Reserve 30% for system
    usable_mb = available_mb * 0.7
    
    # Split between workflows and activities
    workflow_mb = usable_mb * 0.3
    activity_mb = usable_mb * 0.7
    
    return {
        "max_concurrent_workflow_tasks": int(workflow_mb / mb_per_workflow),
        "max_cached_workflows": int(workflow_mb / mb_per_workflow) * 2,
        "max_concurrent_activities": int(activity_mb / mb_per_activity),
    }

# Usage
limits = calculate_worker_limits()
worker = Worker(client, task_queue="queue", **limits, ...)
```

### CPU-Based Tuning

```python
import os

def calculate_cpu_based_limits() -> dict:
    """Calculate limits based on CPU cores."""
    
    cpu_count = os.cpu_count() or 4
    
    return {
        # Workflows are lightweight - many per core
        "max_concurrent_workflow_tasks": cpu_count * 50,
        
        # Activities depend on I/O vs CPU bound
        # I/O bound: Higher multiplier
        # CPU bound: Lower multiplier
        "max_concurrent_activities": cpu_count * 25,  # I/O bound
        # "max_concurrent_activities": cpu_count * 2,  # CPU bound
    }
```

### Activity Thread Pool

```python
from concurrent.futures import ThreadPoolExecutor

# Custom thread pool for sync activities
activity_executor = ThreadPoolExecutor(
    max_workers=50,
    thread_name_prefix="temporal-activity-",
)

worker = Worker(
    client,
    task_queue="queue",
    workflows=[...],
    activities=[...],
    activity_executor=activity_executor,
)
```

---

## Activity Optimization

### Timeout Strategy

```python
from temporalio.common import RetryPolicy
from datetime import timedelta

# Fast activities (API calls, simple DB queries)
FAST_ACTIVITY_CONFIG = {
    "start_to_close_timeout": timedelta(seconds=30),
    "retry_policy": RetryPolicy(
        initial_interval=timedelta(milliseconds=100),
        maximum_interval=timedelta(seconds=5),
        maximum_attempts=3,
    ),
}

# Medium activities (complex processing)
MEDIUM_ACTIVITY_CONFIG = {
    "start_to_close_timeout": timedelta(minutes=5),
    "retry_policy": RetryPolicy(
        initial_interval=timedelta(seconds=1),
        maximum_interval=timedelta(seconds=30),
        maximum_attempts=5,
    ),
}

# Long activities (file processing, batch jobs)
LONG_ACTIVITY_CONFIG = {
    "start_to_close_timeout": timedelta(hours=1),
    "heartbeat_timeout": timedelta(seconds=30),
    "retry_policy": RetryPolicy(
        initial_interval=timedelta(seconds=5),
        maximum_interval=timedelta(minutes=5),
        maximum_attempts=3,
    ),
}
```

### Batch Processing

```python
# BAD - One activity per item (slow, many round-trips)
@workflow.defn
class SlowWorkflow:
    @workflow.run
    async def run(self, items: list) -> list:
        results = []
        for item in items:
            result = await workflow.execute_activity(
                process_item,
                item,
                start_to_close_timeout=timedelta(seconds=30),
            )
            results.append(result)
        return results

# GOOD - Batch items in single activity
@workflow.defn
class FastWorkflow:
    @workflow.run
    async def run(self, items: list) -> list:
        # Process in batches of 100
        batch_size = 100
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await workflow.execute_activity(
                process_batch,
                batch,
                start_to_close_timeout=timedelta(minutes=5),
            )
            results.extend(batch_results)
        
        return results

@activity.defn
async def process_batch(items: list) -> list:
    """Process multiple items in single activity."""
    return [process_item_sync(item) for item in items]
```

### Parallel Activity Execution

```python
import asyncio

@workflow.defn
class ParallelWorkflow:
    @workflow.run
    async def run(self, items: list) -> list:
        # Execute activities in parallel
        tasks = [
            workflow.execute_activity(
                process_item,
                item,
                start_to_close_timeout=timedelta(seconds=30),
            )
            for item in items
        ]
        
        # Gather all results
        results = await asyncio.gather(*tasks)
        return results
```

### Connection Pooling in Activities

```python
# Reuse connections across activity executions
from contextlib import asynccontextmanager
import httpx

# Global connection pool (created at worker startup)
_http_client: httpx.AsyncClient = None

def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=50,
            ),
            timeout=30.0,
        )
    return _http_client

@activity.defn
async def call_api(url: str) -> dict:
    """Activity with connection pooling."""
    client = get_http_client()
    response = await client.get(url)
    return response.json()
```

---

## Workflow Optimization

### Minimize History Size

```python
# BAD - Large payload stored in history
@workflow.defn
class LargePayloadWorkflow:
    @workflow.run
    async def run(self, large_data: dict) -> dict:
        # large_data is stored in workflow history!
        result = await workflow.execute_activity(
            process,
            large_data,  # This bloats history
            start_to_close_timeout=timedelta(minutes=5),
        )
        return result

# GOOD - Store reference, fetch in activity
@workflow.defn
class SmallPayloadWorkflow:
    @workflow.run
    async def run(self, data_id: str) -> dict:
        # Only ID stored in history
        result = await workflow.execute_activity(
            process_by_id,
            data_id,  # Small reference
            start_to_close_timeout=timedelta(minutes=5),
        )
        return result

@activity.defn
async def process_by_id(data_id: str) -> dict:
    """Fetch data in activity, not workflow."""
    data = await fetch_from_storage(data_id)
    return process(data)
```

### Continue-As-New for Long Workflows

```python
@workflow.defn
class LongRunningWorkflow:
    """Process items with continue-as-new to prevent history growth."""
    
    MAX_EVENTS_PER_RUN = 1000
    
    @workflow.run
    async def run(self, state: dict) -> dict:
        processed = state.get("processed", 0)
        cursor = state.get("cursor", None)
        events_this_run = 0
        
        while True:
            # Check if we need to continue-as-new
            info = workflow.info()
            if info.get_current_history_length() > self.MAX_EVENTS_PER_RUN:
                workflow.continue_as_new({
                    "processed": processed,
                    "cursor": cursor,
                })
            
            # Fetch next batch
            batch = await workflow.execute_activity(
                fetch_batch,
                cursor,
                start_to_close_timeout=timedelta(minutes=1),
            )
            
            if not batch["items"]:
                return {"total_processed": processed}
            
            # Process batch
            for item in batch["items"]:
                await workflow.execute_activity(
                    process_item,
                    item,
                    start_to_close_timeout=timedelta(minutes=5),
                )
                processed += 1
            
            cursor = batch.get("next_cursor")
```

### Use Child Workflows for Isolation

```python
@workflow.defn
class ParentWorkflow:
    @workflow.run
    async def run(self, orders: list) -> dict:
        # Process each order in isolated child workflow
        # This limits parent history size
        results = []
        
        for order in orders:
            result = await workflow.execute_child_workflow(
                OrderWorkflow.run,
                order,
                id=f"order-{order['id']}",
            )
            results.append(result)
        
        return {"processed": len(results)}
```

---

## MySQL Performance

### Connection Pool Configuration

```python
# For activities that need database access
import asyncpg
from contextlib import asynccontextmanager

class DatabasePool:
    _pool = None
    
    @classmethod
    async def get_pool(cls):
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                host="localhost",
                port=5432,
                user="temporal",
                password="password",
                database="myapp",
                min_size=10,
                max_size=50,
                command_timeout=30,
            )
        return cls._pool
    
    @classmethod
    @asynccontextmanager
    async def connection(cls):
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            yield conn

@activity.defn
async def query_database(query: str) -> list:
    async with DatabasePool.connection() as conn:
        return await conn.fetch(query)
```

### MySQL Tuning for Temporal

```ini
# /etc/mysql/conf.d/temporal-perf.cnf
[mysqld]
# Connection handling
max_connections = 1000
wait_timeout = 600
interactive_timeout = 600
thread_cache_size = 100

# InnoDB performance
innodb_buffer_pool_size = 8G           # 70-80% of RAM
innodb_buffer_pool_instances = 8       # 1 per GB
innodb_log_file_size = 2G
innodb_log_buffer_size = 256M
innodb_flush_log_at_trx_commit = 2     # Trade durability for speed
innodb_flush_method = O_DIRECT
innodb_io_capacity = 2000
innodb_io_capacity_max = 4000

# Query optimization
join_buffer_size = 256K
sort_buffer_size = 256K
read_rnd_buffer_size = 256K

# Temp tables
tmp_table_size = 256M
max_heap_table_size = 256M
```

### Query Performance Monitoring

```sql
-- Enable slow query log
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
SET GLOBAL log_queries_not_using_indexes = 'ON';

-- Check current connections
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';

-- InnoDB status
SHOW ENGINE INNODB STATUS;

-- Table sizes
SELECT 
    table_name,
    ROUND(data_length / 1024 / 1024, 2) AS data_mb,
    ROUND(index_length / 1024 / 1024, 2) AS index_mb,
    table_rows
FROM information_schema.tables
WHERE table_schema = 'temporal'
ORDER BY data_length DESC;
```

---

## Benchmarking

### Simple Throughput Test

```python
# benchmark.py
import asyncio
import time
from temporalio.client import Client
from uuid import uuid4

async def benchmark_workflow_throughput(
    num_workflows: int = 1000,
    concurrency: int = 100,
):
    """Measure workflow execution throughput."""
    
    client = await Client.connect("localhost:7233")
    
    start_time = time.time()
    completed = 0
    
    async def execute_one():
        nonlocal completed
        await client.execute_workflow(
            BenchmarkWorkflow.run,
            {"data": "test"},
            id=f"bench-{uuid4()}",
            task_queue="benchmark-queue",
        )
        completed += 1
    
    # Run with concurrency limit
    semaphore = asyncio.Semaphore(concurrency)
    
    async def limited_execute():
        async with semaphore:
            await execute_one()
    
    tasks = [limited_execute() for _ in range(num_workflows)]
    await asyncio.gather(*tasks)
    
    duration = time.time() - start_time
    throughput = num_workflows / duration
    
    print(f"Completed: {completed} workflows")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Throughput: {throughput:.2f} workflows/second")
    
    return {
        "completed": completed,
        "duration_seconds": duration,
        "throughput_per_second": throughput,
    }

if __name__ == "__main__":
    asyncio.run(benchmark_workflow_throughput())
```

### Activity Latency Test

```python
# activity_benchmark.py
import asyncio
import time
import statistics

async def benchmark_activity_latency(iterations: int = 100):
    """Measure activity execution latency."""
    
    client = await Client.connect("localhost:7233")
    latencies = []
    
    for i in range(iterations):
        start = time.time()
        
        await client.execute_workflow(
            SingleActivityWorkflow.run,
            {"iteration": i},
            id=f"latency-test-{i}",
            task_queue="benchmark-queue",
        )
        
        latency = (time.time() - start) * 1000  # ms
        latencies.append(latency)
    
    print(f"Iterations: {iterations}")
    print(f"Mean latency: {statistics.mean(latencies):.2f} ms")
    print(f"Median latency: {statistics.median(latencies):.2f} ms")
    print(f"P95 latency: {sorted(latencies)[int(iterations * 0.95)]:.2f} ms")
    print(f"P99 latency: {sorted(latencies)[int(iterations * 0.99)]:.2f} ms")
    print(f"Min latency: {min(latencies):.2f} ms")
    print(f"Max latency: {max(latencies):.2f} ms")
```

### Load Test Script

```bash
#!/bin/bash
# load_test.sh

# Configuration
DURATION=300  # 5 minutes
RATE=100      # workflows per second
QUEUE="load-test-queue"

echo "Starting load test: $RATE workflows/second for $DURATION seconds"

end_time=$(($(date +%s) + $DURATION))
count=0

while [ $(date +%s) -lt $end_time ]; do
    for i in $(seq 1 $RATE); do
        temporal workflow execute \
            --workflow-id "load-$(date +%s)-$i" \
            --task-queue $QUEUE \
            --type LoadTestWorkflow \
            --input '{}' &
        count=$((count + 1))
    done
    sleep 1
done

wait

echo "Completed: $count workflows"
```

---

## Capacity Planning

### Workflow Estimation

```python
def estimate_workflow_capacity(
    workflows_per_day: int,
    avg_activities_per_workflow: int,
    avg_activity_duration_seconds: float,
    peak_multiplier: float = 3.0,
) -> dict:
    """Estimate required capacity."""
    
    # Peak workflows per second
    peak_wf_per_sec = (workflows_per_day / 86400) * peak_multiplier
    
    # Peak activities per second
    peak_act_per_sec = peak_wf_per_sec * avg_activities_per_workflow
    
    # Workers needed (assuming 100 concurrent activities per worker)
    activities_per_worker = 100
    workers_needed = max(1, int(peak_act_per_sec * avg_activity_duration_seconds / activities_per_worker) + 1)
    
    # MySQL connections (2 per workflow + overhead)
    mysql_connections = workers_needed * 50 + 100
    
    return {
        "peak_workflows_per_second": peak_wf_per_sec,
        "peak_activities_per_second": peak_act_per_sec,
        "workers_recommended": workers_needed,
        "mysql_connections_recommended": mysql_connections,
        "worker_config": {
            "max_concurrent_activities": activities_per_worker,
            "max_concurrent_workflow_tasks": 100,
        },
    }

# Example
capacity = estimate_workflow_capacity(
    workflows_per_day=100_000,
    avg_activities_per_workflow=5,
    avg_activity_duration_seconds=2.0,
)
print(capacity)
```

### Resource Sizing Guide

| Workload | Workers | CPU (per worker) | RAM (per worker) | MySQL Connections |
|----------|---------|------------------|------------------|-------------------|
| Light (1K/day) | 1-2 | 1 core | 1 GB | 50 |
| Medium (10K/day) | 2-4 | 2 cores | 2 GB | 100 |
| Heavy (100K/day) | 5-10 | 4 cores | 4 GB | 250 |
| Enterprise (1M/day) | 20-50 | 4 cores | 8 GB | 500 |

### MySQL Sizing

| Workload | CPU | RAM | Disk | Buffer Pool |
|----------|-----|-----|------|-------------|
| Light | 2 cores | 4 GB | 50 GB SSD | 2 GB |
| Medium | 4 cores | 8 GB | 100 GB SSD | 5 GB |
| Heavy | 8 cores | 16 GB | 250 GB SSD | 10 GB |
| Enterprise | 16 cores | 64 GB | 500 GB SSD | 40 GB |

---

## Monitoring Metrics

### Key Performance Indicators

```python
# metrics.py
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class PerformanceMetrics:
    timestamp: datetime
    workflow_throughput: float  # per second
    activity_throughput: float  # per second
    avg_workflow_latency_ms: float
    avg_activity_latency_ms: float
    p99_latency_ms: float
    active_workers: int
    pending_tasks: int
    failed_rate: float  # percentage

async def collect_metrics(client: Client) -> PerformanceMetrics:
    """Collect performance metrics."""
    
    # Count running workflows
    running = 0
    async for _ in client.list_workflows(query="ExecutionStatus='Running'"):
        running += 1
    
    # Count completed in last minute
    cutoff = datetime.utcnow() - timedelta(minutes=1)
    completed = 0
    async for _ in client.list_workflows(
        query=f"ExecutionStatus='Completed' AND CloseTime > '{cutoff.isoformat()}Z'"
    ):
        completed += 1
    
    # Count failed in last minute
    failed = 0
    async for _ in client.list_workflows(
        query=f"ExecutionStatus='Failed' AND CloseTime > '{cutoff.isoformat()}Z'"
    ):
        failed += 1
    
    total = completed + failed
    
    return PerformanceMetrics(
        timestamp=datetime.utcnow(),
        workflow_throughput=completed / 60,
        activity_throughput=0,  # Requires custom tracking
        avg_workflow_latency_ms=0,  # Requires custom tracking
        avg_activity_latency_ms=0,
        p99_latency_ms=0,
        active_workers=0,  # Get from task queue describe
        pending_tasks=running,
        failed_rate=(failed / total * 100) if total > 0 else 0,
    )
```

### Alerting Thresholds

```python
ALERT_THRESHOLDS = {
    "workflow_latency_p99_ms": 5000,  # 5 seconds
    "activity_latency_p99_ms": 10000,  # 10 seconds
    "failed_rate_percent": 1.0,  # 1%
    "pending_tasks_count": 1000,  # Backlog threshold
    "worker_count_min": 2,  # Minimum workers
}

def check_thresholds(metrics: PerformanceMetrics) -> list:
    """Check metrics against thresholds."""
    alerts = []
    
    if metrics.p99_latency_ms > ALERT_THRESHOLDS["workflow_latency_p99_ms"]:
        alerts.append(f"High latency: {metrics.p99_latency_ms}ms")
    
    if metrics.failed_rate > ALERT_THRESHOLDS["failed_rate_percent"]:
        alerts.append(f"High failure rate: {metrics.failed_rate}%")
    
    if metrics.pending_tasks > ALERT_THRESHOLDS["pending_tasks_count"]:
        alerts.append(f"Large backlog: {metrics.pending_tasks} pending")
    
    return alerts
```

---

## Performance Checklist

### Worker Optimization
- [ ] Concurrency limits tuned for workload
- [ ] Cached workflows sized appropriately
- [ ] Thread pool configured for sync activities
- [ ] Graceful shutdown timeout set

### Activity Optimization
- [ ] Appropriate timeouts configured
- [ ] Batch processing where applicable
- [ ] Connection pooling enabled
- [ ] Heartbeating for long activities

### Workflow Optimization
- [ ] Minimal payload sizes
- [ ] Continue-as-new for long workflows
- [ ] Child workflows for isolation
- [ ] No blocking operations in workflow code

### MySQL Optimization
- [ ] Buffer pool sized to 70-80% RAM
- [ ] Connection pool configured
- [ ] Slow query logging enabled
- [ ] Regular ANALYZE TABLE scheduled

### Monitoring
- [ ] Throughput metrics collected
- [ ] Latency percentiles tracked
- [ ] Failed workflow alerts configured
- [ ] Backlog monitoring enabled

---

**Reference:** See **temporal-operations.md** for production maintenance procedures.
