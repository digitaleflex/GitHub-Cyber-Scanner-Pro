#!/usr/bin/env bash
# linux.sh — agentless Linux asset collector (SSH).
# Emits ONE normalized JSON document to stdout (consumed by inventory:upsert).
# Read-only: only reads system state. Requires: standard coreutils + iproute2.
set -u

json_str() { python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1" 2>/dev/null || printf '"%s"' "$(printf '%s' "$1" | sed 's/"/\\"/g')"; }

HOST=$(hostname 2>/dev/null || echo unknown)
OS_PRETTY=$(. /etc/os-release 2>/dev/null && echo "${PRETTY_NAME:-unknown}" || uname -s)
KERNEL=$(uname -r 2>/dev/null)
UNAME=$(uname -a 2>/dev/null)
CPU_MODEL=$(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2- | sed 's/^ //')
CPU_CORES=$(nproc 2>/dev/null || grep -c '^processor' /proc/cpuinfo 2>/dev/null)
MEM_KB=$(grep -m1 MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}')
MEM_GB=$(awk "BEGIN{printf \"%.2f\", ${MEM_KB:-0}/1048576}" 2>/dev/null)
IP=$(ip -4 -o addr show scope global 2>/dev/null | awk 'NR==1{split($4,a,"/");print a[1]}')

# disks (df -BG, local filesystems)
DISKS=$(df -BG -x tmpfs -x devtmpfs 2>/dev/null | awk 'NR>1{printf "%s{\"device\":\"%s\",\"sizeGb\":\"%s\",\"freeGb\":\"%s\",\"mount\":\"%s\"}", (NR>2?",":""), $6, $2, $4, $6}')

# listening ports (ss)
PORTS=$(ss -tlnH 2>/dev/null | awk '{split($4,a,":"); printf "%s%d", (NR>1?",":""), a[length(a)]}' | sort -un | awk '{printf "%s%d", (NR>1?",":""), $1}')

# services (systemd, top active)
SERVICES=$(systemctl list-units --type=service --state=running --no-pager --no-legend 2>/dev/null | awk '{printf "%s{\"name\":\"%s\",\"status\":\"running\"}", (NR>1?",":""), $1}' | head -c 60000)

# packages (dpkg or rpm)
if command -v dpkg-query >/dev/null 2>&1; then
  PKGS=$(dpkg-query -W -f='${Package} ${Version}\n' 2>/dev/null | awk '{printf "%s{\"name\":\"%s\",\"version\":\"%s\"}", (NR>1?",":""), $1, $2}' | head -c 200000)
elif command -v rpm >/dev/null 2>&1; then
  PKGS=$(rpm -qa --queryformat '%{NAME} %{VERSION}\n' 2>/dev/null | awk '{printf "%s{\"name\":\"%s\",\"version\":\"%s\"}", (NR>1?",":""), $1, $2}' | head -c 200000)
else
  PKGS=""
fi

cat <<EOF
{"key":"host:$HOST","type":"linux","name":$(json_str "$HOST"),"fqdn":$(json_str "$HOST"),"mgmtIp":$(json_str "$IP"),"source":"ssh",
"attrs":{"os":$(json_str "$OS_PRETTY"),"version":$(json_str "$KERNEL"),"kernel":$(json_str "$UNAME"),"cpu":$(json_str "$CPU_MODEL"),"cpuCores":$(json_str "$CPU_CORES"),"memGb":$(json_str "$MEM_GB"),
"disks":[${DISKS}],"nics":[],"services":[${SERVICES}],"listeningPorts":[${PORTS}],"packages":[${PKGS}]}}
EOF
