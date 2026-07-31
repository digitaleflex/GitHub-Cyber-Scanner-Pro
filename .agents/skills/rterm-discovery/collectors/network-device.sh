#!/usr/bin/env bash
# network-device.sh — agentless network-device collector (SSH + optional SNMP).
# Cisco IOS/IOS-XE/IOS-XR. Emits ONE normalized JSON document to stdout.
# Run over SSH with algorithmsPreset=cisco + termType=vt100. Read-only.
set -u
HOST="${1:-netdevice}"

# These are run as an interactive SSH session's commands; when sourced as a
# script the collector expects the `show` outputs on stdin (piped by the
# playbook). For direct use it falls back to snmpget if available.

json_kv() { printf '"%s":%s' "$1" "$2"; }
jstr() { printf '"%s"' "$(printf '%s' "$1" | tr -d '\r' | sed 's/"/\\"/g')"; }

# --- read captured show-command output from stdin (or empty) ---
OUT="$(cat 2>/dev/null || true)"

VERSION=$(printf '%s\n' "$OUT" | grep -m1 -E 'Cisco IOS (XE )?Software.*Version' | sed -E 's/.*Version ([^, ]+).*/\1/')
MODEL=$(printf '%s\n' "$OUT" | grep -m1 -E '^cisco |^Cisco ' | sed -E 's/[Cc]isco ([A-Za-z0-9-]+).*/\1/')
SERIAL=$(printf '%s\n' "$OUT" | grep -m1 -E 'Processor board ID|Chassis Serial|Serial Number' | sed -E 's/.*: //')
UPTIME=$(printf '%s\n' "$OUT" | grep -m1 -E 'uptime is' | sed -E 's/.*uptime is //')

# interfaces (ip interface brief)
IFACES=$(printf '%s\n' "$OUT" | awk '/Interface/{next} /IP-Address/{next} /^(Gi|Fa|Eth|Te|Hu|Fo|Lo|Vl|Tu|Se|BDI|BVI|Mgmt|Port)/{gsub(/\r/,""); printf "%s{\"name\":\"%s\",\"ip\":\"%s\",\"status\":\"%s\"}", (c++?",":""), $1, $2, $(NF-1)}' | head -c 40000)

# neighbors (cdp/lldp) -> links
NEIGHBORS=$(printf '%s\n' "$OUT" | awk '/Device ID/{gsub(/\r/,""); printf "%s%s", (c++?",":""), $NF}' | head -c 20000)

# SNMP fallback when ssh output is empty and snmpget exists
if [ -z "$VERSION" ] && command -v snmpget >/dev/null 2>&1 && [ -n "${SNMP_COMMUNITY:-}" ] && [ -n "${SNMP_HOST:-}" ]; then
  VERSION=$(snmpget -v2c -c "$SNMP_COMMUNITY" -Ovq "$SNMP_HOST" 1.3.6.1.2.1.1.1.0 2>/dev/null | tr -d '"')
fi

cat <<EOF
{"key":"host:$HOST","type":"netdevice","name":$(jstr "$HOST"),"fqdn":$(jstr "$HOST"),"mgmtIp":$(jstr "${MGMT_IP:-}"),"source":"ssh",
"attrs":{"os":$(jstr "Cisco IOS"),"version":$(jstr "$VERSION"),"model":$(jstr "$MODEL"),"serial":$(jstr "$SERIAL"),"uptime":$(jstr "$UPTIME"),
"nics":[${IFACES}],"listeningPorts":[],"packages":[]},
"links":[${NEIGHBORS}]}
EOF
