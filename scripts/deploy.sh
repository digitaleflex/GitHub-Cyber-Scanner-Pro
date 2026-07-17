#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/cyberscan"
COMPOSE_FILE="compose.prod.yml"
ENV_FILE=".env"
SERVICE="cyber-scanner"
CONTAINER="cyber_github_scanner"
TIMEOUT=30

usage() {
    echo "Usage: $0 {deploy|rollback|status|logs}"
    exit 1
}

info()  { echo -e "\033[1;34m[INFO]\033[0m $*"; }
ok()    { echo -e "\033[1;32m[OK]\033[0m   $*"; }
err()   { echo -e "\033[1;31m[ERROR]\033[0m $*" >&2; }

healthcheck() {
    info "Waiting for container to be healthy..."
    for i in $(seq 1 $TIMEOUT); do
        if docker ps --filter "name=$CONTAINER" --format "{{.Status}}" | grep -q "^Up"; then
            if docker exec "$CONTAINER" python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" > /dev/null 2>&1; then
                ok "Service is up"
                return 0
            fi
        fi
        sleep 1
    done
    err "Healthcheck failed after ${TIMEOUT}s"
    docker compose -f "$COMPOSE_FILE" logs --tail=20 "$SERVICE"
    return 1
}

deploy() {
    if [[ ! -d "$PROJECT_DIR" ]]; then
        err "Project directory $PROJECT_DIR does not exist"
        info "Run: git clone https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro.git $PROJECT_DIR"
        exit 1
    fi

    cd "$PROJECT_DIR"

    info "Pulling latest code..."
    git -C "$PROJECT_DIR" stash --include-untracked 2>/dev/null || true
    git pull --ff-only origin main

    info "Writing .env from secrets..."
    cat > "$PROJECT_DIR/.env" <<EOF
DOMAIN=$DOMAIN
DB_HOST=db
DB_PORT=5432
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
GITHUB_TOKEN=$GITHUB_TOKEN
SCAN_INTERVAL_SECONDS=$SCAN_INTERVAL_SECONDS
EOF

    info "Building Docker image..."
    docker compose -f "$COMPOSE_FILE" build --pull "$SERVICE"

    info "Stopping old stack..."
    docker compose -f "$COMPOSE_FILE" down --timeout 10 2>/dev/null || true

    info "Starting full stack (DB + app)..."
    docker compose -f "$COMPOSE_FILE" up -d

    if healthcheck; then
        ok "Deployment successful"
        docker compose -f "$COMPOSE_FILE" ps
        docker image prune -f > /dev/null 2>&1 || true
    else
        err "Deployment failed — rolling back..."
        rollback
        exit 1
    fi
}

rollback() {
    cd "$PROJECT_DIR"
    local stash_ref
    stash_ref=$(git stash create "rollback-$(date +%s)" 2>/dev/null || true)

    info "Reverting to previous commit..."
    git log --oneline -2
    git reset --hard HEAD@{1} 2>/dev/null || git reset --hard HEAD~1

    info "Rebuilding previous version..."
    docker compose -f "$COMPOSE_FILE" build "$SERVICE"
    docker compose -f "$COMPOSE_FILE" up -d "$SERVICE"

    if healthcheck; then
        ok "Rollback successful"
    else
        err "Rollback also failed — manual intervention required"
        exit 1
    fi
}

status() {
    cd "$PROJECT_DIR" 2>/dev/null || true
    echo "=== Service ==="
    docker ps --filter "name=$CONTAINER" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo
    echo "=== Images ==="
    docker images cyber-scanner --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}"
    echo
    echo "=== Git ==="
    git -C "$PROJECT_DIR" log --oneline -3 2>/dev/null || echo "Not a git repo"
}

logs() {
    cd "$PROJECT_DIR" 2>/dev/null || true
    docker compose -f "$COMPOSE_FILE" logs -f --tail=50
}

case "${1:-deploy}" in
    deploy)   deploy ;;
    rollback) rollback ;;
    status)   status ;;
    logs)     logs ;;
    *)        usage ;;
esac
