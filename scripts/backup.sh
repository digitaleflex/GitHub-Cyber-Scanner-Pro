#!/usr/bin/env bash
# Sauvegarde quotidienne du Cyber-Scanner-Pro.
# - pg_dump de la base Postgres (cyber_scanner_db) -> backups/cyber_scanner/
# - copie de reports/ et data/ (exports JSON, rapports)
# - notif Discord succès/échec
# Retention : garde les N derniers dumps (BACKUP_KEEP, defaut 14).
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="${PROJECT_DIR}/backups/cyber_scanner"
BACKUP_KEEP="${BACKUP_KEEP:-14}"
DB_CONTAINER="cyber_scanner_db"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-scanner_db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
DUMP="${BACKUP_ROOT}/cyber_scanner_${STAMP}.sql.gz"
ERROR_MSG=""

# ── Discord ──
ENV_FILE="/home/actions-runner/secrets/.env.production"
DISCORD_WEBHOOK="${DISCORD_WEBHOOK_URL:-}"
if [[ -z "$DISCORD_WEBHOOK" && -f "$ENV_FILE" ]]; then
  set -a; . "$ENV_FILE"; set +a
fi

send_discord() {
  local webhook="${DISCORD_WEBHOOK_URL:-}"
  [[ -z "$webhook" ]] && return 0
  curl -fsS -X POST "$webhook" -H "Content-Type: application/json" \
    -d "{\"embeds\":[{\"title\":\"$1\",\"description\":\"$2\",\"color\":$3,\"timestamp\":\"$(date -Iseconds)\"}]}" \
    >/dev/null 2>&1 || true
}

trap 'ERROR_MSG="Erreur ligne $LINENO"; send_discord "🚨 Backup Cyber Scanner — ÉCHEC" "$ERROR_MSG" 15548997; exit 1' ERR

mkdir -p "${BACKUP_ROOT}"

echo "🗄️  Dump PostgreSQL -> ${DUMP}"
docker exec "${DB_CONTAINER}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" | gzip > "${DUMP}"

if [ ! -s "${DUMP}" ]; then
    echo "❌ Dump vide ou échec de pg_dump" >&2
    rm -f "${DUMP}"
    exit 1
fi

echo "📦 Export JSON complet (toutes les tables)"
# Le conteneur écrit dans /app/data/exports (monté sur ./data/exports)
docker exec cyber_github_scanner python scripts/export_json.py >> "${BACKUP_ROOT}/export.log" 2>&1 \
    || echo "⚠️  Export JSON échoué (voir export.log)"
for f in "${PROJECT_DIR}/data/exports"/cyber_export_*.json; do
    [ -e "$f" ] || continue
    if sudo mv -f "$f" "${BACKUP_ROOT}/cyber_export_${STAMP}.json"; then
        gzip -9f "${BACKUP_ROOT}/cyber_export_${STAMP}.json"
        echo "   -> cyber_export_${STAMP}.json.gz"
    else
        echo "⚠️  Impossible de déplacer $(basename "$f") (permissions root)"
    fi
done

echo "📁 Copie reports/ et data/"
if [ -d "${PROJECT_DIR}/reports" ] && [ "$(ls -A "${PROJECT_DIR}/reports")" ]; then
    tar -czf "${BACKUP_ROOT}/reports_${STAMP}.tar.gz" -C "${PROJECT_DIR}" reports
fi
if [ -d "${PROJECT_DIR}/data" ] && [ "$(ls -A "${PROJECT_DIR}/data")" ]; then
    tar -czf "${BACKUP_ROOT}/data_${STAMP}.tar.gz" -C "${PROJECT_DIR}" data
fi

# Retention
DELETED=0
for glob in cyber_scanner_*.sql.gz cyber_export_*.json reports_*.tar.gz data_*.tar.gz; do
    count=0
    for f in "${BACKUP_ROOT}"/${glob}; do
        [ -e "$f" ] || continue
        count=$((count + 1))
    done
    while [ "$count" -gt "${BACKUP_KEEP}" ]; do
        oldest="$(ls -1 "${BACKUP_ROOT}"/${glob} 2>/dev/null | head -1)"
        rm -f "${oldest}"
        count=$((count - 1))
        DELETED=$((DELETED + 1))
    done
done

DUMP_SIZE=$(du -h "${DUMP}" | cut -f1)

echo "✅ Backup terminé : dump ${DUMP_SIZE} + JSON complet (retention ${BACKUP_KEEP}, ${DELETED} ancien(s) purgé(s))"

# ── Notification succès ──
send_discord \
  "✅ Backup Cyber Scanner — OK" \
  "**Base :** \`${DB_NAME}\`\n**Taille dump :** ${DUMP_SIZE}\n**Rétention :** ${BACKUP_KEEP} jours\n**Anciens purgés :** ${DELETED}" \
  5763719
