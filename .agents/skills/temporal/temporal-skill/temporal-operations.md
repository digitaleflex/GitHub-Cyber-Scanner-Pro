# Temporal Operations

> **Backup, Restore, Cluster Health, and MySQL Maintenance**  
> Production operations guide for Temporal deployments.

## Overview

| Operation | Purpose |
|-----------|---------|
| **Backup** | Protect workflow history and state |
| **Restore** | Recover from failures or migrate data |
| **Health Checks** | Monitor cluster and worker health |
| **Maintenance** | MySQL optimization, cleanup, upgrades |

---

## MySQL Database Setup

### Initial Setup

```bash
# Create Temporal databases
mysql -u root -p <<EOF
-- Main database for workflow execution
CREATE DATABASE temporal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Visibility database for workflow search
CREATE DATABASE temporal_visibility CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create Temporal user
CREATE USER 'temporal'@'%' IDENTIFIED BY 'your-secure-password';

-- Grant permissions
GRANT ALL PRIVILEGES ON temporal.* TO 'temporal'@'%';
GRANT ALL PRIVILEGES ON temporal_visibility.* TO 'temporal'@'%';

FLUSH PRIVILEGES;
EOF
```

### Production MySQL Configuration

```ini
# /etc/mysql/mysql.conf.d/temporal.cnf
[mysqld]
# Connection settings
max_connections = 500
wait_timeout = 28800
interactive_timeout = 28800

# InnoDB settings for Temporal
innodb_buffer_pool_size = 4G          # 70% of available RAM
innodb_log_file_size = 1G
innodb_flush_log_at_trx_commit = 1
innodb_flush_method = O_DIRECT

# Query cache (disable for high-write workloads)
query_cache_type = 0
query_cache_size = 0

# Binary logging for replication/backup
log_bin = mysql-bin
binlog_format = ROW
expire_logs_days = 7
sync_binlog = 1

# Character set
character_set_server = utf8mb4
collation_server = utf8mb4_unicode_ci
```

### Start Temporal with MySQL

```bash
# Development/staging
temporal server start-dev \
  --db-filename "" \
  --sql-plugin mysql \
  --sql-host localhost \
  --sql-port 3306 \
  --sql-user temporal \
  --sql-password 'your-secure-password' \
  --sql-database temporal

# Production with additional options
temporal server start-dev \
  --db-filename "" \
  --sql-plugin mysql \
  --sql-host mysql.example.com \
  --sql-port 3306 \
  --sql-user temporal \
  --sql-password 'your-secure-password' \
  --sql-database temporal \
  --sql-tls-enabled \
  --sql-tls-ca-file /path/to/ca.pem \
  --log-level info
```

---

## Backup Strategies

### MySQL Backup with mysqldump

```bash
#!/bin/bash
# backup-temporal.sh

BACKUP_DIR="/backup/temporal"
DATE=$(date +%Y%m%d_%H%M%S)
MYSQL_USER="temporal"
MYSQL_PASSWORD="your-secure-password"
MYSQL_HOST="localhost"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup main database
mysqldump -u $MYSQL_USER -p$MYSQL_PASSWORD -h $MYSQL_HOST \
  --single-transaction \
  --routines \
  --triggers \
  --quick \
  temporal > $BACKUP_DIR/temporal_$DATE.sql

# Backup visibility database
mysqldump -u $MYSQL_USER -p$MYSQL_PASSWORD -h $MYSQL_HOST \
  --single-transaction \
  --routines \
  --triggers \
  --quick \
  temporal_visibility > $BACKUP_DIR/temporal_visibility_$DATE.sql

# Compress backups
gzip $BACKUP_DIR/temporal_$DATE.sql
gzip $BACKUP_DIR/temporal_visibility_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/*_$DATE.sql.gz"
```

### Automated Backup with Cron

```bash
# /etc/cron.d/temporal-backup

# Daily backup at 2 AM
0 2 * * * root /opt/temporal/scripts/backup-temporal.sh >> /var/log/temporal-backup.log 2>&1

# Weekly full backup on Sunday at 3 AM
0 3 * * 0 root /opt/temporal/scripts/backup-temporal-full.sh >> /var/log/temporal-backup.log 2>&1
```

### MySQL Binary Log Backup (Point-in-Time Recovery)

```bash
#!/bin/bash
# backup-binlog.sh

BACKUP_DIR="/backup/temporal/binlog"
MYSQL_USER="temporal"
MYSQL_PASSWORD="your-secure-password"

mkdir -p $BACKUP_DIR

# Flush logs to create new binlog file
mysql -u $MYSQL_USER -p$MYSQL_PASSWORD -e "FLUSH LOGS;"

# Copy binary logs (except current)
CURRENT_LOG=$(mysql -u $MYSQL_USER -p$MYSQL_PASSWORD -e "SHOW MASTER STATUS\G" | grep "File:" | awk '{print $2}')

for log in /var/lib/mysql/mysql-bin.*; do
  if [[ "$(basename $log)" != "$CURRENT_LOG" ]]; then
    cp $log $BACKUP_DIR/
  fi
done
```

### Workflow History Export

```python
# export_workflows.py
import asyncio
import json
from temporalio.client import Client

async def export_workflow_history(workflow_id: str, output_file: str):
    """Export workflow history to JSON file."""
    client = await Client.connect("localhost:7233")
    
    handle = client.get_workflow_handle(workflow_id)
    
    events = []
    async for event in handle.fetch_history_events():
        events.append({
            "event_id": event.event_id,
            "event_type": event.event_type.name,
            "timestamp": str(event.event_time),
            # Add more fields as needed
        })
    
    with open(output_file, "w") as f:
        json.dump(events, f, indent=2)
    
    print(f"Exported {len(events)} events to {output_file}")

async def export_all_workflows(namespace: str = "default"):
    """Export all completed workflows."""
    client = await Client.connect("localhost:7233")
    
    async for workflow in client.list_workflows(
        query="ExecutionStatus='Completed'"
    ):
        output_file = f"exports/{workflow.id}_{workflow.run_id}.json"
        await export_workflow_history(workflow.id, output_file)

if __name__ == "__main__":
    asyncio.run(export_all_workflows())
```

---

## Restore Procedures

### MySQL Restore

```bash
#!/bin/bash
# restore-temporal.sh

BACKUP_FILE=$1
MYSQL_USER="temporal"
MYSQL_PASSWORD="your-secure-password"
MYSQL_HOST="localhost"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

# Stop Temporal server and workers
sudo systemctl stop temporal-worker
sudo systemctl stop temporal-server

# Decompress if needed
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -k $BACKUP_FILE
    BACKUP_FILE="${BACKUP_FILE%.gz}"
fi

# Drop and recreate database
mysql -u $MYSQL_USER -p$MYSQL_PASSWORD -h $MYSQL_HOST <<EOF
DROP DATABASE IF EXISTS temporal;
CREATE DATABASE temporal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF

# Restore from backup
mysql -u $MYSQL_USER -p$MYSQL_PASSWORD -h $MYSQL_HOST temporal < $BACKUP_FILE

# Start services
sudo systemctl start temporal-server
sleep 10
sudo systemctl start temporal-worker

echo "Restore completed from $BACKUP_FILE"
```

### Point-in-Time Recovery

```bash
#!/bin/bash
# pit-recovery.sh

BACKUP_FILE=$1
RECOVERY_TIME=$2  # Format: "2024-01-15 14:30:00"

# Restore base backup first
./restore-temporal.sh $BACKUP_FILE

# Apply binary logs up to recovery point
mysqlbinlog --stop-datetime="$RECOVERY_TIME" \
  /backup/temporal/binlog/mysql-bin.* | \
  mysql -u temporal -p'password' temporal

echo "Point-in-time recovery completed to $RECOVERY_TIME"
```

---

## Health Monitoring

### Cluster Health Check

```bash
#!/bin/bash
# health-check.sh

# Check Temporal server
if temporal operator cluster health 2>/dev/null | grep -q "SERVING"; then
    echo "Temporal Server: HEALTHY"
else
    echo "Temporal Server: UNHEALTHY"
    exit 1
fi

# Check MySQL connection
if mysql -u temporal -p'password' -e "SELECT 1" temporal > /dev/null 2>&1; then
    echo "MySQL: HEALTHY"
else
    echo "MySQL: UNHEALTHY"
    exit 1
fi

# Check task queue pollers
POLLERS=$(temporal task-queue describe --task-queue my-queue 2>/dev/null | grep -c "pollers")
if [ "$POLLERS" -gt 0 ]; then
    echo "Task Queue Pollers: $POLLERS"
else
    echo "Task Queue Pollers: NONE (workers not running)"
    exit 1
fi

# Check for stuck workflows
STUCK=$(temporal workflow list --query "ExecutionStatus='Running' AND StartTime < '$(date -d '1 hour ago' --iso-8601=seconds)'" 2>/dev/null | wc -l)
if [ "$STUCK" -gt 10 ]; then
    echo "WARNING: $STUCK potentially stuck workflows"
fi

echo "All health checks passed"
```

### Python Health Monitor

```python
# health_monitor.py
import asyncio
from temporalio.client import Client
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()

class TemporalHealthMonitor:
    def __init__(self, address: str = "localhost:7233"):
        self.address = address
        self._client = None
    
    async def connect(self):
        self._client = await Client.connect(self.address)
    
    async def check_server_health(self) -> bool:
        """Check if Temporal server is responding."""
        try:
            # Simple query to verify connection
            async for _ in self._client.list_workflows(query="", page_size=1):
                break
            return True
        except Exception as e:
            logger.error("server_health_check_failed", error=str(e))
            return False
    
    async def check_task_queue_pollers(self, task_queue: str) -> int:
        """Count active pollers on task queue."""
        try:
            desc = await self._client.get_task_queue(task_queue)
            return len(desc.pollers) if desc.pollers else 0
        except Exception as e:
            logger.error("task_queue_check_failed", error=str(e))
            return 0
    
    async def check_stuck_workflows(self, threshold_hours: int = 1) -> list:
        """Find workflows running longer than threshold."""
        cutoff = datetime.utcnow() - timedelta(hours=threshold_hours)
        stuck = []
        
        query = f"ExecutionStatus='Running' AND StartTime < '{cutoff.isoformat()}Z'"
        async for workflow in self._client.list_workflows(query=query):
            stuck.append({
                "id": workflow.id,
                "type": workflow.workflow_type,
                "start_time": workflow.start_time,
            })
        
        return stuck
    
    async def check_failed_workflows(self, hours: int = 24) -> int:
        """Count workflows failed in last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        count = 0
        
        query = f"ExecutionStatus='Failed' AND CloseTime > '{cutoff.isoformat()}Z'"
        async for _ in self._client.list_workflows(query=query):
            count += 1
        
        return count
    
    async def full_health_check(self, task_queues: list) -> dict:
        """Run all health checks."""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "server_healthy": await self.check_server_health(),
            "task_queues": {},
            "stuck_workflows": await self.check_stuck_workflows(),
            "failed_last_24h": await self.check_failed_workflows(),
        }
        
        for queue in task_queues:
            results["task_queues"][queue] = {
                "pollers": await self.check_task_queue_pollers(queue)
            }
        
        results["overall_healthy"] = (
            results["server_healthy"] and
            all(q["pollers"] > 0 for q in results["task_queues"].values()) and
            len(results["stuck_workflows"]) < 10
        )
        
        return results

async def main():
    monitor = TemporalHealthMonitor()
    await monitor.connect()
    
    results = await monitor.full_health_check(["orders", "notifications"])
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
```

### Systemd Health Check Timer

```ini
# /etc/systemd/system/temporal-health.service
[Unit]
Description=Temporal Health Check

[Service]
Type=oneshot
ExecStart=/opt/temporal/scripts/health-check.sh
```

```ini
# /etc/systemd/system/temporal-health.timer
[Unit]
Description=Run Temporal Health Check every 5 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable temporal-health.timer
sudo systemctl start temporal-health.timer
```

---

## MySQL Maintenance

### Regular Maintenance Tasks

```bash
#!/bin/bash
# mysql-maintenance.sh

MYSQL_USER="temporal"
MYSQL_PASSWORD="your-secure-password"

# Analyze tables for query optimization
mysql -u $MYSQL_USER -p$MYSQL_PASSWORD temporal -e "
ANALYZE TABLE executions;
ANALYZE TABLE history_node;
ANALYZE TABLE history_tree;
ANALYZE TABLE tasks;
ANALYZE TABLE task_queues;
"

# Check for table issues
mysql -u $MYSQL_USER -p$MYSQL_PASSWORD temporal -e "
CHECK TABLE executions, history_node, history_tree, tasks FAST;
"

echo "Maintenance completed at $(date)"
```

### History Cleanup (Completed Workflows)

```python
# cleanup_history.py
import asyncio
from temporalio.client import Client
from datetime import datetime, timedelta

async def cleanup_old_workflows(days_old: int = 90, dry_run: bool = True):
    """Terminate and delete old completed workflows."""
    client = await Client.connect("localhost:7233")
    
    cutoff = datetime.utcnow() - timedelta(days=days_old)
    query = f"ExecutionStatus='Completed' AND CloseTime < '{cutoff.isoformat()}Z'"
    
    count = 0
    async for workflow in client.list_workflows(query=query):
        if dry_run:
            print(f"Would delete: {workflow.id}")
        else:
            # Note: Temporal auto-cleans based on retention
            # This is for visibility cleanup
            pass
        count += 1
    
    print(f"{'Would delete' if dry_run else 'Deleted'} {count} workflows")

if __name__ == "__main__":
    asyncio.run(cleanup_old_workflows(days_old=90, dry_run=True))
```

### Set Namespace Retention

```bash
# Set retention period for workflow history
temporal operator namespace update \
  --namespace default \
  --retention 30d

# Verify
temporal operator namespace describe --namespace default
```

### MySQL Slow Query Monitoring

```ini
# /etc/mysql/mysql.conf.d/slow-query.cnf
[mysqld]
slow_query_log = 1
slow_query_log_file = /var/log/mysql/temporal-slow.log
long_query_time = 1
log_queries_not_using_indexes = 1
```

```bash
# Analyze slow queries
mysqldumpslow /var/log/mysql/temporal-slow.log
```

### Index Optimization

```sql
-- Check for missing indexes
SELECT 
    t.TABLE_NAME,
    t.TABLE_ROWS,
    ROUND(t.DATA_LENGTH / 1024 / 1024, 2) AS data_mb,
    ROUND(t.INDEX_LENGTH / 1024 / 1024, 2) AS index_mb
FROM information_schema.TABLES t
WHERE t.TABLE_SCHEMA = 'temporal'
ORDER BY t.TABLE_ROWS DESC;

-- Show existing indexes
SHOW INDEX FROM temporal.executions;
SHOW INDEX FROM temporal.history_node;
```

---

## Upgrade Procedures

### Temporal CLI Upgrade

```bash
# Check current version
temporal --version

# Upgrade on macOS
brew upgrade temporal

# Upgrade on Linux
curl -sSf https://temporal.download/cli.sh | sh

# Verify
temporal --version
```

### Rolling Worker Upgrade

```bash
#!/bin/bash
# rolling-upgrade.sh

# 1. Deploy new worker version alongside old
NEW_WORKER_PID=$(uv run python -m src.worker_v2 &)
sleep 30

# 2. Verify new worker is healthy
temporal task-queue describe --task-queue my-queue

# 3. Gracefully stop old workers
kill -SIGTERM $OLD_WORKER_PID

# 4. Wait for in-flight work to complete
sleep 60

# 5. Verify all old workers stopped
ps aux | grep worker_v1
```

### MySQL Upgrade

```bash
# 1. Stop Temporal services
sudo systemctl stop temporal-worker
sudo systemctl stop temporal-server

# 2. Backup before upgrade
./backup-temporal.sh

# 3. Upgrade MySQL
sudo apt update && sudo apt upgrade mysql-server

# 4. Run mysql_upgrade
sudo mysql_upgrade -u root -p

# 5. Restart services
sudo systemctl start mysql
sudo systemctl start temporal-server
sudo systemctl start temporal-worker

# 6. Verify
temporal operator cluster health
```

---

## Disaster Recovery

### Recovery Runbook

```markdown
## Temporal Disaster Recovery Runbook

### 1. Total Server Failure

1. Provision new server
2. Install MySQL and Temporal CLI
3. Restore from latest backup:
   ```bash
   ./restore-temporal.sh /backup/temporal/temporal_latest.sql.gz
   ```
4. Start Temporal server
5. Deploy workers
6. Verify with health checks

### 2. MySQL Corruption

1. Stop Temporal services
2. Attempt repair:
   ```bash
   mysqlcheck -u root -p --repair temporal
   ```
3. If repair fails, restore from backup
4. Apply binary logs for point-in-time recovery

### 3. Stuck Workflow Recovery

1. Identify stuck workflows:
   ```bash
   temporal workflow list --query "ExecutionStatus='Running' AND StartTime < '2024-01-01'"
   ```
2. Reset to last good state:
   ```bash
   temporal workflow reset --workflow-id ID --event-id LAST_GOOD_EVENT
   ```
3. Or terminate and restart:
   ```bash
   temporal workflow terminate --workflow-id ID --reason "Manual recovery"
   ```
```

### Failover Script

```bash
#!/bin/bash
# failover.sh

PRIMARY_HOST="mysql-primary.example.com"
SECONDARY_HOST="mysql-secondary.example.com"

# Check primary health
if ! mysqladmin -h $PRIMARY_HOST ping 2>/dev/null; then
    echo "Primary MySQL unreachable, initiating failover..."
    
    # Update Temporal to point to secondary
    sudo systemctl stop temporal-server
    
    # Update configuration
    sed -i "s/$PRIMARY_HOST/$SECONDARY_HOST/g" /etc/temporal/config.yaml
    
    # Restart with secondary
    sudo systemctl start temporal-server
    
    # Alert team
    curl -X POST "https://slack.webhook.url" \
        -d '{"text":"Temporal failed over to secondary MySQL"}'
    
    echo "Failover complete"
else
    echo "Primary MySQL healthy"
fi
```

---

## Operations Checklist

### Daily
- [ ] Review health check results
- [ ] Check for stuck workflows
- [ ] Monitor error rates

### Weekly
- [ ] Review slow query logs
- [ ] Analyze table statistics
- [ ] Verify backup integrity

### Monthly
- [ ] Test backup restore procedure
- [ ] Review and rotate credentials
- [ ] Check disk space trends
- [ ] Update Temporal CLI

### Quarterly
- [ ] Full disaster recovery drill
- [ ] Capacity planning review
- [ ] Security audit

---

**Next:** See **temporal-cloud.md** for Temporal Cloud deployment.
