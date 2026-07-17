#!/usr/bin/env bash
set -euo pipefail

DOMAIN="cyberbook.eurin.tech"
SCANNER_CONTAINER="cyber_github_scanner"
LOG_FILE="/var/log/cyberscan-monitor.log"
RETRIES=3

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }
notify() { log "ALERT: $*"; }

check_site() {
    for i in $(seq 1 $RETRIES); do
        if curl -skf -o /dev/null --max-time 10 "https://$DOMAIN/" 2>/dev/null; then
            return 0
        fi
        sleep 2
    done
    return 1
}

check_scanner_healthy() {
    docker ps --filter "name=$SCANNER_CONTAINER" --format '{{.Status}}' | grep -q "(healthy)"
}

restart_stack() {
    notify "Restarting Traefik..."
    docker restart traefik || true
    sleep 5

    notify "Restarting $SCANNER_CONTAINER..."
    docker restart "$SCANNER_CONTAINER" || true
    sleep 5

    if check_site; then
        log "RECOVERY OK - Site is back up"
    else
        notify "RECOVERY FAILED - Manual intervention required"
    fi
}

if ! check_site; then
    notify "Site $DOMAIN is DOWN"
    log "Scanner healthy: $(check_scanner_healthy && echo yes || echo no)"

    if ! check_scanner_healthy; then
        notify "Scanner unhealthy, restarting..."
        docker restart "$SCANNER_CONTAINER" || true
        sleep 10
    fi

    if ! check_site; then
        restart_stack
    fi
else
    log "OK - $DOMAIN responded"
fi
