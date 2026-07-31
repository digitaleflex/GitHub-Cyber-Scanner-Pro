#!/usr/bin/env bash
# base-detect.sh — Base Device Detection sweep (reachability + port probe).
# Classifies a host before deep collection: reachable?, OS hint, open ports.
# Emits normalized JSON. Usage: base-detect.sh <host>
set -u
HOST="${1:?host required}"

jstr() { printf '"%s"' "$(printf '%s' "$1" | tr -d '\r' | sed 's/"/\\"/g')"; }

REACHABLE="false"
OS_HINT="unknown"

if ping -c 1 -W 2 "$HOST" >/dev/null 2>&1; then REACHABLE="true"; fi

# port probe (key discovery ports from the ADDM matrix)
probe() { (echo >"/dev/tcp/$HOST/$1") >/dev/null 2>&1 && echo -n "$1 "; }
PORTS=""
for p in 22 135 161 389 443 445 636 902 1433 1521 3306 3940 4100 5985 5986 5988 5989; do
  PORTS="$PORTS$(probe "$p")"
done
PORTS_JSON=$(printf '%s' "$PORTS" | awk '{for(i=1;i<=NF;i++)printf "%s%d",(i>1?",":""),$i}')

# OS hint from open ports
if echo "$PORTS" | grep -qE '(^| )(5985|5986|135|445)( |$)'; then OS_HINT="windows"
elif echo "$PORTS" | grep -qE '(^| )902( |$)'; then OS_HINT="esx"
elif echo "$PORTS" | grep -qE '(^| )22( |$)'; then OS_HINT="unix-or-netdevice"
fi

cat <<EOF
{"key":"host:$HOST","type":"unknown","name":$(jstr "$HOST"),"fqdn":$(jstr "$HOST"),"mgmtIp":$(jstr "$HOST"),"source":"probe",
"attrs":{"reachable":$REACHABLE,"osHint":$(jstr "$OS_HINT"),"openPorts":[${PORTS_JSON}]}}
EOF
