#!/usr/bin/env bash
# bridge-setup.sh — persistent transparent Layer-2 bridge for a NetOps sensor
# Linux only (Ubuntu/Debian netplan + RHEL/Fedora NetworkManager variants)
#
# Usage:
#   sudo ./bridge-setup.sh eth0 eth1 br0 [mgmt_ip_cidr] [mgmt_gw]
# Example:
#   sudo ./bridge-setup.sh eth0 eth1 br0 10.255.1.10/24 10.255.1.1
#
# Creates br0, enslaves eth0 + eth1, disables STP, disables offloads (capture fidelity),
# and writes persistent config (netplan on Debian/Ubuntu, ifcfg on RHEL/Fedora).
set -euo pipefail

[ $EUID -eq 0 ] || { echo "Run as root (sudo)."; exit 1; }
NIC0="${1:?usage: $0 nic0 nic1 br0 [mgmt_ip_cidr] [mgmt_gw]}"
NIC1="${2:?}"
BR="${3:-br0}"
MGMT_IP="${4:-}"
MGMT_GW="${5:-}"

echo ">> Building bridge $BR from $NIC0 + $NIC1"

# Runtime setup (immediate)
ip link set "$NIC0" down || true
ip link set "$NIC1" down || true
ip addr flush dev "$NIC0" || true
ip addr flush dev "$NIC1" || true

ip link add name "$BR" type bridge 2>/dev/null || ip link set "$BR" type bridge
ip link set "$NIC0" master "$BR"
ip link set "$NIC1" master "$BR"
ip link set "$BR" type bridge stp_state 0
ip link set "$NIC0" up
ip link set "$NIC1" up
ip link set "$BR" up

if [ -n "$MGMT_IP" ]; then
  ip addr add "$MGMT_IP" dev "$BR" || true
fi
if [ -n "$MGMT_GW" ]; then
  ip route replace default via "$MGMT_GW" || true
fi

# Disable offloads so netwatch/tshark see real frames, not re-segmented blobs
for i in "$NIC0" "$NIC1" "$BR"; do
  ethtool -K "$i" gro off tso off lro off gso off 2>/dev/null || true
done

# Persistent config
if command -v netplan >/dev/null && [ -d /etc/netplan ]; then
  echo ">> Writing /etc/netplan/99-netops-bridge.yaml (persistent)"
  GATEWAY_BLOCK=""
  [ -n "$MGMT_GW" ] && GATEWAY_BLOCK="      routes: [{to: default, via: $MGMT_GW}]"
  cat > /etc/netplan/99-netops-bridge.yaml <<EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    $NIC0: {dhcp4: no}
    $NIC1: {dhcp4: no}
  bridges:
    $BR:
      interfaces: [$NIC0, $NIC1]
      stp: false
      forward-delay: 0
EOF
  [ -n "$MGMT_IP" ] && echo "      addresses: [$MGMT_IP]" >> /etc/netplan/99-netops-bridge.yaml
  [ -n "$MGMT_GW" ] && echo "      routes: [{to: default, via: $MGMT_GW}]" >> /etc/netplan/99-netops-bridge.yaml
  netplan apply
elif command -v nmcli >/dev/null; then
  echo ">> Writing NetworkManager persistent config (RHEL/Fedora)"
  nmcli con add type bridge ifname "$BR" stp no
  nmcli con add type ethernet ifname "$NIC0" master "$BR"
  nmcli con add type ethernet ifname "$NIC1" master "$BR"
  [ -n "$MGMT_IP" ] && nmcli con mod bridge-$BR ipv4.addresses "$MGMT_IP" ipv4.method manual
  [ -n "$MGMT_GW" ] && nmcli con mod bridge-$BR ipv4.gateway "$MGMT_GW"
  nmcli con up bridge-$BR
  # offload disable via dispatcher
  cat > /etc/NetworkManager/dispatcher.d/99-netops-offloads.sh <<'EOF'
#!/usr/bin/env bash
for i in NIC0 NIC1 BR0; do ethtool -K "$i" gro off tso off lro off gso off 2>/dev/null || true; done
EOF
  chmod +x /etc/NetworkManager/dispatcher.d/99-netops-offloads.sh
else
  echo "!! No netplan or NetworkManager found — runtime bridge set, not persistent"
fi

# Verification
echo
echo ">> Verify:"
bridge link
ip -s link show "$BR"
ethtool -k "$BR" | grep -E 'generic-receive-offload|tcp-segmentation-offload|generic-segmentation' | grep -v ': fixed'
echo
echo ">> Traffic counters should climb as packets flow through. Capture on $BR:"
echo "   sudo netwatch"
echo "   sudo tshark -i $BR -w cap.pcapng"
