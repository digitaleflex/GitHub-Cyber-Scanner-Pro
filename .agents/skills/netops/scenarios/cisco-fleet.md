# Scenario — Cisco Fleet (BGP/OSPF, interface errors, VLAN/VRF, NX-OS)

Native-Cisco troubleshooting using telemetry + CLI + pyATS, escalating to packet sensors when needed. Combines the `ciscoxr`/`c8000-iosxe`/`catalyst8000`/`pyats` skills you already have.

---

## Triage (run on the Cisco device first)

```
show interface Gi1/0/24
show interface Gi1/0/24 detail
show interface counters errors
show ip interface brief
show ip route
show ip protocols
show ip ospf neighbor
show ip bgp summary
show spanning-tree
show vrf
show environment all
show processes cpu sorted
show memory statistics
show log
```

---

## Playbook: "BGP session flapping"

### Step 1 — Telemetry
```
show ip bgp summary                       ! State column: Idle / Active / OpenSent / Established
show ip bgp neighbors 10.0.0.2            ! detailed: last error, hold time, keepalive
show ip bgp neighbors 10.0.0.2 advertised-routes
show ip bgp neighbors 10.0.0.2 received-routes
show ip bgp ipv4 unicast summary
```

### Step 2 — Common causes
| State/finding | Cause | Next |
|---|---|---|
| `Idle` | No TCP connectivity to neighbor | `ping`/`traceroute` to neighbor; check ACL |
| `Active` (stuck) | TCP SYN not answered or RST | Capture on the link — do SYNs arrive? RSTs? |
| `OpenSent`→`Active` flip | OPEN message rejected (wrong AS / hold-time) | Check `remote-as`; capture the OPEN |
| Flaps between Established↔Idle | TCP resets, MTU black-hole, or hold-time expiry | Capture; check MTU (mtu-path.md) |
| `Notification` errors | `show bgp` last error message | Decode the BGP Notification code |

### Step 3 — Capture (if telemetry unclear)
SPAN the interface toward the neighbor:
```
monitor session 1 source interface Gi0/0 both
monitor session 1 destination interface Gi1/0/48   ! Linux sensor
```
```bash
# On the sensor — BGP on TCP 179
sudo tshark -i eth0 -Y "tcp.port == 179" -w bgp.pcap
# Decode BGP:
tshark -r bgp.pcap -Y "bgp" -V | grep -iE 'BGP|OPEN|UPDATE|NOTIFICATION|Type'
# Look for: SYN with no SYN-ACK (connectivity), RST (reset), NOTIFICATION (protocol error)
```
```bash
# With ngrep for readable BGP OPEN messages:
sudo ngrep -d eth0 -W byline -X 'ffffffffffffffffffffffffffffffff002d0104' 'tcp port 179'
# (the hex is a BGP OPEN marker — tshark is more reliable for BGP)
```

### Step 4 — MTU check (very common BGP killer)
BGP OPEN + UPDATE messages can exceed path MTU → if PMTUD broken, large UPDATEs drop and the session resets.
```bash
tracepath -n <neighbor-ip>
ping -c 3 -M do -s 1472 <neighbor-ip>
```
Fix: set MSS clamp or fix ICMP filtering (mtu-path.md).

---

## Playbook: "OSPF adjacency stuck"

```
show ip ospf neighbor                    ! state: INIT / EXSTART / EXCHANGE / FULL
show ip ospf neighbor detail
show ip ospf interface Gi0/0
```

| State stuck at | Likely cause | Fix |
|---|---|---|
| `INIT` (no reply) | Hello mismatch (area, auth, subnet, hello/dead timers, stub flag) | Compare `show ip ospf interface` both sides |
| `EXSTART` | **MTU mismatch** (DBD packets too big) | Check `show ip ospf interface MTU` both sides; align or set `ip ospf mtu-ignore` |
| `EXCHANGE` | DBD content mismatch / LSDB corruption | Capture OSPF; check DBD packets |
| `LOADING` | LSR/LSU failing | Retransmissions — check connectivity |

### Capture OSPF
```bash
sudo tshark -i eth0 -Y "ospf" -w ospf.pcap
tshark -r ospf.pcap -V | grep -iE 'Hello|DBD|LSR|LSU|LSAck|Area|MTU|Auth'
# Hello mismatch: compare hello-interval, dead-interval, area ID, auth type both sides
```

---

## Playbook: "interface errors / CRC / drops"

```
show interface Gi1/0/24 | inc error|CRC|drop|runts|giants|input|output
show interface Gi1/0/24 detail
show controllers ethernet-controller Gi1/0/24   ! low-level phy
show platform hardware fed switch active fwd-asic counters rewrite drop all
```

| Counter | Meaning | Likely cause |
|---|---|---|
| `CRC` / `input errors` | Frame corrupted | Cabling, duplex mismatch, bad SFP/optics, EMI |
| `runts` | Undersized frames | Duplex mismatch |
| `giants` | Oversized frames | MTU mismatch with jumbo |
| `input drops` (no errors) | Queue congestion / CPU punt | Congestion, QoS, control-plane policing |
| `output drops` | Egress queue full | Congestion, QoS shaping |
| `late collisions` | Duplex mismatch (half/full) | Force full-duplex both ends |
| `alignment errors` | Physical/cable | Cabling, NIC, port |

### Duplex check
```
show interface Gi1/0/24 | inc Duplex|Speed
! Mismatch (one side full, other half) → force full-duplex + matching speed both ends
```
```bash
ethtool eth0 | grep -iE 'speed|duplex'      # Linux host side
```

### Capture for confirmation
SPAN the port and look for runts/jabbers in the capture:
```bash
sudo tshark -i eth0 -Y "frame.too_short || frame.too_long" -w errors.pcap
sudo tshark -i eth0 -T fields -e frame.len | sort -n | head    # runts at the low end
```

---

## Playbook: "STP / VLAN / VRF issues"

### STP
```
show spanning-tree                       ! root bridge, port states (Fwd/Blk/Altn/Dscr)
show spanning-tree vlan 10 detail
show spanning-tree interface Gi1/0/24 detail
show spanning-tree summary
```
| Finding | Cause |
|---|---|
| Port in `Blk` unexpectedly | STP blocking due to topology (normal) or priority misconfiguration |
| Frequent topology changes | Flapping link, duplex mismatch, unidirectional link |
| Root bridge wrong | Priority/MAC — set root with `spanning-tree vlan X root primary` |

### VLAN
```
show vlan brief                           ! VLAN exists, ports assigned
show interfaces trunk                     ! trunk allowed-VLANs
show interfaces switchport                 ! access/trunk, native VLAN
```
| Finding | Cause |
|---|---|
| Host can't reach same-VLAN peer | Wrong access VLAN assignment, native VLAN mismatch on trunk, VLAN not allowed on trunk |
| Trunk not passing some VLANs | `switchport trunk allowed vlan` excludes it |

### VRF
```
show vrf                                  ! list
show ip route vrf MGMT                    ! route in a specific VRF
show ip interface brief | inc VRF
ping vrf MGMT <target>
```
Common issue: traffic goes into the wrong VRF (management plane leaking into data VRF). Check `rd`/`route-target` import/export.

---

## Playbook: "change validation with pyATS" (you have the skill)

Before any change: snapshot. After: snapshot. Diff. See `cisco/telemetry.md`.

```python
from genie.testbed import load
import json
tb = load('testbed.yaml')
state = {}
for name, dev in tb.devices.items():
    dev.connect()
    state[name] = {
        'interfaces': dev.parse('show interfaces'),
        'route': dev.parse('show ip route'),
        'bgp': dev.parse('show ip bgp summary'),
        'ospf': dev.parse('show ip ospf neighbor'),
    }
json.dump(state, open('before.json','w'), indent=2, default=str)
# ... make your change ...
# re-parse into after.json, then genie.diff(before.json, after.json)
```
A clean diff (only expected changes) = the change did what you intended. Unexpected deltas = investigate immediately.

---

## Playbook: "high CPU on a Cisco device"

```
show processes cpu sorted                 ! top CPU consumers
show processes cpu history                 ! 60s/60m/72h graphs
show platform                              ! hardware
```
| Finding | Cause | Next |
|---|---|---|
| `IP Input` high | Process-switched traffic (should be CEF) | Check `show ip cef`; check for punt traffic |
| `SSH`/`HTTP` high | Management-plane attack | ACL on mgmt VTY; capture to see source |
| `BGP`/`OSPF` high | Convergence churn | Check adjacency stability |
| Spikes correlated with alerts | Malicious traffic to CPU | SPAN the control plane / CPU queue |

### Capture control-plane traffic
```
monitor session 1 source cpu queue all    ! (some platforms support CPU as SPAN source)
```
or SPAN the uplink and filter for traffic destined to the device's own IP.

---

## NX-OS specifics

```
show running-config | inc feature
show vlan
show vpc                                   ! vPC state
show interface
show hardware
show processes cpu
show routing
show bgp ipv4 unicast summary
```
NX-OS ERSPAN syntax differs slightly — see `cisco/span-erspan.md` for the NX-OS variant.

---

## Escalation to packet sensors (when telemetry isn't enough)

| Telemetry shows… | Escalate to… |
|---|---|
| BGP flaps, no error counters on interface | SPAN the BGP link → capture TCP 179 (mtu-path.md likely) |
| OSPF stuck EXSTART | SPAN → capture OSPF DBD (MTU mismatch) |
| Interface errors rising | SPAN the port → look for runts/CRC; fix cabling/duplex |
| Control-plane CPU high | SPAN CPU queue or uplink → find the offending traffic |
| New SNI/IP the device talks to | SPAN → netwatch JA4 + threat detection |

Telemetry narrows to the suspect in seconds; the sensor proves the why in minutes.

---

## Evidence checklist

- [ ] `show` command outputs from each suspect device
- [ ] gNMI/SNMP trend graphs during the incident window
- [ ] pcap/Flight Recorder from the SPAN sensor
- [ ] pyATS before/after diff (prove only intended changes occurred)
- [ ] ESSH audit log (every command you ran, with timestamps)
