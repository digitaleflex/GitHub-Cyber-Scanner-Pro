# Scenario — Security / IDS / Threat Detection

Detecting malicious traffic: C2 beaconing, port scans, DNS tunneling, exfiltration, and capturing forensic evidence. Two tiers: **netwatch's built-in threat detection** (single host/sensor) and **Suricata IDS** (fleet, signature-based).

---

## What to look for (the signals)

| Signal | Threat | Tool |
|---|---|---|
| Regular, low-jitter check-ins to one IP | **C2 beaconing** | netwatch Timeline + threat detection; Suricata |
| Sequential SYN to many ports/hosts | **Port scan** | netwatch; Suricata `sf_portscan` |
| Long DNS query labels, high query rate, TXT queries | **DNS tunneling / exfiltration** | tshark filters; Suricata |
| New JA4 fingerprint talking to your hosts | **Unknown/unauthorized software or malware** | netwatch JA4 (Packets tab) |
| Sudden spike in outbound bytes | **Data exfiltration** | ntopng / NetFlow; netwatch Processes |
| TLS to non-standard ports / self-signed | **Possible C2** | netwatch Packets + JA4 |
| Connections to known-bad IPs/domains | **Botnet/malware** | Suricata with threat intel feeds |

---

## Tier 1 — netwatch built-in threat detection (single sensor, zero config)

NetWatch runs background detection for C2 beaconing, port scans, and DNS tunneling with **zero setup**. A critical alert auto-freezes the Flight Recorder.

### Run on a sensor
```bash
sudo netwatch          # inline bridge or SPAN-destination sensor
# Timeline tab (7) → security alerts land here, color-coded
# A critical alert auto-freezes the recorder → Shift+F to export the bundle
```

### JA4 fingerprint hunting (identify clients even when encrypted)
```
# In the netwatch Packets tab, filter for JA4 fingerprints
# A JA4 hash like t13d1516h2_8daaf6152771_b186095e22b6 uniquely identifies a client software
# Pivot on a fingerprint to find every flow from the same software
# An unknown JA4 talking to your servers = investigate
```
> JA4 is the TLS/QUIC analog of a user-agent — recognize a specific browser, tool, or malware by its handshake, **even though the traffic is encrypted**.

---

## Tier 2 — Suricata IDS (fleet, signature-based, production-grade)

Suricata has a **native Windows build** and runs on Linux. It's the standard open-source IDS — what SecOps teams actually run. Outputs structured JSON (EVE) to a SIEM.

### Install (Linux)
```bash
# Ubuntu/Debian
sudo add-apt-repository ppa:oisf/suricata-stable
sudo apt update && sudo apt install suricata
# RHEL/Fedora
sudo dnf install suricata
```

### Install (Windows)
- Download from the Suricata releases page (native MSI builds exist)
- Or via `winget install suricata` if packaged
- Requires Npcap for capture

### Run inline or on a SPAN
```bash
# On a sensor (SPAN destination or inline bridge)
sudo suricata -i br0 -c /etc/suricata/suricata.yaml --runmode workers
# EVE JSON logs to /var/log/suricata/eve.json
```

### Rules (signatures)
```bash
# Update rules with suricata-update
sudo suricata-update                          # pulls Emerging Threats Open rules
sudo systemctl reload suricata
# Custom rule — alert on a known-bad IP:
echo 'alert ip $HOME_NET any -> [10.20.30.40,10.20.30.41] any (msg:"traffic to known C2"; sid:1000001; rev:1;)' \
  | sudo tee /etc/suricata/rules/local.rules
sudo systemctl reload suricata
```

### Ingest EVE to a SIEM
EVE JSON is line-delimited, perfect for ELK/Wazum/Splunk:
```bash
# Sample an alert
tail -f /var/log/suricata/eve.json | jq 'select(.event_type=="alert")'
# Common fields: .alert.signature, .src_ip, .dest_ip, .dest_port, .proto
```

### Useful rule categories (from Emerging Threats)
- C2 beaconing detection
- Port scan detection (Suricata's `stream` engine)
- DNS tunneling signatures
- Known-malware JA3/JA4 hashes
- Threat-intel feeds (abuse.ch, etc.)

---

## Playbook: "suspected C2 beaconing"

### With netwatch (live, single sensor)
```bash
sudo netwatch
# Timeline tab → look for "beaconing" alerts
# Connections tab → filter for the suspect IP → check regularity of connections
# Packets tab → JA4 of the suspect flow → google/pivot on the hash
# Shift+R to arm Flight Recorder, reproduce, Shift+F to freeze → evidence bundle
```

### With tshark (confirming regularity)
```bash
# Capture and look at connection timestamps to one IP
sudo tshark -i eth0 -Y "ip.addr==10.20.30.40 && tcp.flags.syn==1 && tcp.flags.ack==0" \
  -T fields -e frame.time | sort
# Regular intervals (e.g. every 60s ± 1s) = beaconing
# Also: check jitter — low jitter is the C2 signature (high jitter = human/browsing)
```

### With Suricata (fleet)
```bash
# ET rules flag beaconing patterns; check EVE:
tail -f /var/log/suricata/eve.json | jq 'select(.event_type=="alert") | select(.alert.category | test("C2|Trojan|Beacon"; "i"))'
```

---

## Playbook: "port scan detection"

### netwatch
```bash
sudo netwatch
# Timeline tab → "port scan" alerts auto-appear
```

### tshark (manual)
```bash
# SYN without ACK to many ports on one host = scan
sudo tshark -i eth0 -Y "tcp.flags.syn==1 && tcp.flags.ack==0" \
  -T fields -e ip.src -e tcp.dstport | sort -u | uniq -c | sort -rn | head
# One src hitting many dst ports = scan
```

### Suricata
Suricata's `stream` engine detects scans; EVE has `event_type: alert` with `scan` signatures.

---

## Playbook: "DNS tunneling / exfiltration"

### Detect (see dns.md too)
```bash
# Long DNS query labels (data encoded in subdomain)
sudo tshark -i eth0 -Y "dns.flags.response == 0" -T fields -e dns.qry.name \
  | awk '{print length($0), $0}' | sort -n | tail
# High query rate from one host
sudo tshark -i eth0 -Y "dns.flags.response == 0" -T fields -e ip.src | sort | uniq -c | sort -rn | head
# TXT queries (common tunneling channel)
sudo tshark -i eth0 -Y "dns.qry.type == 16"
# ngrep for long DNS names
sudo ngrep -d eth0 -W byline '.{40,}' 'udp port 53'
```

### Confirm exfiltration volume
```bash
# Total DNS bytes from a host — abnormally high = exfil
sudo tshark -i eth0 -Y "dns && ip.src==10.0.0.5" -T fields -e frame.len | awk '{s+=$1} END {print s}'
```

---

## Playbook: "capture forensic evidence (Flight Recorder / pcap)"

When you catch the threat in the act, freeze the evidence.

### netwatch Flight Recorder
```
Shift+R          # arm the rolling recorder (before reproducing)
# (reproduce the incident)
Shift+F          # freeze → bundle (packets + connections + DNS + health + alerts)
Shift+E          # export the bundle to disk
```

### tshark ring buffer (pre-incident, 24/7)
```bash
sudo dumpcap -i eth0 -w /data/cap.pcapng -b filesize:100000 -b files:50
# Last 5 GB always available; stop and copy the relevant files when investigating
```

### Windows Pktmon (headless capture)
```powershell
pktmon start --capture --comp nics --pkt-size 0 -f C:\caps\cap.etl
# (incident happens)
pktmon stop
pktmon etl2pcap C:\caps\cap.etl -o C:\caps\cap.pcapng
# Attach cap.pcapng to the incident ticket
```

### Chain of custody
- Don't modify the original pcap — copy it and work on the copy
- Record the capture time window, sensor interface, and SPAN source
- Hash the evidence: `sha256sum cap.pcapng > cap.pcapng.sha256`
- netwatch's bundle + ESSH audit log + the pcap = full evidentiary picture

---

## Playbook: "unknown software talking to my servers (JA4)"

```bash
sudo netwatch
# Packets tab → see JA4 fingerprints of clients hitting your servers
# An unfamiliar JA4 hash → pivot to find every flow with that fingerprint
# Google the hash (JA4 databases exist) or compare to known-malware JA4 lists
# If it's malware → quarantine the host, escalate to incident response
```

---

## Quick detection-rule cheatsheet

| Threat | tshark filter | netwatch tab | Suricata rule |
|---|---|---|---|
| C2 beaconing | regular SYN to one IP (manual) | Timeline alert | ET C2 rules |
| Port scan | `tcp.flags.syn==1 && tcp.flags.ack==0` to many ports | Timeline alert | stream engine |
| DNS tunneling | long `dns.qry.name`, high rate, TXT | (manual tshark) | ET DNS rules |
| Exfiltration | high outbound bytes to one dest | Processes tab | (manual) |
| Unknown client | unfamiliar JA4 | Packets JA4 | JA3/JA4 hash rules |
| Bad IP | traffic to threat-intel IP | Connections filter | threat-intel feed |

---

## Evidence checklist

- [ ] Alert timestamp + which tool flagged it (netwatch Timeline / Suricata EVE)
- [ ] Flight Recorder bundle OR pcap covering the event
- [ ] JA4 fingerprint of the suspect flow (if TLS)
- [ ] Beaconing regularity proof (sorted timestamps, low jitter)
- [ ] Source/dest IP + port + process (RustNet `--pcap-export` for process attribution)
- [ ] sha256 of the evidence file
- [ ] ESSH audit log of what you did during the investigation
