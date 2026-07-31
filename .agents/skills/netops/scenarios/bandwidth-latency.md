# Scenario — Bandwidth, Latency, Retransmits, QoS

"Slow" is the worst-defined complaint. Pin it down to **throughput**, **RTT**, **jitter**, **loss**, or **retransmits** first — each has a different cause and tool.

---

## Triage (run from the affected host)

```bash
# Bandwidth — iperf3 between two endpoints (install on both)
iperf3 -c server -t 30 -P 4            # 4 parallel streams, 30s — gets link capacity
iperf3 -c server -R                    # reverse direction
iperf3 -c server --udp -b 100M        # UDP test for loss/jitter at a target rate

# Path loss + RTT
mtr -rwzbc 100 --tcp --port 443 target

# Latency/jitter to a target
ping -c 100 -i 0.1 target | tee ping.log   # 10s of pings, then stats

# Interface health (Linux, on the host)
ethtool -S eth0 | grep -iE 'err|drop|crc|fifo'
ethtool eth0 | grep -iE 'speed|duplex'

# Interface health (Windows)
pktmon counters --comp nics
Get-NetAdapterStatistics
```

---

## Symptom → cause map

| Symptom | Likely cause | Confirm with |
|---|---|---|
| iperf3 << link capacity | Congestion, QoS limiting, duplex mismatch | `show interface` duplex; `show policy-map interface` |
| High RTT but low loss | Bufferbloat (bloated queues), long path | bufferbloat test; netwatch Stats handshake-timing histogram |
| High retransmits | Loss (congestion or L1 errors) | `show interface` errors; tshark retransmission filter |
| Jitter on UDP (voice/video) | Queuing variance, congestion | iperf3 `--udp` jitter output; QoS policy |
| Slows at peak times | Link saturation at peak | gNMI throughput stream; `show interface` utilization |
| One direction slow, other fine | Asymmetric routing, half-duplex | `show interface` duplex; mtr forward vs reverse |
| Microbursts (periodic stalls) | Shallow buffers, bursty traffic | netwatch Stats; switch buffer counters |

---

## Playbook: "link is saturated, users slow"

### Step 1 — Telemetry (gNMI streaming interface counters)
```bash
gnmic -a 10.0.0.1:57400 --username admin --insecure subscribe \
  --path "/interfaces/interface[name=Gi1/0/24]/state/counters/in-octets" \
  --path "/interfaces/interface[name=Gi1/0/24]/state/counters/out-octets" \
  --stream-mode sample --sample-interval 1s
# Compute bps: (delta_in_octets * 8) / interval = bits/sec
```
Or CLI:
```
show interface Gi1/0/24
show interfaces Gi1/0/24 stats        ! 5-min input/output rate
show interface Gi1/0/24 history       ! historical rates
```

### Step 2 — Who's using the bandwidth? (sensor on the uplink)
```
monitor session 1 source interface Gi1/0/24 both
monitor session 1 destination interface Gi1/0/48     ! Linux sensor
```
```bash
# On the sensor — per-conversation throughput
sudo netwatch
# Processes tab if host-based; Connections tab for top flows

# Or tshark conversation stats over 60s:
sudo tshark -i eth0 -a duration:60 -q -z conv,ip | sort -k4 -h | tail
# Top talkers:
sudo tshark -i eth0 -a duration:60 -q -z endpoints,ip
```

### Step 3 — QoS / congestion evidence
```
show policy-map interface Gi1/0/24    ! per-class drops — is a class starving?
show class-map
show queueing interface Gi1/0/24
```
If a QoS class is dropping heavily while another is idle → QoS misclassification or mis-sizing. Packets confirm what's in each class:
```bash
sudo tshark -i eth0 -Y "ip" -T fields -e ip.src -e ip.dst -e ip.dsfield.dscp | sort | uniq -c | sort -rn
# See DSCP distribution — are markings correct?
```

### Step 4 — Fix + validate
- If saturated → upgrade link, add capacity, or rebalance ECMP
- If QoS misconfigured → fix the policy, pyATS-diff to validate the change
- If bursty → consider larger buffers or QoS shaping

---

## Playbook: "high latency / bufferbloat"

Symptom: ping latency spikes under load (e.g. 10ms idle → 300ms during a download).

### Diagnose
```bash
# Run an iperf3 download (saturate the path) WHILE pinging
iperf3 -c server -R -t 30 &
ping -c 30 -i 0.2 target | tee bufferbloat.log
# If ping jumps from 10ms → 200ms+ during the download → bufferbloat
```

### Confirm on the sensor (netwatch Stats tab)
The TCP handshake-timing histogram shows RTT inflation under load. On a SPAN sensor:
```bash
sudo netwatch
# Stats tab → watch RTT scale up during saturation
# Or tshark:
sudo tshark -i eth0 -Y "tcp.analysis.ack_rtt" -T fields -e tcp.analysis.ack_rtt | sort -h | tail
```

### Fix
- Enable SQM/QoS fq_codel or cake on the bottleneck router (Linux: `tc qdisc add ... cake`)
- Reduce queue depth on the switch interface
- This is a queue-management problem, not a bandwidth problem

---

## Playbook: "retransmits / packet loss"

### Confirm loss
```bash
mtr -rwzbc 200 --tcp --port 443 target      # shows loss% per hop
# Hop with loss = where packets drop
```

### Find retransmits in a capture
```bash
# On a sensor:
sudo tshark -i eth0 -Y "tcp.analysis.retransmission" -w retransmits.pcap
# Count per flow:
sudo tshark -i eth0 -Y "tcp.analysis.retransmission" -T fields -e ip.src -e ip.dst -e tcp.dstport | sort | uniq -c | sort -rn
# RustNet also surfaces retransmits per-connection (Overview tab, retransmit column)
sudo rustnet -i eth0
# netwatch Stats tab → TCP handshake-timing histogram shows retransmits
```

### Determine cause
| Signal | Cause |
|---|---|
| Loss on one hop only, clean before/after | That hop's device/link — L1 or congestion there |
| Loss starts at first hop, persists | Local NIC/cable/duplex — `ethtool -S` errors |
| Loss proportional to load | Congestion (need more capacity or QoS) |
| Loss only on one TCP flow, not others | Path MTU issue → mtu-path.md |
| Loss + CRC errors on `show interface` | Cabling/duplex/PHY — physical layer |
| Loss + input drops, no errors | Congestion drops (queue full) |

### Physical-layer checks
```
show interface Gi1/0/24 | inc error|CRC|drop|duplex|speed
show controllers ethernet-controller Gi1/0/24   ! low-level phy errors
```
```bash
ethtool -S eth0 | grep -iE 'crc|err|drop|fifo|miss'
ethtool eth0    # confirm Speed + Duplex negotiated correctly (auto-neg mismatch → errors)
```

---

## Playbook: "QoS / marking verification"

Confirm DSCP/802.1p markings survive the path — common cause of "voice is bad."

```bash
# Capture and show DSCP distribution
sudo tshark -i eth0 -Y "ip" -T fields -e ip.dsfield.dscp | sort | uniq -c
# ngrep can't decode DSCP, but it can find by ToS byte:
sudo ngrep -d eth0 -X '0x??' 'ip'    # (tshark is better for this)
```
```
show policy-map interface Gi1/0/24    ! are markings being trusted/remarked?
show mls qos interface Gi1/0/24       ! (on Catalyst) trust state
show class-map
```
If voice packets arrive with DSCP 0 → trust boundary is misconfigured (some switch is remarking to 0).

---

## Playbook: "microbursts / periodic stalls"

Symptom: throughput oscillates, stalls every few seconds, but average counters look fine.

### Diagnose with netwatch (live, sub-second)
```bash
sudo netwatch     # inline bridge sensor — Stats tab shows the bursts at sub-second cadence
```

### Switch buffer counters
```
show platform hardware fed switch active fwd-asic counters rewrite drop all
show platform hardware fed switch active fwd-asic resource drop all
```
If buffer drops spike during bursts → shallow buffers or no QoS to absorb bursts.

### Fix
- Add QoS with shaped queuing to absorb bursts
- Larger buffers (or per-queue buffers)
- This is invisible to 30s SNMP polls — you need streaming (gNMI 1s) or a packet sensor to catch it

---

## Evidence checklist

- [ ] iperf3 results both directions (capacity vs expected)
- [ ] mtr output (per-hop loss + RTT)
- [ ] `show interface` + `show policy-map interface` from the bottleneck device
- [ ] tshark/netwatch conversation stats during the problem (top talkers)
- [ ] DSCP distribution capture (if QoS relevant)
- [ ] gNMI throughput stream (if streaming set up)
