#!/usr/bin/env bash
# symptom-router.sh — interactive decision engine: symptom → best tool + architecture
# The NetOps decision framework as a script. Pick a symptom, get a recommended playbook.
set -euo pipefail

cat <<'BANNER'
╔══════════════════════════════════════════════════════════════════╗
║  NetOps Symptom Router — CCIE/RHCE-level recommendation engine   ║
╚══════════════════════════════════════════════════════════════════╝
Pick the symptom that best matches the problem. Each option prints the
recommended tool, architecture, and the scenario file to follow.
BANNER

PS3="Symptom number → "
options=(
  "1. Can't reach X (connectivity, intermittent, hangs)"
  "2. Slow / high latency / jitter / retransmits"
  "3. MTU / large transfers stall / VPN drops big packets"
  "4. DNS fails / slow / wrong answer"
  "5. TLS/HTTPS handshake fails / cert / SNI / QUIC"
  "6. Suspected malware / C2 / port scan / DNS tunneling"
  "7. BGP/OSPF flap, interface errors, VLAN/VRF (Cisco fleet)"
  "8. Which process owns this connection? (host-based)"
  "9. I need to plan a sensor fleet (architect)"
  "10. Capture 24/7 to disk (headless ring buffer)"
  "11. Verify a network change (pyATS diff)"
  "12. ERSPAN from a Cisco device to a remote sensor"
)

recommend() {
  cat <<EOF

────────────────────────────────────────────────────────
$1
────────────────────────────────────────────────────────
EOF
}

select opt in "${options[@]}" "Quit"; do
case "$opt" in
  "1. Can't reach X (connectivity, intermittent, hangs)")
  recommend "CONNECTIVITY — start with triage, escalate to packets"
cat <<'EOF'
TRIAGE (from affected host):
  mtr -rwzbc 100 <X>                          # per-hop loss + RTT
  mtr -rwzbc 100 --tcp --port 443 <X>         # if ICMP blocked
  nc -vz -w 5 <X> 443                          # TCP handshake?
  curl -v --max-time 10 https://<X>/           # app-level

TELEMETRY (Cisco path — narrow the suspect):
  show interface Gi1/0/10
  show ip route <X>
  show mac address-table address <mac>
  show interface counters errors

PACKETS (escalate — pick architecture):
  Host-based (Linux app server):  sudo netwatch ; sudo rustnet
  SPAN the suspect port:          monitor session 1 source Gi1/0/10 both
                                  monitor session 1 destination Gi1/0/48
  ERSPAN across L3:               monitor session 1 type erspan-source ...
  See: scenarios/connectivity.md
EOF
;;
  "2. Slow / high latency / jitter / retransmits")
  recommend "BANDWIDTH/LATENCY — measure throughput + loss + QoS"
cat <<'EOF'
MEASURE (between two endpoints):
  iperf3 -c <server> -t 30 -P 4               # link capacity (4 streams)
  iperf3 -c <server> -R                        # reverse direction
  iperf3 -c <server> --udp -b 100M             # UDP loss/jitter at target rate
  mtr -rwzbc 200 --tcp --port 443 <X>          # per-hop loss

WHO'S USING IT (sensor on the uplink):
  sudo netwatch                         # Processes/Connections tabs
  tshark -i eth0 -a duration:60 -q -z conv,ip  # top conversations
  tshark -i eth0 -a duration:60 -q -z endpoints,ip   # top talkers

PHYSICAL / QoS:
  show interface Gi1/0/24 | inc error|CRC|duplex|speed
  show policy-map interface Gi1/0/24           # QoS class drops
  ethtool -S eth0 | grep -iE 'crc|err|drop'   # Linux host side
  See: scenarios/bandwidth-latency.md
EOF
;;
  "3. MTU / large transfers stall / VPN drops big packets")
  recommend "MTU / PMTUD — binary search the working size, fix ICMP filtering"
cat <<'EOF'
DIAGNOSE:
  tracepath -n <X>                             # shows "pmtu N" + bottleneck hop
  ping -c 3 -M do -s 1472 <X>                  # 1500 total — fails?
  ping -c 3 -M do -s 1452 <X>                  # 1480 (GRE) — works?
  ping -c 3 -M do -s 1372 <X>                  # 1400 (IPsec) — works?

CONFIRM ICMP FRAG-NEEDED IS RETURNING (or filtered):
  sudo tshark -i eth0 -Y "icmp.type == 3 && icmp.code == 4"
  (absent = ICMP filtered = PMTUD black hole)

FIX:
  Allow ICMP Type 3 Code 4 on firewalls:  permit icmp any any packet-too-big
  MSS clamp on tunnel:                   interface Tunnel0 ;  ip tcp adjust-mss 1360
  Set tunnel MTU:                        interface Tunnel0 ;  ip mtu 1400
  See: scenarios/mtu-path.md
EOF
;;
  "4. DNS fails / slow / wrong answer")
  recommend "DNS — check resolution path and resolver health"
cat <<'EOF'
DIAGNOSE:
  getent hosts <name>                          # what the app sees (NSS order)
  dig +trace <name>                            # iterative resolution
  dig <name> @8.8.8.8  vs  dig <name> @10.0.0.1   # public vs internal
  dig <name> +time=2 +tries=1                  # timeout if resolver down

CAPTURE (host-based):
  sudo tshark -i any -Y "dns" -T fields -e frame.time -e dns.qry.name -e dns.time
  sudo ngrep -d eth0 -W byline -i '<name>' 'udp port 53'

SECURITY (DNS tunneling — long labels, high rate, TXT):
  sudo tshark -i eth0 -Y "dns.flags.response == 0" -T fields -e dns.qry.name | awk '{print length}' | sort -n | tail
  See: scenarios/dns.md
EOF
;;
  "5. TLS/HTTPS handshake fails / cert / SNI / QUIC")
  recommend "TLS — see the alert, decrypt if you control the client"
cat <<'EOF'
DIAGNOSE:
  openssl s_client -connect <X>:443 -servername <X> </dev/null 2>&1 | grep -iE 'alert|verify|cipher'
  curl -v --max-time 10 https://<X>/           # the `*` lines
  curl --http1.1 https://<X>/                  # HTTP/2 failing? fallback test

CAPTURE THE HANDSHAKE:
  sudo tshark -i any -Y "tls.handshake.type==1 || tls.handshake.type==2 || tls.alert_message" -w tls.pcap
  tshark -r tls.pcap -Y "tls.alert_message" -V | grep -i alert

DECRYPT (only traffic YOU control):
  SSLKEYLOGFILE=/tmp/k.txt curl https://<X>/ &  # set on the client
  SSLKEYLOGFILE=/tmp/k.txt sudo netwatch # Packets tab → filter decrypted:true
  sudo tshark -i eth0 -o "tls.keylog_file:/tmp/k.txt" -Y "http"

QUIC (UDP 443):
  sudo tshark -i any -Y "quic"                  # QUIC failing? UDP 443 blocked?
  See: scenarios/tls-https.md
EOF
;;
  "6. Suspected malware / C2 / port scan / DNS tunneling")
  recommend "SECURITY — netwatch threat detection + Suricata + evidence"
cat <<'EOF'
LIVE (netwatch built-in detection, zero config):
  sudo netwatch
  # Timeline tab (7) → C2 beaconing / port scan / DNS tunneling alerts
  # Shift+R arm Flight Recorder → reproduce → Shift+F freeze → Shift+E export

JA4 FINGERPRINT (identify unknown clients even when encrypted):
  # netwatch Packets tab → JA4 hash per TLS flow → pivot to find same software

IDS (fleet, signature-based):
  sudo suricata -i br0 -c /etc/suricata/suricata.yaml --runmode workers
  tail -f /var/log/suricata/eve.json | jq 'select(.event_type=="alert")'

BEACONING REGULARITY (manual):
  sudo tshark -i eth0 -Y "ip.addr==<bad> && tcp.flags.syn==1 && tcp.flags.ack==0" -T fields -e frame.time | sort
  See: scenarios/security-ids.md
EOF
;;
  "7. BGP/OSPF flap, interface errors, VLAN/VRF (Cisco fleet)")
  recommend "CISCO FLEET — telemetry + CLI, escalate to SPAN for packets"
cat <<'EOF'
TELEMETRY FIRST:
  show ip bgp summary / show ip bgp neighbors <n>
  show ip ospf neighbor / show ip ospf interface
  show interface Gi1/0/24 | inc error|CRC|duplex
  show spanning-tree / show vrf / show ip route <X>

BGP FLAP ESCALATE TO PACKETS (often MTU):
  monitor session 1 source interface Gi0/0 both
  monitor session 1 destination interface Gi1/0/48
  sudo tshark -i eth0 -Y "tcp.port == 179" -w bgp.pcap
  tracepath -n <neighbor>      # check PMTU

OSPF STUCK EXSTART = MTU MISMATCH (very common):
  show ip ospf interface <iface>    # MTU both sides
  See: scenarios/cisco-fleet.md + cisco/telemetry.md
EOF
;;
  "8. Which process owns this connection? (host-based)")
  recommend "PROCESS ATTRIBUTION — RustNet (cross-platform) or ss/netstat"
cat <<'EOF'
LINUX:
  sudo rustnet                                 # process-attributed TUI, filter process:<name>
  ss -tunap | grep <port>                      # socket → PID

WINDOWS:
  rustnet -i "Ethernet"                        # Admin; native process APIs
  netstat -ano | findstr :<port>                # PID → tasklist /fi "PID eq <pid>"

FORENSIC PCAP WITH PROCESS ATTRIBUTION (RustNet):
  sudo rustnet --pcap-export cap.pcap
  python3 scripts/pcap_enrich.py cap.pcap cap_enriched.pcap
  # Open cap_enriched.pcap in Wireshark — each packet annotated with owning process
EOF
;;
  "9. I need to plan a sensor fleet (architect)")
  recommend "ARCHITECTURE — telemetry wide, packets deep, hybrid"
cat <<'EOF'
RULE: telemetry is wide & cheap (scales to 1000s); packets are deep & expensive (one per choke point).

WIDE LAYER (every device):
  gNMI streaming → Grafana        (cisco/telemetry.md)
  SNMP polling → snmp_exporter
  NetFlow/IPFIX → ntopng collector

DEEP LAYER (3-5 choke points, inline Linux bridge + bypass tap):
  Internet edge:        S1 — br0 bridge + bypass tap → netwatch daemon --metrics --remote
  DB-tier uplink:       S2 — br0 + bypass tap
  WAN aggregation:      S3 — br0 + bypass tap
  (scripts/bridge-setup.sh + reference/sensor-builds.md Recipe A)

WINDOWS SENSORS (host-based or SPAN-destination — NEVER a transparent inline bridge):
  RustNet for live TUI, Pktmon for headless capture-to-disk
  (reference/sensor-builds.md Recipe B)

FLOW (when you don't need packets, just summaries):
  NetFlow/IPFIX from Cisco → ntopng/PRTG   (reference/architectures.md §9)
EOF
;;
  "10. Capture 24/7 to disk (headless ring buffer)")
  recommend "HEADLESS CAPTURE — tshark/dumpcap (Linux/Win) or Pktmon (Win)"
cat <<'EOF'
LINUX:
  sudo ./scripts/tshark-rotate.sh br0 /data/captures 100 50 "not port 22"
  # (ring buffer: 100MB files, keep last 50 = 5GB, exclude SSH noise)

WINDOWS (Pktmon, built-in):
  .\scripts\pktmon-sensor.ps1 -OutDir C:\caps -MaxGB 5
  # (rotates ETL, converts to pcapng on stop)
  # Schedule at startup via Task Scheduler

WINDOWS (tshark if Wireshark/Npcap installed):
  dumpcap -i "Ethernet" -w C:\cap.pcapng -b filesize:100000 -b files:50

ANALYZE A RING FILE:
  tshark -r cap.pcapng -Y "tcp.analysis.retransmission"
  tshark -r cap.pcapng -o "tls.keylog_file:/tmp/k.txt" -Y "http"
EOF
;;
  "11. Verify a network change (pyATS diff)")
  recommend "CHANGE VALIDATION — snapshot before, change, snapshot after, diff"
cat <<'EOF'
BEFORE:
  python3 pre_state.py before.json     # parse show interfaces/route/bgp on all devices

  (make your change on the Cisco device)

AFTER:
  python3 pre_state.py after.json
  python3 -c "from genie.diff import Diff; import json; \
    Diff(json.load(open('before.json')), json.load(open('after.json'))).find_diff(); ..."

  # Clean diff (only expected changes) = change did what you intended
  # Unexpected deltas = investigate immediately
  See: cisco/telemetry.md (pyATS section)
EOF
;;
  "12. ERSPAN from a Cisco device to a remote sensor")
  recommend "ERSPAN (IOS-XE/NX-OS only) — mirror across L3 via GRE"
cat <<'EOF'
SOURCE (Cisco IOS-XE):
  monitor session 1 type erspan-source
   source interface Gi1/0/10 both
   no shutdown
   destination
    erspan-id 100
    ip address <sensor-ip>
    origin ip address <this-device-loopback>
    mtu 1464
   exit

SENSOR (Linux — tshark auto-decaps GRE):
  sudo tshark -i eth0 -w erspan.pcap
  editcap --extract-gre erspan.pcap inner.pcap
  tshark -r inner.pcap -Y "tcp.port==443"

SENSOR (Linux — decap for netwatch/rustnet):
  sudo ./scripts/erspan-decap.sh eth0 erspan0 100
  sudo netwatch

CAVEATS: IOS-XE & NX-OS only (not small IOS switches); GRE overhead ~24B; match erspan-id.
  See: cisco/span-erspan.md
EOF
;;
  "Quit") break ;;
  *) echo "Invalid option." ;;
esac
echo
echo "Press Enter for the menu again..."; read -r
PS3="Symptom number → "
done
