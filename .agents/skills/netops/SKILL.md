---
name: netops
description: The ultimate network troubleshooting skill — a CCIE/RHCE-level reference and decision engine for diagnosing ANY network, connectivity, bandwidth, latency, DNS, TLS, or security problem. Covers packet-level sensors (NetWatch, RustNet, tshark, ngrep, Pktmon), all capture architectures (SPAN/RSPAN/ERSPAN, transparent Linux bridge, L3 gateway, host-based, one-armed SPAN), Windows AND Linux sensor builds, and Cisco native telemetry (SNMP/NETCONF/gNMI/CLI/pyATS). Includes a decision framework that picks the best tool + architecture per symptom, multi-platform command references, and 20+ worked incident scenarios with implementation details, commands, and scripts. Use whenever something is slow, down, dropping, flapping, unreachable, mis-behaving on the wire, or you need to plan/scale a monitoring sensor fleet.
---

# NetOps — Ultimate Network Troubleshooting Skill

You are a **CCIE- and RHCE-level network engineer**. This skill resolves **any** network-related issue — connectivity, bandwidth, latency, packet loss, MTU, DNS, TLS, routing, switching, security/IDS — by picking the **best tool + architecture for the specific symptom** rather than reaching for one tool out of habit.

The skill is organized as an index plus focused subfiles. **Read the Decision Framework first**, then jump to the relevant scenario or reference.

---

## When to Use This Skill

Trigger on any of:
- "X can't reach Y" / "intermittent drops" / "slow" / "high latency" / "packet loss"
- "is this link saturated" / "QoS" / "throughput" / "jumbo frames / MTU black hole"
- "DNS failing" / "TLS handshake failing" / "cert / SNI / cipher" / "QUIC"
- "BGP flapping" / "OSPF adjacency down" / "MAC flapping" / "ARP cache"
- "suspect malware / C2 beaconing / port scan / DNS tunneling"
- "I need to put a sensor on this link" / "monitor this Cisco device"
- "plan a fleet monitoring architecture" / "scale from one box to 500 devices"

---

## The Two-Layer Mental Model (read this first)

Every network problem is solved by combining two layers. Get the layer wrong and you waste hours.

| Layer | Question it answers | Tools | Cost |
|---|---|---|---|
| **Telemetry (wide & cheap)** | *What* changed and *where*? | SNMP, gNMI streaming, NETCONF, CLI `show`, pyATS diffs | Scales to 1000s of devices, no SPOF |
| **Packets (deep & expensive)** | *Why* at the byte level? | NetWatch, RustNet, tshark, ngrep, Pktmon | One sensor per choke point, SPOF risk |

**Rule:** Telemetry tells you *which device/link* is misbehaving. Packets tell you *why*. You almost never start with packets — you start with telemetry (or a user symptom), narrow to a suspect, then escalate to packets on that one suspect. The hybrid is the only production answer.

---

## Decision Framework — pick the tool + architecture

### Step 1 — Classify the symptom (which tool)

| Symptom class | First-line tool | Why | Escalate to |
|---|---|---|---|
| "Which process owns this connection?" | **RustNet** (host) | Native process attribution on Linux/macOS/Windows | netwatch for packets |
| "What's on the wire right now (live TUI)?" | **NetWatch** | Full L7 + TLS decrypt + JA4 + threats + Flight Recorder | tshark for scripted |
| "Find a string/pattern in live traffic" | **ngrep** | Regex on payload, instant | tshark for structured |
| "Capture 24/7 to disk, scriptable, rotate" | **tshark/dumpcap** (Linux/Win) | Industry standard, ring buffers | — |
| "Windows box, can't install anything" | **Pktmon** | Built into Windows 10/11/Server, kernel-level | Wireshark to read ETL→pcapng |
| "Post-hoc deep forensic decode of a pcap" | **Wireshark** / **tshark** | Reference dissectors | — |
| "Detect attacks / C2 / scans across a fleet" | **Suricata** + SIEM | Production IDS, EVE JSON | netwatch for live single-host |
| "Is the Cisco device/interface healthy?" | **SNMP / gNMI / CLI** | Native telemetry, scales | netwatch on a SPAN of that port |
| "Did my change break anything?" | **pyATS/Genie** | Pre/post structured diff | — |
| "Web dashboard / NOC wall, ingest NetFlow" | **ntopng** | Browser view, flow ingestion | — |

### Step 2 — Pick the capture architecture (how the sensor sees traffic)

The right architecture depends on **where the traffic is** and **what you can change**. See `reference/architectures.md` for full details.

| Situation | Architecture | Sensor OS | Notes |
|---|---|---|---|
| Watch a Cisco port, can't install on the box | **SPAN** (local) / **RSPAN** (remote VLAN) / **ERSPAN** (L3+GRE) | Linux or Windows | One-armed listener; no SPOF; oversubscription risk |
| Permanent deep eyes on a critical uplink | **Transparent Linux bridge** (`br0`) inline | **Linux only** | 2 NICs + bypass tap; highest fidelity; SPOF w/o bypass |
| Inline with one NIC, accept routing changes | **L3 gateway/router** mode | Linux or Windows | Hosts point at sensor as gateway; hairpin routing |
| Watch a single host's own traffic | **Host-based** (run tool on the host) | Linux: any tool · Windows: RustNet/Pktmon/tshark | No sensor needed |
| VM-to-VM traffic on a hypervisor | **vSwitch mirror/SPAN** | Sensor VM, 1 vNIC | No physical NICs |
| Fleet-wide, no packets, just flow summaries | **NetFlow/IPFIX/sFlow** from Cisco → collector | ntopng/PRTG/ManageEngine | Scales, no SPOF, no packet truth |

### Step 3 — Confirm the platform constraints

| Constraint | Implication |
|---|---|
| **True transparent L2 inline bridge** | **Linux only.** Windows has no clean `br0` equivalent. Use Linux at inline choke points. |
| **Windows sensor** | Use as host-based, SPAN-destination, or L3-gateway. **Never** a transparent inline bridge. |
| **Bypass tap (fail-open on power loss)** | Non-negotiable on any *production* inline bridge. Buy a dual-port bypass NIC or hardware tap. |
| **SPAN oversubscription** | Destination port must match/exceed source speed; `both` direction or you see half the conversation. |
| **ERSPAN** | IOS-XE & NX-OS only (Catalyst 9300, Cat 8K, Nexus). NOT supported on small IOS switches. |
| **eBPF process attribution** | Linux only. macOS uses PKTAP, Windows uses native APIs (RustNet). |
| **TLS decryption (`SSLKEYLOGFILE`)** | Only for traffic **you control** (your client/browser). Never third-party or malware. Works on netwatch + tshark + Wireshark. |

### Step 4 — Run the scenario playbook

Jump to the matching file in `scenarios/`:

- **[scenarios/connectivity.md](./scenarios/connectivity.md)** — "can't reach X", intermittent failures, SYN_SENT hangs, CLOSE_WAIT leaks, ARP/MAC issues, routing black holes
- **[scenarios/bandwidth-latency.md](./scenarios/bandwidth-latency.md)** — saturation, throughput, jitter, RTT spikes, retransmits, QoS, bufferbloat
- **[scenarios/mtu-path.md](./scenarios/mtu-path.md)** — PMTUD black holes, MSS clamping, jumbo frames, fragmentation
- **[scenarios/dns.md](./scenarios/dns.md)** — NXDOMAIN, SERVFAIL, timeout, hijack, split-horizon, DNS tunneling
- **[scenarios/tls-https.md](./scenarios/tls-https.md)** — handshake failures, cert/SNI/cipher, OCSP, HTTP/2 & QUIC, `SSLKEYLOGFILE` decryption
- **[scenarios/security-ids.md](./scenarios/security-ids.md)** — C2 beaconing, port scans, DNS tunneling, Suricata deployment, evidence capture
- **[scenarios/cisco-fleet.md](./scenarios/cisco-fleet.md)** — BGP/OSPF flaps, interface errors, VLAN/VRF, IOS-XE/NX-OS specifics, pyATS change validation

---

## Skill File Index

### Reference (deep command references — accuracy-verified)
- **[reference/tools.md](./reference/tools.md)** — Exact syntax for **NetWatch, RustNet, tshark, ngrep, Pktmon** (every flag you'll use)
- **[reference/architectures.md](./reference/architectures.md)** — SPAN / RSPAN / ERSPAN / Linux bridge / L3 gateway / one-armed / vSwitch — when, how, configs, trade-offs
- **[reference/sensor-builds.md](./reference/sensor-builds.md)** — Step-by-step sensor build recipes: **Linux bridge sensor**, **Windows SPAN sensor**, **Windows L3 gateway sensor**, **headless streaming sensor**, bypass-tap wiring

### Cisco native telemetry (the wide/cheap layer)
- **[cisco/telemetry.md](./cisco/telemetry.md)** — SNMP, gNMI streaming, NETCONF/RESTCONF, CLI `show` reference, pyATS/Genie testbed + diff
- **[cisco/span-erspan.md](./cisco/span-erspan.md)** — Authoritative SPAN/RSPAN/ERSPAN configs for **IOS-XE** (Catalyst 9300, Cat 8K) and **NX-OS** (Nexus), with verification commands

### Scenarios (worked incidents)
- **[scenarios/connectivity.md](./scenarios/connectivity.md)**
- **[scenarios/bandwidth-latency.md](./scenarios/bandwidth-latency.md)**
- **[scenarios/mtu-path.md](./scenarios/mtu-path.md)**
- **[scenarios/dns.md](./scenarios/dns.md)**
- **[scenarios/tls-https.md](./scenarios/tls-https.md)**
- **[scenarios/security-ids.md](./scenarios/security-ids.md)**
- **[scenarios/cisco-fleet.md](./scenarios/cisco-fleet.md)**

### Scripts (ready to run)
- **[scripts/bridge-setup.sh](./scripts/bridge-setup.sh)** — Persistent transparent `br0` bridge on Ubuntu/Debian (netplan) and RHEL (NetworkManager)
- **[scripts/win-l3-gateway.ps1](./scripts/win-l3-gateway.ps1)** — Turn a Windows box into an L3 gateway sensor (IP-Forward + NAT optional)
- **[scripts/tshark-rotate.sh](./scripts/tshark-rotate.sh)** — 24/7 rotating ring-buffer capture to disk
- **[scripts/pktmon-sensor.ps1](./scripts/pktmon-sensor.ps1)** — Headless Pktmon capture-to-ETL with rotation + pcapng conversion
- **[scripts/erspan-decap.sh](./scripts/erspan-decap.sh)** — Decapsulate ERSPAN/GRE so netwatch/tshark see the inner packets
- **[scripts/symptom-router.sh](./scripts/symptom-router.sh)** — Interactive: symptom → recommended tool + architecture (the decision framework as a script)

---

## The 30-Second Triage (use this first)

Before touching any tool, gather these 5 facts. 80% of "mysterious" problems are solved here.

```
1. WHO reported it, WHEN did it start, WHAT changed recently?
2. WHAT is the exact symptom? (timeout? refused? slow? intermittent? which app?)
3. SCOPE: one host? one subnet? one app? everyone? time-of-day pattern?
4. LAYER: is it DNS? (nslookup/dig) routing? (traceroute/mtr) transport? (ping/tcp) app? (curl)
5. FROM WHERE? reproduce from the affected host AND from a known-good host — compare.
```

Then:

| Symptom | First command (run from the affected host) |
|---|---|
| "can't reach X" | `mtr -rwzbc 100 <X>` (path + loss per hop) |
| "slow / latency" | `mtr -rwzbc 100 --tcp --port 443 <X>` (TCP path) |
| "DNS weird" | `dig +trace <name>` + `getent hosts <name>` |
| "TLS failing" | `openssl s_client -connect <X>:443 -servername <sni>` |
| "HTTP failing" | `curl -v --max-time 10 <url>` (read the `*` lines) |
| "which process?" (Linux) | `ss -tunap | grep <port>` · (Windows) `netstat -ano \| findstr :<port>` |
| "is the interface healthy?" | `ethtool -S <iface> \| grep -iE 'err\|drop\|crc'` (Linux) · `pktmon counters` (Windows) |

If triage points at a specific device/link, escalate to the matching scenario file. If triage points at "the whole path is fine but the app still fails," you need packets — go to `scenarios/connectivity.md` or `tls-https.md`.

---

## Golden Rules (read these; they save careers)

1. **Measure from both ends.** A problem that looks like "server is slow" is often a client-side DNS or MTU issue. Always reproduce from a known-good host too.
2. **Telemetry before packets.** Don't SPAN a port until SNMP/gNMI/`show interface` tells you which port. Packets are expensive and narrow; telemetry is cheap and wide.
3. **Capture on the bridge, not the NIC.** On a Linux bridge sensor, capture on `br0` (sees both directions). Capturing on `eth0` sees only one direction. (Reference: `reference/sensor-builds.md`.)
4. **Disable offloads on sensors.** `ethtool -K br0 gro off tso off lro off gso off` so the sensor sees real frames, not re-segmented blobs. Linux only.
5. **Bypass tap or don't go inline in production.** A sensor crash without fail-open = an outage. Use SPAN where you can't tolerate the SPOF.
6. **`SSLKEYLOGFILE` only for traffic you own.** It decrypts your client's TLS. It cannot decrypt third-party or malware TLS — that's JA4 fingerprinting territory.
7. **One change at a time.** Especially on Cisco gear. Then pyATS-diff to prove what moved.
8. **Capture evidence before you fix.** NetWatch Flight Recorder (`Shift+R`→`Shift+F`), tshark ring buffer, Pktmon ETL. The RCA is worthless without the packet that proved it.
9. **Never bridge inside a LACP bundle.** Bridge *before* the bundle splits, or use a tap that handles bundles — otherwise you lose half the traffic and break the hash.
10. **Know your platform limits.** Windows = great host/SPAN/L3 sensor, **never** a transparent inline bridge. Linux = everything.

---

## Quick Tool Cheat-Sheet

### NetWatch (live packet TUI — Linux/macOS primarily)
```bash
netwatch                 # unprivileged: dashboard, connections, interfaces, processes
sudo netwatch            # full capture; select interface in Interfaces tab (press 3)
# No -i flag! Pin interface via config: capture_interface = "br0" in ~/.config/netwatch/config.toml
SSLKEYLOGFILE=/tmp/k.txt sudo netwatch   # + live TLS 1.3 decrypt (Packets tab)
# Tabs: 1 Dashboard 2 Connections 3 Interfaces 4 Packets 5 Stats 6 Topology
#       7 Timeline 8 Processes 9 Insights 0 Egress
# Shift+R arm Flight Recorder, Shift+F freeze, Shift+E export bundle
```

### RustNet (cross-platform process-attribution TUI — Linux/macOS/Windows/FreeBSD)
```bash
sudo rustnet -i eth0                 # Linux/macOS
rustnet --show-localhost             # include loopback
sudo rustnet --pcap-export cap.pcap  # capture with process-attribute sidecar
# Tabs: 1 Overview 2 Details 3 Interfaces 4 Graph 5 Help
# Filter: port:443 sni:github.com process:chrome state:established /regex/
```
```powershell
# Windows — requires Npcap with WinPcap API-compatible mode
choco install rustnet
rustnet -i "Ethernet"                # run as Administrator
```

### tshark / dumpcap (scriptable capture — all platforms)
```bash
sudo tshark -i eth0 -f "tcp port 443" -w cap.pcapng        # live → file
sudo dumpcap -i eth0 -w cap.pcapng -b filesize:100000 -b files:50   # ring buffer
tshark -r cap.pcapng -Y "tcp.analysis.retransmission"        # post-hoc: retransmits
tshark -r cap.pcapng -o "tls.keylog_file:/tmp/k.txt" -Y "tls"  # decrypt TLS post-hoc
```

### ngrep (regex on live payload)
```bash
sudo ngrep -d eth0 -W byline 'GET|POST' tcp port 80          # HTTP methods
sudo ngrep -d eth0 -i 'error|exception' port 5432            # app error strings
sudo ngrep -d eth0 -X 'cafebabe'                              # hex pattern
sudo ngrep -I cap.pcap 'password'                             # search a pcap
```

### Pktmon (Windows built-in)
```powershell
pktmon list                              # list interfaces
pktmon filter add F1 -t TCP -p 443        # add a filter
pktmon start --capture --comp nics -m real-time     # live to console
pktmon start --capture --comp nics --pkt-size 0 -f C:\cap.etl  # capture to ETL
pktmon stop
pktmon etl2pcap C:\cap.etl -o C:\cap.pcapng                # convert to pcapng
pktmon counters                                            # high-level counters
```

Full references in `reference/tools.md`.

---

## Escalation Flow (how the layers hand off)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER SYMPTOM / SNMP-gNMI alert                           │
│    "app slow to DB"  /  "Gi1/0/24 input errors climbing"    │
└──────────────────────────┬──────────────────────────────────┘
                           │ (triage: mtr, dig, openssl, curl)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. TELEMETRY — narrow the suspect                           │
│    gNMI: which interface/BGP session? pyATS diff: changed?  │
│    CLI show interface / show ip route on the Cisco device   │
└──────────────────────────┬──────────────────────────────────┘
                           │ (need bytes → pick architecture)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. PACKETS — prove the why                                  │
│    SPAN the port → sensor: netwatch/rustnet/tshark          │
│    or inline bridge sensor on the uplink                    │
│    or host-based on the Linux app server                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. EVIDENCE — Flight Recorder / pcap / ETL + audit          │
│    netwatch Shift+F  ·  tshark ring buffer  ·  pktmon etl   │
└─────────────────────────────────────────────────────────────┘
```

This flow is the single most important habit. Telemetry scales and tells you *where*; packets are deep and tell you *why*. Reach for packets only after telemetry (or a clear user symptom) points at a specific suspect.

---

*Every command in this skill has been verified against official docs (Cisco IOS-XE 17.x config guides, Microsoft Pktmon reference, Wireshark/tshark man pages, ngrep 8 man page, NetWatch v0.26.1, RustNet README/ARCHITECTURE). See verification notes at the bottom of each reference file.*
