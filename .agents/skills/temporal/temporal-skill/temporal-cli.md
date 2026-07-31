# Temporal CLI Reference

> Complete reference for Temporal CLI commands

## Installation

```bash
# macOS
brew install temporal

# Linux
curl -sSf https://temporal.download/cli.sh | sh

# Verify installation
temporal --version
```

---

## Server Commands

### Start Development Server

```bash
# Basic start
temporal server start-dev

# Custom ports
temporal server start-dev --port 7233 --ui-port 8233

# With custom namespace
temporal server start-dev --namespace my-namespace

# Persistent database
temporal server start-dev --db-filename /path/to/temporal.db

# Combined options
temporal server start-dev \
  --port 7233 \
  --ui-port 8233 \
  --namespace development \
  --db-filename ./temporal.db \
  --log-level info
```

---

## Workflow Commands

### Start Workflow

```bash
# Basic start
temporal workflow start \
  --workflow-id "my-workflow-123" \
  --task-queue "my-queue" \
  --type "MyWorkflow" \
  --input '{"key": "value"}'

# Start with multiple inputs
temporal workflow start \
  --workflow-id "my-workflow" \
  --task-queue "my-queue" \
  --type "MyWorkflow" \
  --input '"arg1"' \
  --input '{"key": "value"}'

# Start and wait for completion
temporal workflow execute \
  --workflow-id "my-workflow" \
  --task-queue "my-queue" \
  --type "MyWorkflow" \
  --input '{"key": "value"}'
```

### List Workflows

```bash
# List all workflows
temporal workflow list

# List running workflows
temporal workflow list --query "ExecutionStatus='Running'"

# List failed workflows
temporal workflow list --query "ExecutionStatus='Failed'"

# List by type
temporal workflow list --query "WorkflowType='OrderWorkflow'"

# List with time filter
temporal workflow list --query "StartTime > '2024-01-01'"

# List with multiple filters
temporal workflow list --query "WorkflowType='OrderWorkflow' AND ExecutionStatus='Running'"

# JSON output
temporal workflow list --output json
```

### Describe Workflow

```bash
# Get workflow details
temporal workflow describe --workflow-id "my-workflow"

# With run ID
temporal workflow describe --workflow-id "my-workflow" --run-id "abc123"

# JSON output
temporal workflow describe --workflow-id "my-workflow" --output json
```

### Show History

```bash
# Show event history
temporal workflow show --workflow-id "my-workflow"

# JSON output
temporal workflow show --workflow-id "my-workflow" --output json

# Follow (watch in real-time)
temporal workflow show --workflow-id "my-workflow" --follow

# Show specific events
temporal workflow show --workflow-id "my-workflow" \
  | grep -A 5 "ActivityTaskScheduled"
```

### Get Result

```bash
# Get workflow result
temporal workflow result --workflow-id "my-workflow"

# With run ID
temporal workflow result --workflow-id "my-workflow" --run-id "abc123"
```

### Query Workflow

```bash
# Query workflow state
temporal workflow query \
  --workflow-id "my-workflow" \
  --query-type "get_status"

# Query with arguments
temporal workflow query \
  --workflow-id "my-workflow" \
  --query-type "get_items" \
  --input '"pending"'
```

### Signal Workflow

```bash
# Send signal
temporal workflow signal \
  --workflow-id "my-workflow" \
  --signal-name "approve" \
  --input '{"approver": "admin"}'

# Signal without input
temporal workflow signal \
  --workflow-id "my-workflow" \
  --signal-name "stop"
```

### Cancel Workflow

```bash
# Cancel (graceful)
temporal workflow cancel --workflow-id "my-workflow"

# With reason
temporal workflow cancel \
  --workflow-id "my-workflow" \
  --reason "User requested cancellation"
```

### Terminate Workflow

```bash
# Terminate (immediate)
temporal workflow terminate --workflow-id "my-workflow"

# With reason
temporal workflow terminate \
  --workflow-id "my-workflow" \
  --reason "Manual termination"
```

### Reset Workflow

```bash
# Reset to specific event
temporal workflow reset \
  --workflow-id "my-workflow" \
  --event-id 5 \
  --reason "Replay from event 5"

# Reset all workflows of a type
temporal workflow reset-batch \
  --query "WorkflowType='MyWorkflow' AND ExecutionStatus='Failed'" \
  --reason "Bulk reset"
```

### Count Workflows

```bash
# Count running workflows
temporal workflow count --query "ExecutionStatus='Running'"

# Count by type
temporal workflow count --query "WorkflowType='OrderWorkflow'"
```

### Stack Trace

```bash
# Get stack trace (for debugging stuck workflows)
temporal workflow stack --workflow-id "my-workflow"
```

---

## Schedule Commands

### Create Schedule

```bash
# Create with cron
temporal schedule create \
  --schedule-id "daily-report" \
  --cron "0 9 * * *" \
  --workflow-id "daily-report" \
  --task-queue "reports" \
  --workflow-type "ReportWorkflow" \
  --input '{"type": "daily"}'

# Create with interval
temporal schedule create \
  --schedule-id "health-check" \
  --interval "5m" \
  --workflow-id "health-check" \
  --task-queue "monitoring" \
  --workflow-type "HealthCheckWorkflow"
```

### List Schedules

```bash
temporal schedule list
temporal schedule list --output json
```

### Describe Schedule

```bash
temporal schedule describe --schedule-id "daily-report"
```

### Trigger Schedule

```bash
# Trigger immediate execution
temporal schedule trigger --schedule-id "daily-report"
```

### Pause/Unpause

```bash
# Pause
temporal schedule toggle \
  --schedule-id "daily-report" \
  --pause \
  --reason "Maintenance"

# Unpause
temporal schedule toggle \
  --schedule-id "daily-report" \
  --unpause \
  --reason "Maintenance complete"
```

### Update Schedule

```bash
temporal schedule update \
  --schedule-id "daily-report" \
  --cron "0 10 * * *"
```

### Delete Schedule

```bash
temporal schedule delete --schedule-id "daily-report"
```

### Backfill

```bash
temporal schedule backfill \
  --schedule-id "daily-report" \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-07T00:00:00Z"
```

---

## Task Queue Commands

### Describe Task Queue

```bash
temporal task-queue describe --task-queue "my-queue"
```

### List Pollers

```bash
temporal task-queue get-build-ids --task-queue "my-queue"
```

---

## Namespace Commands

### List Namespaces

```bash
temporal operator namespace list
```

### Describe Namespace

```bash
temporal operator namespace describe --namespace "default"
```

### Create Namespace

```bash
temporal operator namespace create --namespace "my-namespace"
```

### Update Namespace

```bash
temporal operator namespace update \
  --namespace "my-namespace" \
  --description "My custom namespace"
```

---

## Cluster Commands

### Describe Cluster

```bash
temporal operator cluster describe
```

### Health Check

```bash
temporal operator cluster health
```

---

## Environment Variables

```bash
# Temporal address
export TEMPORAL_ADDRESS=localhost:7233

# Namespace
export TEMPORAL_NAMESPACE=default

# TLS configuration
export TEMPORAL_TLS_CERT=/path/to/cert.pem
export TEMPORAL_TLS_KEY=/path/to/key.pem
export TEMPORAL_TLS_CA=/path/to/ca.pem
```

---

## Query Syntax

### Supported Fields

| Field | Description | Example |
|-------|-------------|---------|
| `WorkflowId` | Workflow ID | `WorkflowId='order-123'` |
| `WorkflowType` | Workflow type name | `WorkflowType='OrderWorkflow'` |
| `ExecutionStatus` | Status | `ExecutionStatus='Running'` |
| `StartTime` | Start time | `StartTime > '2024-01-01'` |
| `CloseTime` | Close time | `CloseTime < '2024-01-02'` |
| `TaskQueue` | Task queue name | `TaskQueue='orders'` |

### Execution Status Values

- `Running`
- `Completed`
- `Failed`
- `Canceled`
- `Terminated`
- `ContinuedAsNew`
- `TimedOut`

### Operators

```bash
# Equals
--query "WorkflowType='OrderWorkflow'"

# Not equals
--query "ExecutionStatus != 'Completed'"

# Greater/less than
--query "StartTime > '2024-01-01'"

# AND
--query "WorkflowType='OrderWorkflow' AND ExecutionStatus='Running'"

# OR
--query "ExecutionStatus='Failed' OR ExecutionStatus='TimedOut'"

# Parentheses
--query "(WorkflowType='A' OR WorkflowType='B') AND ExecutionStatus='Running'"
```

---

## Output Formats

```bash
# Table (default)
temporal workflow list

# JSON
temporal workflow list --output json

# JSON with specific fields
temporal workflow list --output json | jq '.executions[].workflowId'

# Pretty JSON
temporal workflow describe --workflow-id "test" --output json | jq
```

---

## Common Workflows

### Debug Failed Workflow

```bash
# 1. Find failed workflows
temporal workflow list --query "ExecutionStatus='Failed'"

# 2. Get details
temporal workflow describe --workflow-id "failed-workflow"

# 3. View history
temporal workflow show --workflow-id "failed-workflow"

# 4. Get stack trace
temporal workflow stack --workflow-id "failed-workflow"

# 5. Reset and retry
temporal workflow reset \
  --workflow-id "failed-workflow" \
  --event-id 10 \
  --reason "Retry after fix"
```

### Monitor Running Workflow

```bash
# Watch in real-time
temporal workflow show --workflow-id "my-workflow" --follow

# Query status
temporal workflow query \
  --workflow-id "my-workflow" \
  --query-type "get_status"
```

### Batch Operations

```bash
# Terminate all failed workflows of a type
for wf in $(temporal workflow list \
  --query "WorkflowType='MyWorkflow' AND ExecutionStatus='Failed'" \
  --output json | jq -r '.executions[].workflowId'); do
  temporal workflow terminate --workflow-id "$wf" --reason "Batch cleanup"
done
```

---

## Tips

1. **Use aliases** for common commands:
   ```bash
   alias twl='temporal workflow list'
   alias twd='temporal workflow describe --workflow-id'
   alias tws='temporal workflow show --workflow-id'
   ```

2. **Pipe to jq** for JSON processing:
   ```bash
   temporal workflow list --output json | jq '.executions | length'
   ```

3. **Use --follow** to watch workflows:
   ```bash
   temporal workflow show --workflow-id "my-wf" --follow
   ```

4. **Export environment variables** for repeated use:
   ```bash
   export TEMPORAL_NAMESPACE=production
   temporal workflow list  # Uses production namespace
   ```

---

## Next Steps

- **temporal-testing.md** - Testing workflows
- **temporal-advanced.md** - Advanced patterns
- **temporal-production.md** - Production deployment
