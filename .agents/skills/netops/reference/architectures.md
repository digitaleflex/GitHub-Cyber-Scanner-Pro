# Capture Architectures — how a sensor sees traffic

This file covers every way to get packets in front of a sensor, with configs, trade-offs, and platform constraints. Verified against Cisco IOS-XE 17.x config guides and NetworkLessons ERSPAN walkthrough.

**The one rule above all:** a true **transparent Layer-2 inline bridge is Linux-only.** Windows has no clean equivalent. Choose the architecture by what you can change and where the traffic is.

---

## Architecture Decision Matrix

| Situation | Architecture | Sensor OS | SPOF? | Sees both dirs? | Fidelity |
|---|---|---|---|---|---|
| Watch a Cisco port, can't install on box | SPAN (local) | Linux/Win | No | Yes (if `both`) | Good (oversubscription risk) |
| Mirror across switches, same L2 | RSPAN | Linux/Win | No | Yes | Good |
| Mirror across L3 / data center | ERSPAN (GRE) | Linux/Win | No | Yes | Good (GRE overhead) |
| Permanent deep eyes on critical uplink | **Transparent Linux bridge** (`br0`) | **Linux only** | **Yes (use bypass tap)** | Yes | **Best** |
| Inline with one NIC, accept routing changes | L3 gateway/router | Linux/Win | Yes | Yes (hairpin) | Good (L3, not L2) |
| Watch a single host's own traffic | Host-based | Linux: all tools · Win: RustNet/Pktmon/tshark | No | Yes | Best (it's the host's NIC) |
| VM-to-VM traffic | vSwitch mirror/SPAN | Sensor VM (1 vNIC) | No | Yes | Good |
| Fleet-wide, no packets | NetFlow/IPFIX/sFlow → collector | ntopng/PRTG | No | n/a (flows) | Summaries only |

---

## 1. SPAN (local) — Switched Port ANalyzer

The classic "copy this port's traffic to another port where my sensor listens."

### When
- You want to watch traffic on a specific Cisco switch port or VLAN
- The sensor is on the **same switch** as the source
- Can't install software on the Cisco box itself

### IOS-XE config (Catalyst 9300, Cat 8K)
```
! On the Cisco switch
configure terminal
monitor session 1 source interface Gi1/0/1 both      ! rx/tx/both
monitor session 1 destination interface Gi1/0/24      ! sensor plugged here
end
show monitor session 1
! Remove when done:
no monitor session 1
```

### Sensor side
Plug the sensor into Gi1/0/24, then:
```bash
# Linux sensor
sudo netwatch          # or rustnet -i eth0 / tshark -i eth0
# Windows sensor (RustNet)
rustnet -i "Ethernet"          # as Administrator
# Windows sensor (Pktmon, headless)
pktmon start --capture --comp nics -m real-time
```

### Caveats
- **Destination port speed must ≥ source speed.** Mirroring a 10G source to a 1G destination drops frames.
- **`both` direction or you see only half the conversation.**
- **Oversubscription:** if source traffic exceeds destination port's capacity, frames drop silently. SPAN is for diagnosis, not line-rate capture guarantees.
- Destination port is **monitoring-only** — it can't carry normal traffic while a SPAN session is active.
- SPAN strips some Layer-2 info depending on config; not ideal for deep L2 forensics.

---

## 2. RSPAN — Remote SPAN (across switches, same L2)

Mirror traffic to a sensor on a **different switch** via a dedicated RSPAN VLAN.

### When
- Source and sensor are on different switches but same Layer-2 domain
- You want one central sensor for multiple access switches

### IOS-XE config
```
! On BOTH switches — define the RSPAN VLAN
vlan 999
 name RSPAN_VLAN
 remote-span
exit

! Source switch
monitor session 1 source interface Gi1/0/1 both
monitor session 1 destination remote vlan 999

! Destination switch (where the sensor is)
monitor session 2 source remote vlan 999
monitor session 2 destination interface Gi1/0/24
```

### Caveats
- The RSPAN VLAN must be trunked between switches
- RSPAN VLAN traffic is flooded — be mindful of broadcast impact
- Same oversubscription/direction caveats as local SPAN

---

## 3. ERSPAN — Encapsulated Remote SPAN (across L3, via GRE)

Mirror traffic across **Layer 3** by encapsulating mirrored frames in GRE. The sensor can be anywhere reachable by IP.

### When
- Source and sensor are in different subnets/data centers
- You want to centralize sensors (one sensor receives ERSPAN from many devices)
- **IOS-XE & NX-OS only** — Catalyst 9300, Cat 8K, Nexus. **NOT** supported on small IOS switches.

### IOS-XE source config (verified — NetworkLessons/Cisco 17.x guide)
```
configure terminal
monitor session 1 type erspan-source
 source interface GigabitEthernet 2 rx          ! rx/tx/both
 no shutdown
 destination
  erspan-id 100
  ip address 172.16.2.200                       ! the sensor's IP
  origin ip address 172.16.12.1                 ! source IP for the GRE tunnel
  mtu 1464                                     ! account for GRE overhead
 exit
end
show monitor session 1
```

### IOS-XE destination config (if terminating on a router that strips GRE)
```
monitor session 1 type erspan-destination
 destination interface GigabitEthernet 2        ! sensor plugged here
 source
  erspan-id 100
  ip address 172.16.2.200                        ! must match source's destination IP
 exit
no shutdown
```

> **Common pattern:** the sensor itself (Linux/Windows) receives raw GRE packets directly — no destination router needed. The sensor's capture tool decapsulates. Wireshark/tshark auto-decaps GRE by default; netwatch/rustnet may need explicit decap (see `scripts/erspan-decap.sh`).

### NX-OS config (Nexus)
```
monitor session 1 type erspan-source
  source interface Ethernet1/1 both
  destination ip 10.20.30.40
  erspan-id 101
  mtu 1464
  no shut
```

### Sensor side (Linux, decapsulating)
```bash
# tshark auto-decaps GRE — just capture:
sudo tshark -i eth0 -w erspan.pcap
# Or extract inner packets to a clean pcap:
editcap --extract-gre erspan.pcap inner.pcap
# Then analyze inner.pcap:
tshark -r inner.pcap -Y "tcp.analysis.retransmission"
# For netwatch/rustnet which don't auto-decap, use the decap script:
# (see scripts/erspan-decap.sh — uses tc/iptables or a GRE tunnel interface)
```

### Caveats
- **GRE overhead** (~24 bytes/ packet) — set MTU to 1464 to avoid fragmentation of the outer packet
- **Not on small IOS switches** (e.g. Catalyst 2960) — only IOS-XE & NX-OS platforms
- ERSPAN-ID must match between source and destination
- The sensor sees traffic as if it were on the source port — but with GRE encapsulation; decap before deep analysis

---

## 4. Transparent Linux bridge — inline, highest fidelity

**Linux only.** The sensor sits physically inline on the cable path, bridging two NICs at Layer 2 so traffic passes through unchanged, while netwatch taps the bridge.

### When
- You want permanent, highest-fidelity, full-duplex visibility on a critical uplink
- You can tolerate a SPOF **with a bypass tap** (or accept the risk in a maintenance window)
- You need accurate RTT/handshake timing (better than SPAN's mirroring jitter)

### The picture
```
[Cisco device] ──cable── [ 🖥️ Linux sensor ] ──cable── [rest of network]
   Gi0/0                eth0        (br0)        eth1
```

### Bridge setup (runtime — see `scripts/bridge-setup.sh` for persistent)
```bash
# Two NICs: eth0 (to Cisco), eth1 (to upstream)
ip link set eth0 down
ip link set eth1 down
ip addr flush dev eth0
ip addr flush dev eth1

ip link add name br0 type bridge
ip link set eth0 master br0
ip link set eth1 master br0
ip link set br0 type bridge stp_state 0          # NO STP — transparent pipe
ip link set eth0 up
ip link set eth1 up
ip link set br0 up

# Optional management IP on br0 (for SSHing to the sensor — NOT for bridged traffic)
ip addr add 10.255.1.10/24 dev br0

# CRITICAL: disable offloads so netwatch sees real frames (not re-segmented blobs)
ethtool -K eth0 gro off tso off lro off gso off
ethtool -K eth1 gro off tso off lro off gso off
ethtool -K br0  gro off tso off lro off gso off
```

### Persistent (Ubuntu netplan)
```yaml
# /etc/netplan/01-bridge.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0: {dhcp4: no}
    eth1: {dhcp4: no}
  bridges:
    br0:
      interfaces: [eth0, eth1]
      stp: false
      forward-delay: 0
      addresses: [10.255.1.10/24]
      routes:
        - to: default
          via: 10.255.1.1
```
Apply: `sudo netplan apply`. See `scripts/bridge-setup.sh` for RHEL/NetworkManager variant.

### Run netwatch on the bridge
```bash
# netwatch has no -i flag — pin the interface via config OR select in the TUI Interfaces tab (press 3)
sed -i 's/^capture_interface = ""/capture_interface = "br0"/' ~/.config/netwatch/config.toml
sudo netwatch                       # ALWAYS br0, never eth0/eth1
SSLKEYLOGFILE=/tmp/k.txt sudo netwatch   # + TLS decrypt
```

### Why capture on `br0` not the NICs
- `eth0` sees only Cisco→upstream direction
- `eth1` sees only upstream→Cisco direction
- `br0` (the bridge) sees **both** because the bridge merges them — the only interface that sees the full conversation
- Capturing on a single NIC makes you miss half of every bidirectional handshake

### Caveats
- **SPOF without a bypass tap.** A sensor crash = link down. Buy a bypass NIC (Solarflare/Intel/Silicom) or hardware tap that fails open.
- **Disable STP on br0.** You don't want the bridge participating in spanning tree.
- **Never bridge inside a LACP bundle.** Bridge *before* the bundle splits or use a tap that handles bundles.
- **Sensor NICs faster than the link.** A 1G link on 10G NICs never drops.
- **Landlock sandbox (Linux 5.13+):** netwatch auto-hardens; rustnet does too.

---

## 5. L3 gateway / router mode — inline with ONE NIC

**Works on Linux AND Windows.** The sensor becomes the default gateway for a subnet; traffic hairpins in and out the same NIC.

### When
- You have only one NIC available
- You can change the default-gateway setting on the hosts you want to observe (or DHCP-option it)
- You accept a routed hop (TTL decrements, sensor MAC appears)

### Linux setup
```bash
sysctl -w net.ipv4.ip_forward=1
# Assign the gateway IP that hosts point at, e.g. on eth0:
ip addr add 10.0.0.1/24 dev eth0
# Hosts on the subnet use 10.0.0.1 as their default gateway
sudo netwatch     # sees both directions on the one NIC (hairpin)
```
Persistent: `net.ipv4.ip_forward=1` in `/etc/sysctl.d/99-forward.conf`.

### Windows setup (see `scripts/win-l3-gateway.ps1`)
```powershell
# Enable IP forwarding
Set-NetIPInterface -Forwarding Enabled
# Assign the gateway IP
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 10.0.0.1 -PrefixLength 24
# (Optional) NAT to upstream if needed:
New-NetNat -Name "SensorNAT" -InternalIPInterfaceAddressPrefix 10.0.0.0/24
# Then run RustNet on the interface
rustnet -i "Ethernet"
```

### Caveats
- **Invasive** — change gateway on every observed host (or via DHCP option 3)
- It's a **routed hop**: TTL decrements, non-IP traffic (ARP, some broadcasts) doesn't traverse cleanly
- Still a SPOF (subnet loses gateway if sensor dies) — mitigate with VRRP/keepalived to a backup
- L3, not L2 — you lose pure Layer-2 visibility (frame-level forensics, non-IP protocols)

---

## 6. One-armed SPAN — single-NIC passive listener

**Linux AND Windows.** One NIC plugged into a SPAN destination port. Not inline — passive.

### When
- Single NIC, passive listening, accept it's SPAN (not bridging)
- The cleanest single-NIC approach

### Setup
```
[Cisco] ──SPAN── [sensor eth0: netwatch/rustnet/tshark/pktmon]
```
```bash
sudo netwatch       # Linux
rustnet -i "Ethernet"       # Windows (Admin)
pktmon start --capture --comp nics -m real-time   # Windows headless
```

### Caveats
- Consumes a SPAN destination port on the switch
- Same SPAN oversubscription/direction caveats
- Not "inline" — you can't inject, only observe

---

## 7. Host-based — run the tool on the host itself

**Linux: any tool. Windows: RustNet/Pktmon/tshark.** No sensor needed — the host's own NIC is the capture interface.

### When
- You want to observe a **single host's** own traffic (what is THIS app talking to?)
- Linux app server with a stuck connection
- Windows server you can log into

### Linux
```bash
sudo rustnet                                # see which process owns each connection
sudo netwatch                               # full packet view of this host's traffic
sudo tshark -i any -f "tcp port 443" -w cap.pcapng
```

### Windows
```powershell
rustnet -i "Ethernet"                        # process-attributed TUI (Admin)
pktmon start --capture --comp nics -m real-time   # headless
tshark -i "Ethernet" -f "tcp port 443" -w cap.pcapng  # if Wireshark/Npcap installed
```

### Caveats
- Only sees that host's traffic — not the network's
- For Windows, **RustNet is preferred** over the undocumented Windows netwatch build
- For host-based you do NOT need a bridge or SPAN — the NIC is the source

---

## 8. vSwitch mirror / SPAN — VM-to-VM traffic

### When
- Traffic between VMs on a hypervisor (Hyper-V, KVM, ESXi)
- No physical NICs involved

### Hyper-V
```powershell
# Enable mirroring on the vSwitch port for the sensor VM
Set-VMNetworkAdapter -VMName SensorVM -RouterGuard Enabled -AllowTeaming On
# On the vSwitch, set the sensor VM's port as the destination:
Set-VMNetworkAdapter -VMName SensorVM -PortMirroring Destination
Set-VMNetworkAdapter -VMName TargetVM  -PortMirroring Source
```

### KVM/libvirt (set up a mirror via `virsh`)
```bash
# Add a mirror to a libvirt network (advanced; see libvirt net-dumpxml)
# Or attach the sensor VM's vNIC to the bridge in "mirror" mode via vnet setup
```

### ESXi
- vSphere Distributed Switch → port mirroring session → sensor VM's port as destination

### Sensor side
Sensor VM with one vNIC sees the mirrored traffic. Run netwatch/rustnet/tshark on that vNIC as usual.

---

## 9. NetFlow / IPFIX / sFlow — fleet-wide, no packets

### When
- You need fleet-wide traffic visibility across hundreds of interfaces
- You don't need packet-level truth (flows are summaries)
- You want to scale without sensors in the datapath and without SPOFs

### Cisco device export (IOS-XE)
```
! Export NetFlow from interface
interface Gi0/0
 ip flow monitor NFMON sampler NFMON input
!
flow exporter NFE
 destination 10.20.30.40                    ! collector
 source Gi0/1
 transport udp 2055
!
flow monitor NFMON
 exporter NFE
 record netflow ipv4 original-input
!
flow sampler NFMON
 mode random 1 out-of 100
```

### Collectors (run on Linux/Windows)
- **ntopng** (`ntop/ntopng`) — web dashboard, NetFlow/sFlow ingestion, scales
- **ManageEngine NetFlow Analyzer** / **PRTG** / **SolarWinds NTA** — commercial, Windows-installable
- **CESNET ipfixcol2** — open-source IPFIX collector

### Caveats
- **Flow records are summaries, not packets** — no TLS handshake timing, no JA4, no retransmit detail
- Sampled flows (`1 out-of 100`) miss low-volume conversations
- Use as the **wide telemetry layer** that tells you where to point a packet sensor

---

## Bypass tap — fail-open hardware (for production inline bridges)

A bypass network tap is a small inline device that, on power loss or sensor failure, electrically connects its two inline ports directly so the link stays up. Non-negotiable for any production inline bridge.

### Topologies
```
# Dual-NIC bypass card in the sensor (most common)
[Cisco] ── bypass NIC eth0 ← sensor → bypass NIC eth1 ── [upstream]
         (on power loss: eth0↔eth1 connect directly via relay)

# Standalone hardware tap (sensor attaches to monitor ports)
[Cisco] ──┬── [upstream]                 (inline path always passes)
          │
          monitor-A ── sensor eth0
          monitor-B ── sensor eth1        (full-duplex = 2 monitor ports = 2 NICs)
```

### When to use which
- **Bypass NIC** — sensor is the inline element; fail-open is a relay inside the NIC
- **Hardware tap** — tap is the inline element (always passive, never a SPOF); sensor attaches to monitor ports; usually needs 2 NICs (one per direction) unless you use an aggregator tap (combines both directions onto one RX, but loses direction info and can drop under high bidir load)

### Vendors
Solarflare, Intel, Silicom make bypass NICs with Linux drivers. Windows bypass driver support is spotty — another reason inline bridges run on Linux.

---

## Quick "which architecture?" picker

```
Q: Can you install software on the device you want to watch?
   YES → host-based (run netwatch/rustnet/tshark/pktmon on it)
   NO  → continue

Q: Is the device a Cisco switch/router?
   YES → you can SPAN/RSPAN/ERSPAN a port → one-armed sensor (Linux or Windows)
   NO  → continue

Q: Do you need permanent, highest-fidelity, full-duplex on a critical uplink?
   YES → transparent Linux bridge (br0) + bypass tap  [Linux only]
   NO  → continue

Q: Only one NIC available and you can change host gateways?
   YES → L3 gateway/router mode (Linux or Windows)
   NO  → continue

Q: VM-to-VM traffic?
   YES → vSwitch mirror/SPAN

Q: Fleet-wide, no packets, just flows?
   YES → NetFlow/IPFIX/sFlow → collector (ntopng/PRTG)
```
