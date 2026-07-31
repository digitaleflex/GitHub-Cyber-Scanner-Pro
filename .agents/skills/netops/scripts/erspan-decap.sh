#!/usr/bin/env bash
# erspan-decap.sh — decapsulate ERSPAN/GRE so netwatch/rustnet/tshark see the inner packets
#
# ERSPAN sends mirrored traffic wrapped in GRE. Wireshark/tshark auto-decaps GRE,
# but netwatch/rustnet don't. This sets up a Linux GRE tunnel interface that decapsulates
# inbound ERSPAN packets, so you can capture on the tunnel interface with any tool.
#
# Prerequisites (on the ERSPAN destination / sensor):
#   - The sensor receives ERSPAN packets on eth0 (gre proto 0xbeef for ERSPAN)
#   - Run as root
#
# Usage:
#   sudo ./erspan-decap.sh <rx_iface> <tunnel_name> [erspan_id]
# Example:
#   sudo ./erspan-decap.sh eth0 erspan0 100
#   # Then: sudo netwatch   (sees the inner/original packets)
set -euo pipefail
[ $EUID -eq 0 ] || { echo "Run as root (sudo)."; exit 1; }

RX="${1:?usage: $0 rx_iface tunnel_name [erspan_id]}"
TUN="${2:-erspan0}"
ERSPAN_ID="${3:-}"

echo ">> Setting up GRE decap on $RX → tunnel $TUN"

# Linux GRE decap: create a GRE tunnel that strips the outer header
# ERSPAN uses GRE protocol 0xbeef (ERSPANv1) or 0x22eb (ERSPANv2)
# Standard gre tunnel with local/remote any
if [ -n "$ERSPAN_ID" ]; then
  # ERSPAN-aware decap (iproute2 supports erspan type)
  ip link add "$TUN" type erspan local any remote any erspan-id "$ERSPAN_ID" seq
else
  ip link add "$TUN" type gre local any remote any
fi
ip link set "$TUN" up

# Enable forwarding so packets entering $RX destined to the GRE decap get handled
sysctl -w net.ipv4.conf.all.rp_filter=0 >/dev/null 2>&1 || true
sysctl -w net.ipv4.conf."$RX".rp_filter=0 >/dev/null 2>&1 || true

echo ">> Tunnel $TUN is up. Capture on it to see inner (decapsulated) ERSPAN traffic:"
echo "   sudo netwatch"
echo "   sudo rustnet -i $TUN"
echo "   sudo tshark -i $TUN -w inner.pcap"
echo
echo ">> Alternative (no tunnel, just decap a saved pcap with editcap):"
echo "   tshark -i $RX -w erspan.pcap"
echo "   editcap --extract-gre erspan.pcap inner.pcap"
echo "   tshark -r inner.pcap -Y 'tcp.port==443'"
echo
echo ">> Cleanup:"
echo "   ip link del $TUN"
