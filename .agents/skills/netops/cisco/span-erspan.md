# Cisco SPAN / RSPAN / ERSPAN — authoritative configs

Verified against Cisco IOS-XE 17.x configuration guides and NetworkLessons ERSPAN walkthrough. Syntax matches Catalyst 9300, Catalyst 8000 (Cat 8K), and Nexus.

**Platform support:** SPAN/RSPAN on most Catalyst switches. **ERSPAN on IOS-XE & NX-OS only** (Catalyst 9300, Cat 8K, Nexus). **NOT supported** on small IOS switches (Catalyst 2960, 1000 series, etc.) — check `show platform` / feature navigator before planning ERSPAN.

---

## 1. Local SPAN — same switch

### IOS-XE (Catalyst 9300 / Cat 8K)
```
configure terminal
! Source can be an interface, a port-channel, or a VLAN
monitor session 1 source interface Gi1/0/1 both          ! rx | tx | both
monitor session 1 destination interface Gi1/0/24         ! sensor plugged here
! Optionally filter VLANs on a trunk source:
! monitor session 1 filter vlan 10-20
end
show monitor session 1
! Remove:
no monitor session 1
```

### NX-OS (Nexus)
```
monitor session 1
  source interface Ethernet1/1 both
  destination interface Ethernet1/24
  no shut
```

### Verification
```
show monitor                                       ! all sessions
show monitor session 1                             ! details
show interface Gi1/0/24                             ! destination port up?
```

### Caveats
- Destination port speed **must ≥ source speed** (mirroring 10G→1G drops frames)
- Use `both` direction or you see only half the conversation
- Destination port is monitoring-only — no normal traffic while SPAN is active
- SPAN strips some L2 info (VLAN tags depending on config); not ideal for deep L2 forensics

---

## 2. RSPAN — across switches, same L2 domain

Mirror to a sensor on a different switch via a dedicated RSPAN VLAN.

### IOS-XE
```
! On BOTH switches — define the RSPAN VLAN
vlan 999
 name RSPAN_VLAN
 remote-span
exit

! Source switch
monitor session 1 source interface Gi1/0/1 both
monitor session 1 destination remote vlan 999

! Destination switch (sensor here)
monitor session 2 source remote vlan 999
monitor session 2 destination interface Gi1/0/24
```

### NX-OS
```
vlan 999
  remote-span
monitor session 1
  source interface Ethernet1/1 both
  destination remote vlan 999
monitor session 2
  source remote vlan 999
  destination interface Ethernet1/24
```

### Caveats
- RSPAN VLAN must be trunked between switches
- RSPAN VLAN traffic is flooded — watch broadcast impact on trunks
- Don't use the RSPAN VLAN for normal traffic

---

## 3. ERSPAN — across L3, via GRE encapsulation

Mirror across Layer 3 by encapsulating mirrored frames in GRE. Sensor can be anywhere reachable by IP.

### IOS-XE SOURCE session (verified — Cisco 17.x guide + NetworkLessons)
```
configure terminal
monitor session 1 type erspan-source
 source interface GigabitEthernet 2 rx               ! rx | tx | both
 no shutdown
 destination
  erspan-id 100                                      ! must match destination
  ip address 172.16.2.200                            ! sensor's IP
  origin ip address 172.16.12.1                      ! source IP for GRE outer header
  mtu 1464                                           ! account for GRE overhead (~24 bytes)
 exit
end
show monitor session 1
```

### IOS-XE DESTINATION session (if terminating GRE on a router that forwards to the sensor)
```
configure terminal
monitor session 1 type erspan-destination
 destination interface GigabitEthernet 2             ! sensor plugged here
 source
  erspan-id 100                                      ! must match source
  ip address 172.16.2.200                            ! must match source's destination IP
 exit
 no shutdown
end
show monitor session 1
```

> **Common pattern:** the sensor (Linux/Windows) receives raw GRE packets directly — no destination router needed. tshark auto-decaps GRE. For netwatch/rustnet, decap first (see `scripts/erspan-decap.sh`).

### NX-OS (Nexus) SOURCE
```
monitor session 1 type erspan-source
  source interface Ethernet1/1 both
  destination ip 10.20.30.40                         ! sensor IP
  erspan-id 101
  mtu 1464
  no shut
```

### NX-OS DESTINATION (optional, if Nexus terminates)
```
monitor session 2 type erspan-destination
  destination interface Ethernet1/24
  source ip 10.20.30.40
  erspan-id 101
  no shut
```

### Verification (source side)
```
show monitor session 1
show monitor session 1 detail                        ! includes GRE stats
ping <sensor-ip> source <origin-ip>                 ! confirm L3 reachability
```

### Sensor side (Linux, decapsulating)
```bash
# tshark auto-decaps GRE — just capture
sudo tshark -i eth0 -w erspan.pcap
# Extract inner packets to a clean pcap
editcap --extract-gre erspan.pcap inner.pcap
tshark -r inner.pcap -Y "tcp.analysis.retransmission"
# For netwatch/rustnet which don't auto-decap, use a GRE tunnel interface or the decap script:
# scripts/erspan-decap.sh (uses a Linux GRE tunnel to decap, then netwatch on the tunnel)
```

### ERSPAN caveats
- **GRE overhead ~24 bytes** — set MTU 1464 to avoid outer-packet fragmentation
- **Not on small IOS switches** (Catalyst 2960/1000) — IOS-XE & NX-OS only
- **ERSPAN-ID must match** between source and destination
- Sensor sees traffic as if on the source port, but GRE-encapsulated — **decap before deep analysis**
- ERSPAN is one-way (source → sensor); sensor can't inject

---

## Which SPAN flavor to pick

| Need | Use |
|---|---|
| Watch one port, sensor on same switch | **Local SPAN** |
| Watch one port, sensor on different switch, same L2 | **RSPAN** |
| Watch one port, sensor across L3 / different data center | **ERSPAN** |
| Watch a whole VLAN | Local SPAN with VLAN source |
| Multiple sources → one sensor | ERSPAN from many devices → one Linux sensor (scales!) |
| Need to capture line-rate guaranteed | Don't use SPAN — use an inline Linux bridge sensor |

---

## Coupling SPAN with the right tool

After configuring SPAN/ERSPAN, pick the sensor tool by goal:

| Goal | Tool on the sensor |
|---|---|
| Live TUI, full packets, TLS decrypt, threats | `netwatch` (Linux) |
| Live TUI, process attribution (Windows) | `rustnet -i "Ethernet"` |
| Regex on payload fast | `ngrep -d eth0 'pattern'` |
| Scripted capture to disk with rotation | `dumpcap -i eth0 -b filesize:100000 -b files:50` |
| Headless Windows capture | `pktmon start --capture --comp nics` |
| IDS / attack detection | `suricata -i eth0` (Linux/Windows) |

Always verify with `show monitor` on the Cisco side and `pktmon counters` / `ethtool -S` on the sensor side that traffic is actually arriving before debugging why your tool shows nothing.
