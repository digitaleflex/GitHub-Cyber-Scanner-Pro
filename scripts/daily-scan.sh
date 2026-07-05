#!/usr/bin/env bash
set -euo pipefail

# Trigger a scan via the local API
curl -sf -X POST http://localhost:8000/api/scan || {
    echo "Scan trigger failed — is the app running?"
    exit 1
}
