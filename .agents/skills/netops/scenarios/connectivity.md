# Scenario — Connectivity ("can't reach X", intermittent, hangs)

The most common network complaint. Work the 30-second triage in SKILL.md first, then this.

---

## Triage ladder (run from the affected host)

```bash
# 1. Name resolution
dig +trace example.com
getent hosts example.com          # what the host actually resolves to (split-horizon check)
# 2. ICMP path
mtr -rwzbc 100 example.com        # per-hop loss% + RTT (10s)
# 3. TCP path (ICMP blocked? use TCP/443)
mtr -rwzbc 100 --tcp --port 443 example.com
# 4. Does the TCP handshake complete?
nc -vz -w 5 example.com 443      # or: bash -c "timeout 5 bash -c '</dev/tcp/example.com/443' && echo OPEN || echo CLOSED"
# 5. App-level
curl -v --max-time 10 https://example.com/   # read the `*` lines
openssl s_client -connect example.com:443 -servername example.com -showcerts </dev/null
```

Windows equivalent:
```powershell
Resolve-DnsName example.com
Test-NetConnection example.com -Port 443
tracert example.com
curl.exe -v --max-time 10 https://example.com/
```

---

## Symptom → cause map

| Symptom | Likely cause | Confirm with |
|---|---|---|
| `mtr` shows 100% loss at hop N | Routing black hole or ACL at hop N | `traceroute -T -p 443` to that hop; check ACL on the device |
| `nc` shows "Connection refused" | Port closed / firewall RST | Check service running? `ss -tlnp \| grep :443` on server |
| `nc` times out (no response) | Silent drop (firewall DROP or host down) | SPAN the server's port — see if SYN arrives |
| SYN_SENT hangs | Server not ACKing SYN, or SYN dropped on path | netwatch on server: do SYNs arrive? Is SYN-ACK leaving? |
| CLOSE_WAIT accumulating | App not closing sockets (app bug, not network) | `ss -tan state close-wait` on server; check app code |
| Intermittent, time-of-day | Congestion peaks, link saturation | bandwidth-latency.md |
| Only one host affected | Host-specific: ARP, local firewall, MAC flap | `show mac address-table address <mac>` on switch |
| Whole subnet affected | Gateway/STP/VLAN issue | `show spanning-tree`, `show vrf`, check gateway |
| Works from A but not B | Path difference — ACL, route, MTU | Compare `mtr` from A and B; check MTU (mtu-path.md) |

---

## Playbook: "app server can't reach DB, intermittent"

### Step 1 — Triage from the app server (Linux)
```bash
mtr -rwzbc 100 db.internal
nc -vz -w 5 db.internal 5432
# During a failure window:
ss -tan | grep db.internal   # see SYN_SENT? CLOSE_WAIT? ESTABLISHED-but-stuck?
```

### Step 2 — Telemetry on the Cisco path (escalation #1)
```bash
essh connect admin@core-sw-01    # or gyshell / netcatty
```
```
show interface Gi1/0/10          ! app-tier uplink — errors? drops?
show ip route 10.20.30.5         ! route to DB
show mac address-table address <db-mac>   ! which port is the DB on?
show interface counters errors | inc Gi1/0/10
```

### Step 3 — Packets on the suspect link (escalation #2)
Choose architecture by what you can change:

**Option A: SPAN the DB uplink to a Linux sensor**
```
! On the DB-tier switch
monitor session 1 source interface Gi1/0/10 both
monitor session 1 destination interface Gi1/0/48   ! Linux sensor here
```
```bash
# On the Linux sensor
sudo netwatch
# Connections tab → filter for the app server's IP
# Packets tab → see SYNs arrive? SYN-ACKs leave? retransmits?
```

**Option B: Host-based on the app server** (if it's Linux)
```bash
sudo rustnet                    # which process owns the stuck connection?
sudo netwatch            # full packet view of this host's traffic
```

**Option C: ERSPAN from a remote switch to a central sensor**
```
monitor session 1 type erspan-source
 source interface Gi1/0/10 both
 destination
  erspan-id 100
  ip address 10.20.30.40         ! central Linux sensor
  origin ip address 10.0.0.11
  mtu 1464
 exit
```
```bash
# On the central sensor
sudo tshark -i eth0 -w erspan.pcap
editcap --extract-gre erspan.pcap inner.pcap
tshark -r inner.pcap -Y "tcp.port==5432 && tcp.analysis.retransmission"
```

### Step 4 — Prove the why
On the sensor during a failure window:
- **netwatch Connections tab:** see SYN_SENT with no SYN-ACK → server-side drop
- **netwatch Stats tab:** TCP handshake-timing histogram → retransmits spiking
- **tshark:** `tshark -r cap.pcap -Y "tcp.flags.syn==1 && tcp.flags.ack==0"` to count SYNs vs `tcp.flags.syn==1 && tcp.flags.ack==1` for SYN-ACKs — if SYNs >> SYN-ACKs, server is dropping them
- **netwatch Flight Recorder:** `Shift+R` (arm) before reproducing, `Shift+F` (freeze) → portable bundle for RCA

### Step 5 — Evidence + close
```bash
essh audit tail --lines 100       # what you ran on the switches
# Attach the Flight Recorder bundle to the ticket
# pyATS diff to prove nothing else changed:
python3 diff_state.py before.json after.json
```

---

## Playbook: "CLOSE_WAIT / TIME_WAIT storm (app bug, network symptom)"

**Often misdiagnosed as a network problem.** CLOSE_WAIT means the *remote* sent FIN and the *local app* never closed the socket — that's an app bug, not a network issue. Network tools confirm it's the app.

```bash
# On the app server (Linux)
ss -tan state close-wait | wc -l          # count
ss -tanp state close-wait | head          # which process/PID?
sudo rustnet                                # Connections tab, filter state:close-wait, see process grouping
# On the server's uplink sensor (SPAN): do FINs arrive from the DB?
sudo tshark -i eth0 -Y "tcp.flags.fin==1 && ip.src==<db-ip>" -T fields -e frame.time
# If FINs arrive but sockets linger in CLOSE_WAIT → APP bug. Fix the app's socket handling.
```

---

## Playbook: "MAC flapping / ARP spoofing"

Symptom: intermittent reachability to one host; switch logs show `%MAC_MOVE-Notification`.

```
show mac address-table address aaaa.bbbb.cccc   ! which ports is this MAC on?
show mac address-table | inc aaaa.bbbb.cccc     ! count of entries
show logging | inc MAC_MOVE
```
```bash
# SPAN the suspect ports and watch ARP
sudo ngrep -d eth0 -X '000108000604' 'arp'        # ARP request pattern
sudo tshark -i eth0 -Y "arp.opcode == 1" -T fields -e eth.src -e arp.src.proto_ipv4
# Two sources replying for the same IP = spoofing; enable DHCP snooping + Dynamic ARP Inspection on the switch
```

---

## Playbook: "routing black hole / asymmetry"

Symptom: works one direction, fails the other; or `mtr` shows loss starting at hop N.

```bash
mtr -rwzbc 100 --tcp --port 443 target                # forward path
# Reverse path: from the target back to you
# (SSH to the target, run mtr back to your IP — compare)
```
```
show ip route <your-ip>          ! on each hop's device
show ip cef <your-ip> detail      ! load-share / next-hop
show ip access-lists              ! ACLs silently dropping
```
SPAN the suspect hop's interface and check whether packets arrive but don't leave → black hole confirmed.

---

## Playbook: "DNS-related connectivity" (short version — see dns.md)

```bash
dig +trace example.com @8.8.8.8       # does it resolve via a public resolver?
dig example.com @10.0.0.1             # via the internal resolver — compare
getent hosts example.com              # what the app actually sees (NSS, /etc/hosts, split-horizon)
```
If DNS works but the host can't reach the resolved IP → it's not DNS, it's routing. See above.

---

## Evidence checklist

- [ ] `mtr` output from affected host during the failure (forward and reverse)
- [ ] `show interface` + `show ip route` from each suspect Cisco hop
- [ ] pcap or Flight Recorder bundle from the SPAN/sensor during the failure
- [ ] pyATS before/after diff (prove nothing else changed)
- [ ] ESSH audit log (who did what, when)
- [ ] Root cause statement: "X because Y, proven by Z (the packet/filter output)"
