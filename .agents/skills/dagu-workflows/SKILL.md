---
description: Comprehensive Dagu workflow orchestration skill for creating, managing, and automating workflows with Dagu - a compact portable workflow engine. Covers all step types, scheduling patterns, error handling, and deployment strategies.
name: dagu-workflows
---

# Dagu Workflow Orchestration Skill

Expert-level skill for building, deploying, and managing Dagu workflows for task orchestration, automation, and pipeline management.

## Overview

Dagu is a compact, portable workflow engine that provides declarative orchestration of command execution across diverse environments. This skill covers complete workflow design patterns from simple cron replacements to complex multi-step pipelines with error handling, notifications, and distributed execution.

## What Dagu Can Do

- **Task Orchestration**: Chain shell commands, scripts, Docker containers, or remote SSH commands
- **Scheduling**: Cron-based scheduling, one-time execution, or event-driven triggers
- **Error Handling**: Automatic retry with exponential backoff, failure notifications, error isolation
- **Parallel Execution**: Run steps concurrently with dependency management
- **Monitoring**: Web UI, logs, history tracking, and status monitoring
- **Integration**: HTTP APIs, databases (PostgreSQL, SQLite), message queues (Redis), cloud storage (S3)

## What Dagu Cannot Do

- Long-running durable workflows (use Temporal instead for multi-day processes)
- Native event-driven triggers (requires external polling or webhooks)
- Stateful checkpointing across server restarts
- Complex decision trees with persistent state

## When to Use Dagu vs Alternatives

| Use Case | Use Dagu | Use Temporal |
|----------|----------|--------------|
| Cron job replacement | ✅ Perfect fit | ❌ Overkill |
| ETL pipelines (< 24 hours) | ✅ Ideal | ⚠️ Can work |
| Build/test automation | ✅ Great | ❌ Overkill |
| Multi-day business processes | ❌ Not suitable | ✅ Designed for this |
| Event-driven microservices | ⚠️ Needs wrapper | ✅ Native |
| Simple task chaining | ✅ Perfect | ❌ Overkill |

## Core Concepts

### DAG (Directed Acyclic Graph)
A workflow defined as steps with dependencies forming a graph. Steps run in order respecting dependencies - a step only runs after all its dependencies complete successfully.

### Execution Modes

**Chain Mode (Default)**: Steps run sequentially top-to-bottom
```yaml
steps:
  - command: step1.sh  # runs first
  - command: step2.sh  # waits for step1
  - command: step3.sh  # waits for step2
```

**Graph Mode**: Explicit dependencies, allows parallel execution
```yaml
type: graph
steps:
  - id: step_a
    command: echo A
    depends: []         # runs immediately
  - id: step_b
    command: echo B
    depends: [step_a]   # waits for step_a
  - id: step_c
    command: echo C
    depends: [step_a]   # runs in parallel with step_b
```

### Key Dagu 2.x Requirements
- Step IDs must use `snake_case` (not hyphens)
- Graph mode required for explicit dependencies
- All workflow files end in `.yaml`

## Workflow Structure

### Minimal Workflow
```yaml
steps:
  - command: echo "Hello from Dagu!"
```

### Complete Production Workflow
```yaml
# Metadata
name: data-pipeline
description: Daily ETL pipeline for sales data
owner: data-team@company.com
tags:
  - etl
  - production
  - sales

# Execution mode
type: graph

# Scheduling (cron format)
schedule:
  - "0 2 * * *"  # Daily at 2 AM

# Global settings
timeout_sec: 3600  # 1 hour max
max_active_steps: 3  # Parallelism limit

# Environment variables
env:
  - ENV: production
  - DB_HOST: db.company.com

# Secrets (referenced from Dagu secret store)
secrets:
  - DB_PASSWORD
  - API_KEY

# Parameters (user input or defaults)
params:
  - DATE: "2026-01-01"
  - DRY_RUN: "false"

# DAG-level retry (entire workflow)
retry_policy:
  limit: 3
  interval_sec: 300  # 5 minutes
  backoff: true

# Step definitions
steps:
  # Extract
  - id: extract_sales
    name: Extract Sales Data
    command: |
      psql -h ${DB_HOST} -U etl_user -c "
        COPY (SELECT * FROM sales WHERE date = '${DATE}')
        TO '/tmp/sales_${DATE}.csv'
        WITH CSV HEADER;
      "
    retry_policy:
      limit: 3
      interval_sec: 10
    timeout_sec: 300

  # Transform (parallel transforms possible)
  - id: transform_revenue
    name: Calculate Revenue
    depends: [extract_sales]
    command: python /scripts/calc_revenue.py --input /tmp/sales_${DATE}.csv
    output: REVENUE_DATA

  - id: transform_metrics
    name: Calculate Metrics
    depends: [extract_sales]
    command: python /scripts/calc_metrics.py --input /tmp/sales_${DATE}.csv
    output: METRICS_DATA

  # Load
  - id: load_warehouse
    name: Load to Data Warehouse
    depends: [transform_revenue, transform_metrics]
    command: |
      python /scripts/load_dw.py \
        --revenue ${REVENUE_DATA} \
        --metrics ${METRICS_DATA} \
        --date ${DATE}

  # Cleanup
  - id: cleanup
    name: Cleanup Temporary Files
    depends: [load_warehouse]
    command: rm -f /tmp/sales_${DATE}.csv
    continue_on:
      exit_code: [0, 1]  # Continue even if cleanup fails

# Lifecycle handlers
handler_on:
  success:
    command: notify.sh "ETL succeeded for ${DATE}"
  failure:
    command: pager.sh "ETL failed for ${DATE}"
  exit:
    command: rm -rf /tmp/${DAG_RUN_ID}

# Notifications
mail_on:
  failure: true
  success: false
```

## Step Types Reference

### Shell Steps (Most Common)
```yaml
steps:
  # Simple command
  - command: echo "Hello"

  # Multi-line script
  - command: |
      echo "Step 1"
      echo "Step 2"
      ./process.sh

  # With specific shell
  - command: python3 process.py
    executor: python3

  # With working directory
  - command: npm install
    working_dir: /app/frontend

  # Environment variables
  - command: python process.py
    env:
      - DEBUG: "1"
      - BATCH_SIZE: "1000"

  # Timeout
  - command: long_process.sh
    timeout_sec: 3600

  # Signal handling for graceful shutdown
  - command: server.sh
    signal_on_stop: SIGTERM  # Default, can use SIGINT, SIGKILL, etc.
```

### HTTP Steps
```yaml
steps:
  - type: http
    name: Fetch API Data
    config:
      url: https://api.example.com/data
      method: GET
      headers:
        Authorization: Bearer ${API_TOKEN}
        Content-Type: application/json
      timeout: 30
      silent: false  # Show response in logs
    output: API_RESPONSE
```

### Docker Steps
```yaml
steps:
  - type: docker
    name: Run Container
    config:
      image: python:3.11
      auto_remove: true
      volumes:
        - /host/data:/data
      environment:
        - ENV=production
      command: python /data/process.py
```

### SSH Steps (Remote Execution)
```yaml
steps:
  - type: ssh
    name: Deploy to Server
    config:
      host: prod-server-01
      user: deploy
      key: /home/user/.ssh/deploy_key
      command: |
        cd /app
        git pull
        docker-compose up -d
```

### JQ Steps (JSON Processing)
```yaml
steps:
  - type: jq
    name: Extract Price
    config:
      input: ${API_RESPONSE}  # From previous step
      query: .bitcoin.usd
    output: BTC_PRICE
```

### Mail Steps
```yaml
steps:
  - type: mail
    name: Send Report
    config:
      to: team@company.com
      from: dagu@company.com
      subject: "Daily Report - ${DATE}"
      message: |
        Revenue: ${REVENUE}
        Metrics: ${METRICS}
      attachments:
        - /tmp/report.pdf
```

### SQL Steps
```yaml
steps:
  # PostgreSQL
  - type: sql
    name: Query Database
    config:
      driver: postgres
      dsn: postgresql://user:pass@host/db
      query: SELECT * FROM sales WHERE date = $1
      args:
        - ${DATE}
    output: SALES_DATA

  # SQLite
  - type: sql
    name: Local Query
    config:
      driver: sqlite3
      dsn: /path/to/local.db
      query: SELECT count(*) FROM events
```

### Template Steps
```yaml
steps:
  - type: template
    name: Generate Config
    config:
      data:
        db_host: ${DB_HOST}
        db_name: ${DB_NAME}
    script: |
      #!/bin/bash
      cat > config.json << EOF
      {
        "database": {
          "host": "{{ .db_host }}",
          "name": "{{ .db_name }}"
        }
      }
      EOF
```

### S3 Steps
```yaml
steps:
  - type: s3
    name: Upload to S3
    config:
      endpoint: s3.amazonaws.com
      bucket: my-backup-bucket
      key: backups/${DATE}/data.tar.gz
      source: /tmp/data.tar.gz
      access_key: ${AWS_ACCESS_KEY}
      secret_key: ${AWS_SECRET_KEY}
```

## Scheduling Patterns

### Cron Scheduling
```yaml
# Every minute
schedule:
  - "* * * * *"

# Every 5 minutes
schedule:
  - "*/5 * * * *"

# Daily at midnight
schedule:
  - "0 0 * * *"

# Daily at 2 AM
schedule:
  - "0 2 * * *"

# Every Monday at 9 AM
schedule:
  - "0 9 * * 1"

# First day of month at midnight
schedule:
  - "0 0 1 * *"
```

### Multiple Schedules
```yaml
schedule:
  - "0 9 * * 1"    # Monday 9 AM
  - "0 14 * * 5"   # Friday 2 PM
```

### No Schedule (Manual/Event Triggered)
```yaml
# No schedule field - only runs manually or via API/webhook
name: on-demand-job
steps:
  - command: ./process.sh
```

## Error Handling & Retry

### Step-Level Retry
```yaml
steps:
  - id: fetch_api
    command: curl -fsS https://api.example.com/data
    retry_policy:
      limit: 5              # Max 5 retries
      interval_sec: 10      # Start with 10s delay
      exit_code: [6, 22, 28]  # Network errors only
      backoff: true         # Exponential: 10s, 20s, 40s, 60s
      max_interval_sec: 60  # Cap at 60s
```

### Default Retry (All Steps)
```yaml
defaults:
  retry_policy:
    limit: 3
    interval_sec: 5
    exit_code: [1, 2]

steps:
  - command: step1.sh  # Uses default retry
  - command: step2.sh  # Uses default retry
  - command: step3.sh
    retry_policy:
      limit: 0  # Override - no retry for this step
```

### DAG-Level Retry (Entire Workflow)
```yaml
retry_policy:
  limit: 3              # Retry whole DAG 3 times
  interval_sec: 300     # Wait 5 minutes between attempts
  backoff: true
  max_interval_sec: 3600  # Max 1 hour wait
```

### Continue On Failure
```yaml
steps:
  # Continue even if cleanup fails
  - command: rm -rf /tmp/cache
    continue_on:
      exit_code: [0, 1]  # 0=success, 1=minor error
      
  # Continue on specific output
  - command: ./validate.sh
    continue_on:
      output:
        - "WARNING"
        - "SKIP"
        - "re:^INFO:.*"  # Regex pattern
```

### Pre-Conditions
```yaml
steps:
  - command: ./deploy.sh
    preconditions:
      - condition: "${ENV}"
        expected: "production"
```

## Lifecycle Handlers

Run code when workflow reaches certain states:

```yaml
handler_on:
  # Run before any steps
  init:
    command: setup.sh ${DAG_NAME}
  
  # Run on successful completion
  success:
    command: notify.sh "${DAG_NAME} succeeded"
  
  # Run on failure
  failure:
    command: pager.sh "${DAG_NAME} failed"
  
  # Run on manual stop/timeout
  abort:
    command: rollback.sh
  
  # Run when waiting for approval
  wait:
    command: notify-slack.sh "Approval needed"
  
  # Always runs last (success or failure)
  exit:
    command: cleanup.sh
```

## Control Flow Patterns

### Sequential Execution (Default)
```yaml
steps:
  - command: step1.sh
  - command: step2.sh  # waits for step1
  - command: step3.sh  # waits for step2
```

### Parallel Execution
```yaml
type: graph
steps:
  - id: task_a
    command: echo A
    depends: []
  - id: task_b
    command: echo B
    depends: []
  - id: task_c
    command: echo C
    depends: []
  # All three run in parallel
```

### Fan-Out / Fan-In
```yaml
type: graph
steps:
  # Fan out: One to many
  - id: prepare
    command: prepare.sh
    depends: []
  
  - id: process_1
    command: process_1.sh
    depends: [prepare]
  - id: process_2
    command: process_2.sh
    depends: [prepare]
  - id: process_3
    command: process_3.sh
    depends: [prepare]
  # process_1, 2, 3 run in parallel after prepare
  
  # Fan in: Many to one
  - id: combine
    command: combine.sh
    depends: [process_1, process_2, process_3]
  # Waits for all three processes
```

### Diamond Pattern
```yaml
type: graph
steps:
  - id: start
    command: start.sh
    depends: []
  
  - id: left
    command: left.sh
    depends: [start]
  - id: right
    command: right.sh
    depends: [start]
  
  - id: end
    command: end.sh
    depends: [left, right]
```

### Conditional Execution
```yaml
steps:
  - id: check_env
    command: |
      if [ "${ENV}" = "production" ]; then
        exit 0
      else
        exit 1
      fi
    continue_on:
      exit_code: [0, 1]
  
  - id: prod_deploy
    depends: [check_env]
    command: deploy_prod.sh
    preconditions:
      - condition: "${ENV}"
        expected: "production"
```

### Loop Over Items
```yaml
steps:
  - call: process_file
    parallel:
      items:
        - file1.csv
        - file2.csv
        - file3.csv
      max_concurrent: 2  # Process 2 at a time
    params: "FILE=${ITEM}"

---
name: process_file
params:
  - FILE: ""
steps:
  - command: python process.py --file ${FILE}
```

## Data Flow & Variables

### Environment Variables
```yaml
# Global env (all steps)
env:
  - GLOBAL_VAR: "value"

steps:
  # Step-specific env
  - command: echo ${LOCAL_VAR}
    env:
      - LOCAL_VAR: "step_value"
      - GLOBAL_VAR: "overridden"  # Overrides global
```

### Step Output to Variable
```yaml
steps:
  - id: get_version
    command: cat VERSION
    output: VERSION_NUM  # Captures stdout
  
  - id: build
    depends: [get_version]
    command: |
      echo "Building version ${VERSION_NUM}"
      ./build.sh --version ${VERSION_NUM}
```

### Dynamic Variables
```yaml
env:
  - TODAY: "`date +%Y-%m-%d`"  # Evaluated at runtime
  - TIMESTAMP: "`date +%s`"
```

### Template Variables
```yaml
steps:
  - command: echo "Run ID: ${DAG_RUN_ID}"
  - command: echo "Started: ${DAG_RUN_STARTED_AT}"
  - command: echo "Status: ${DAG_RUN_STATUS}"
```

## Deployment Patterns

### Local Development
```bash
# Install
curl -fsSL https://dagu.dev/install.sh | sh

# Start server + scheduler
dagu start-all

# Access Web UI
open http://localhost:8080
```

### macOS Service (Persistent)
```bash
# Install
dagu server

# Create LaunchAgent plist
cat > ~/Library/LaunchAgents/com.dagu.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.dagu</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/bin/dagu</string>
    <string>start-all</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
EOF

# Load service
launchctl load ~/Library/LaunchAgents/com.dagu.plist
launchctl start com.dagu
```

### Linux Systemd
```bash
# Create service file
sudo tee /etc/systemd/system/dagu.service << 'EOF'
[Unit]
Description=Dagu Workflow Scheduler
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/dagu start-all
Restart=always
RestartSec=5
User=dagu

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable dagu
sudo systemctl start dagu
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3'
services:
  dagu:
    image: ghcr.io/dagu-org/dagu:latest
    ports:
      - "8080:8080"
    volumes:
      - ./dags:/home/dagu/.config/dagu/dags
      - dagu-data:/home/dagu/.local/share/dagu
    environment:
      - DAGU_HOST=0.0.0.0
      - DAGU_PORT=8080
    command: dagu start-all

volumes:
  dagu-data:
```

## Common Workflow Patterns

### ETL Pipeline
```yaml
name: daily-etl
schedule:
  - "0 2 * * *"
type: graph

steps:
  - id: extract
    command: python extract.py --date ${DATE}
    output: RAW_DATA
  
  - id: transform_clean
    depends: [extract]
    command: python transform.py --input ${RAW_DATA}
    output: CLEAN_DATA
  
  - id: load_dw
    depends: [transform_clean]
    command: python load.py --input ${CLEAN_DATA}
  
  - id: cleanup
    depends: [load_dw]
    command: rm -f ${RAW_DATA} ${CLEAN_DATA}
    continue_on:
      exit_code: [0, 1]

handler_on:
  success:
    command: curl -X POST slack-webhook -d '{"text":"ETL Complete"}'
  failure:
    command: curl -X POST pager-duty -d '{"incident":"ETL Failed"}'
```

### CI/CD Pipeline
```yaml
name: app-deploy
env:
  - APP_NAME: myapp

steps:
  - id: test
    command: npm test
  
  - id: build
    depends: [test]
    command: docker build -t ${APP_NAME}:${VERSION} .
  
  - id: push
    depends: [build]
    command: docker push ${APP_NAME}:${VERSION}
  
  - id: deploy_staging
    depends: [push]
    command: kubectl apply -f k8s/staging/
    approval:
      prompt: "Approve production deployment?"
  
  - id: deploy_prod
    depends: [deploy_staging]
    command: kubectl apply -f k8s/production/
```

### Data Backup
```yaml
name: backup-database
schedule:
  - "0 3 * * *"  # 3 AM daily

steps:
  - id: backup
    command: |
      pg_dump -h ${DB_HOST} -U ${DB_USER} ${DB_NAME} \
        | gzip > /backup/db_${DATE}.sql.gz
  
  - id: verify
    depends: [backup]
    command: gzip -t /backup/db_${DATE}.sql.gz
  
  - id: upload
    depends: [verify]
    type: s3
    config:
      bucket: my-backups
      key: database/db_${DATE}.sql.gz
      source: /backup/db_${DATE}.sql.gz
  
  - id: cleanup_local
    depends: [upload]
    command: find /backup -name "db_*.sql.gz" -mtime +7 -delete
```

### API Monitoring
```yaml
name: api-health-check
schedule:
  - "*/5 * * * *"  # Every 5 minutes

steps:
  - id: check_api
    command: |
      curl -fsS https://api.example.com/health \
        -H "Authorization: Bearer ${API_TOKEN}"
    retry_policy:
      limit: 3
      interval_sec: 5
      exit_code: [6, 22, 28]
  
  - id: check_db
    depends: [check_api]
    command: |
      psql ${DATABASE_URL} -c "SELECT 1;" > /dev/null
  
  handler_on:
    failure:
      command: |
        curl -X POST ${PAGERDUTY_WEBHOOK} \
          -d '{"incident": "API Down", "severity": "critical"}'
```

## Advanced Features

### Approval Gates
```yaml
steps:
  - id: prepare_deploy
    command: prepare.sh
  
  - id: deploy_prod
    depends: [prepare_deploy]
    command: deploy.sh production
    approval:
      prompt: "Review staging deployment before approving production"
      input: [APPROVED_BY, MAINTENANCE_WINDOW]
      required: [APPROVED_BY]
  
  - id: notify
    depends: [deploy_prod]
    command: |
      echo "Deployed by ${APPROVED_BY} during ${MAINTENANCE_WINDOW}"
```

### Queue Management
```yaml
# ~/.config/dagu/config.yaml
queues:
  enabled: true
  config:
    - name: "critical"
      max_concurrency: 5
    - name: "batch"
      max_concurrency: 1

---
# workflow.yaml
name: critical-job
queue: critical  # Uses critical queue

---
# batch.yaml
name: batch-job
queue: batch  # Only 1 runs at a time
```

### Distributed Execution
```yaml
# ~/.config/dagu/config.yaml
distributed:
  enabled: true
  workers:
    - name: worker-1
      labels:
        - gpu
        - high-memory
    - name: worker-2
      labels:
        - cpu

---
# workflow.yaml
name: ml-training
steps:
  - id: train_model
    command: python train.py
    labels:
      - gpu
      - high-memory  # Runs only on worker-1
```

### Git Sync
```yaml
# ~/.config/dagu/config.yaml
git:
  enabled: true
  remote: https://github.com/org/dagu-workflows.git
  branch: main
  path: /home/dagu/workflows
  ssh_key: /home/dagu/.ssh/id_rsa
  sync_interval: 60  # Sync every 60 seconds
```

## CLI Commands

```bash
# Start workflow
dagu start workflow.yaml
dagu start workflow.yaml -- P1=value1 P2=value2

# Dry run (simulate without executing)
dagu dry workflow.yaml

# Check status
dagu status workflow-name
dagu history workflow-name

# List workflows
dagu list

# Validate workflow
dagu validate workflow.yaml

# Stop running workflow
dagu stop workflow-name

# Retry failed workflow
dagu retry workflow-name --run-id=<id>

# View logs
dagu log workflow-name
dagu log workflow-name <run-id>

# Start scheduler
dagu scheduler

# Start web UI
dagu server

# Start both
dagu start-all
```

## Best Practices

1. **Idempotency**: Design steps to be safe if rerun (retry logic)
2. **Timeouts**: Always set reasonable `timeout_sec` for long steps
3. **Secrets**: Use Dagu's secret store, never commit credentials
4. **Logs**: Capture important output to variables for debugging
5. **Cleanup**: Use `handler_on.exit` for guaranteed cleanup
6. **Naming**: Use descriptive step IDs and names
7. **Documentation**: Add descriptions to workflows and steps
8. **Testing**: Use `dagu dry` to validate before production
9. **Monitoring**: Set up failure notifications
10. **Version Control**: Store workflows in Git with Git Sync

## Troubleshooting

### Workflow not running
- Check scheduler: `pgrep -f "dagu scheduler"`
- Check schedule format (cron valid?)
- Check logs: `dagu log workflow-name`

### Step keeps failing
- Check `retry_policy` configuration
- Verify `exit_code` values
- Check step timeout

### Permission denied
- Check file permissions on DAG files
- Verify user running Dagu has access to commands

### Scheduler won't start
- Check port 8090/8080 not in use
- Check `~/.config/dagu/` directory permissions
- Review logs in `~/.local/share/dagu/logs/`

## References

- Official Docs: https://docs.dagu.sh
- GitHub: https://github.com/dagu-org/dagu
- Examples: https://docs.dagu.sh/writing-workflows/examples
- Step Types: https://docs.dagu.sh/step-types/shell

## Skill Usage Summary

When user asks to create a Dagu workflow:
1. Ask what the workflow should do (use case)
2. Determine if cron schedule or event-triggered needed
3. Identify steps required (shell, HTTP, Docker, etc.)
4. Define dependencies between steps
5. Add error handling (retry_policy, continue_on)
6. Add lifecycle handlers for notifications/cleanup
7. Test with `dagu validate` and `dagu dry`
8. Deploy to `~/.config/dagu/dags/`
9. Start scheduler if not running
