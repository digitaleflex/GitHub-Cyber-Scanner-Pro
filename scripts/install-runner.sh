#!/usr/bin/env bash
set -euo pipefail

RUNNER_DIR="/home/action-runners"
RUNNER_USER="github-runner"
RUNNER_NAME="cyber-scanner-runner"
REPO_URL="https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

usage() {
    echo "Usage: $0 <github-token>"
    echo ""
    echo "Install a self-hosted GitHub Actions runner for $REPO_URL"
    echo ""
    echo "  1. Go to: $REPO_URL/settings/actions/runners/new"
    echo "  2. Generate a token"
    echo "  3. Run: sudo $0 <token>"
    exit 1
}

if [[ -z "${1:-}" ]]; then
    usage
fi
GITHUB_TOKEN="$1"

# Prerequisites
if ! command -v curl &>/dev/null; then
    echo "Installing curl..."
    apt-get update && apt-get install -y curl tar
fi
if ! command -v jq &>/dev/null; then
    echo "Installing jq..."
    apt-get update && apt-get install -y jq
fi
if ! command -v node &>/dev/null; then
    echo "Installing nodejs..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt-get install -y nodejs
fi

# Create runner directory
mkdir -p "$RUNNER_DIR"

# Determine latest runner version
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/^v//')
RUNNER_FILE="actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_FILE}"

# Download and extract
cd "$RUNNER_DIR"
if [[ ! -f "$RUNNER_FILE" ]]; then
    echo "Downloading GitHub Actions Runner v${RUNNER_VERSION}..."
    curl -fsSL -O "$RUNNER_URL"
    echo "Extracting..."
    tar xzf "$RUNNER_FILE"
fi

# Configure (config.sh refuses to run as root — drop privileges if root)
echo "Configuring runner: $RUNNER_NAME"
if [[ $EUID -eq 0 ]]; then
    RUNNER_ALLOW_RUNASROOT=1 ./config.sh \
        --url "$REPO_URL" \
        --token "$GITHUB_TOKEN" \
        --name "$RUNNER_NAME" \
        --labels "self-hosted,cyber-scanner" \
        --work "_work" \
        --replace \
        --unattended
else
    ./config.sh \
        --url "$REPO_URL" \
        --token "$GITHUB_TOKEN" \
        --name "$RUNNER_NAME" \
        --labels "self-hosted,cyber-scanner" \
        --work "_work" \
        --replace \
        --unattended
fi

# Fix ownership for the service
chown -R "$SUDO_USER:$SUDO_USER" "$RUNNER_DIR" 2>/dev/null || true

# Install as systemd service (needs root)
echo "Installing as systemd service..."
./svc.sh install
./svc.sh start

echo ""
echo "=== DONE ==="
echo "Runner installed at: $RUNNER_DIR"
echo "Runner name:         $RUNNER_NAME"
echo "Repository:          $REPO_URL"
echo ""
echo "Check status:  sudo ./svc.sh status"
echo "View logs:     sudo journalctl -u actions.runner.${RUNNER_NAME,,} -f"
echo "Stop runner:   sudo ./svc.sh stop"
echo "Remove runner: sudo ./config.sh remove --token <new-token>"
