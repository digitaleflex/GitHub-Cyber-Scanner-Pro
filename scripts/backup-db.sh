#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/app/reports/backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-scanner_db}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-cyberpass}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/scanner_db_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

export PGPASSWORD="$DB_PASSWORD"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --clean --if-exists | gzip > "$BACKUP_FILE"
unset PGPASSWORD

echo "✅ Backup saved: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Rotation: delete backups older than RETENTION_DAYS
find "$BACKUP_DIR" -name "scanner_db_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
echo "🧹 Rotation done (retention: ${RETENTION_DAYS}d)"
