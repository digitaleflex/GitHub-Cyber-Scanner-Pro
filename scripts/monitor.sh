#!/usr/bin/env bash
set -euo pipefail

DOMAIN="cyberbook.eurin.tech"
SCANNER_CONTAINER="cyber_github_scanner"
LOG_FILE="/var/log/cyberscan-monitor.log"
RETRIES=3

# ── Discord ──
ENV_FILE="/home/actions-runner/secrets/.env.production"
if [[ -z "${DISCORD_WEBHOOK_URL:-}" && -f "$ENV_FILE" ]]; then
  set -a; . "$ENV_FILE"; set +a
fi

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }
ALERT_STATE_FILE="/tmp/cyberscan-alert-state"

send_discord() {
  local webhook="${DISCORD_WEBHOOK_URL:-}"
  [[ -z "$webhook" ]] && return 0
  curl -fsS -X POST "$webhook" -H "Content-Type: application/json" \
    -d "{\"embeds\":[{\"title\":\"$1\",\"description\":\"$2\",\"color\":$3,\"timestamp\":\"$(date -Iseconds)\"}]}" \
    >/dev/null 2>&1 || true
}
notify() {
  # Anti-spam : une seule alerte tant que le problème persiste
  if [[ -f "$ALERT_STATE_FILE" ]]; then
    log "ALERT (suppressed, already alerted): $*"
    return
  fi
  echo "ALERT" > "$ALERT_STATE_FILE"
  log "ALERT: $*"
  send_discord "🔴 Cyber Scanner — ALERTE" "$*" 15548997
}
clear_alert_state() {
  rm -f "$ALERT_STATE_FILE"
}

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
        clear_alert_state
        send_discord "🟢 Cyber Scanner — RÉTABLI" "**Domaine :** ${DOMAIN}\nLe site répond de nouveau après redémarrage." 5763719
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
    clear_alert_state
fi
