#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="cyberscan-backup"
SCRIPT_PATH="/opt/cyberscan/scripts/backup-db.sh"

# Create systemd service
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=CyberScan PostgreSQL backup
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=$SCRIPT_PATH
User=root
Environment=DB_HOST=localhost DB_PORT=5432 DB_NAME=scanner_db DB_USER=postgres DB_PASSWORD=${DB_PASSWORD} BACKUP_DIR=/opt/cyberscan/reports/backups
EOF

# Create systemd timer (daily at 03:00)
cat > /etc/systemd/system/${SERVICE_NAME}.timer <<EOF
[Unit]
Description=Daily CyberScan PostgreSQL backup

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.timer
systemctl start ${SERVICE_NAME}.timer

echo "✅ Backup timer installed:"
systemctl status ${SERVICE_NAME}.timer --no-pager
