#!/usr/bin/env bash
# tshark-rotate.sh — 24/7 rotating ring-buffer capture on a sensor
# Writes pcapng files into a directory, rotating by size and keeping the last N.
# Works on Linux and Windows (under WSL/Git-Bash with tshark installed).
#
# Usage:
#   sudo ./tshark-rotate.sh <iface> <outdir> [filesize_mb] [num_files] [bpf_filter]
# Example:
#   sudo ./tshark-rotate.sh br0 /data/captures 100 50 "not port 22"
set -euo pipefail

IFACE="${1:?usage: $0 iface outdir [filesize_mb] [num_files] [bpf_filter]}"
OUTDIR="${2:?}"
SIZE_MB="${3:-100}"        # per-file size in MB
NUM_FILES="${4:-50}"       # keep last N files
FILTER="${5:-}"

mkdir -p "$OUTDIR"
OUT="$OUTDIR/cap.pcapng"

echo ">> Ring-buffer capture on $IFACE → $OUT (size ${SIZE_MB}MB, keep ${NUM_FILES}, filter: '${FILTER:-none}')"
echo ">> Ctrl+C to stop. Files: $OUT_00001_YYYYmmddHHMMSS.pcapng etc."

# Use dumpcap (lighter than tshark for long runs)
if command -v dumpcap >/dev/null; then
  BIN=dumpcap
  FILTER_ARG=""
  [ -n "$FILTER" ] && FILTER_ARG="-f $FILTER"
  echo ">> Using dumpcap"
  # shellcheck disable=SC2086
  exec $BIN -i "$IFACE" -w "$OUT" -b filesize:"$((SIZE_MB * 1000))" -b files:"$NUM_FILES" $FILTER_ARG
else
  BIN=tshark
  FILTER_ARG=""
  [ -n "$FILTER" ] && FILTER_ARG="-f $FILTER"
  echo ">> dumpcap not found; using tshark"
  # shellcheck disable=SC2086
  exec $BIN -i "$IFACE" -w "$OUT" -b filesize:"$((SIZE_MB * 1000))" -b files:"$NUM_FILES" $FILTER_ARG
fi

# After capture, analyze the latest file:
#   latest=$(ls -t "$OUTDIR"/*.pcapng | head -1)
#   tshark -r "$latest" -Y "tcp.analysis.retransmission"
#   tshark -r "$latest" -o "tls.keylog_file:/tmp/sslkeylog.txt" -Y "http"
