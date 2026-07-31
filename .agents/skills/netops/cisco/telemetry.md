# Cisco Native Telemetry — the wide/cheap layer

Verified against Cisco IOS-XE 17.x configuration guides, NX-OS docs, and pyATS/Genie documentation. Use these BEFORE reaching for packet sensors — they scale to the whole fleet and have no SPOF.

**Golden rule:** Telemetry tells you *which device/link* is misbehaving. Packets tell you *why*. Start here; escalate to a SPAN/sensor when telemetry (or a clear user symptom) points at a specific suspect.

---

## 1. SNMP — universal, polling, every device

### When
- Fleet-wide interface counters, errors, CPU/mem, environmental
- Works on essentially every Cisco device ever made

### IOS-XE enable
```
snmp-server community public RO IPv6-BASE
snmp-server community secure RO SNMPv3-RO
snmp-server group GRPV3 v3 priv read SNMPv3-RO
snmp-server user admin GRPV3 v3 auth sha <authpass> priv aes 128 <privpass>
snmp-server host 10.20.30.40 version 3 priv admin traps
snmp-server enable traps
```

### Poll with snmp_exporter (Prometheus)
```yaml
# snmp_exporter snmp.yml
modules:
  cisco_ios:
    walk:
      - 1.3.6.1.2.1.2          # ifTable (interfaces)
      - 1.3.6.1.2.1.31.1.1     # ifXTable (64-bit counters)
      - 1.3.6.1.4.1.9.9.109.1  # cisco memory pool
      - 1.3.6.1.4.1.9.2.1.58   # CPU
    metrics:
      - {name: ifHCInOctets,   OID: 1.3.6.1.2.1.31.1.1.1.6}
      - {name: ifHCOutOctets,  OID: 1.3.6.1.2.1.31.1.1.1.10}
      - {name: ifInErrors,     OID: 1.3.6.1.2.1.2.2.1.14}
      - {name: ifOutErrors,    OID: 1.3.6.1.2.1.2.2.1.20}
```

### Quick CLI polling (one-off)
```bash
# Interface input errors on a device
snmpwalk -v3 -u admin -l authPriv -a SHA -A '<authpass>' -x AES -X '<privpass>' \
  10.0.0.1 1.3.6.1.2.1.2.2.1.14
# CPU 5-sec
snmpget -v3 ... 10.0.0.1 1.3.6.1.4.1.9.2.1.58.0
```

### Caveats
- 32-bit counters wrap at ~114 Mbps — use 64-bit `ifHC*` counters for modern links
- Polling interval ≥ 30s for fleet scale
- SNMPv1/v2c are cleartext — use SNMPv3 for production

---

## 2. gNMI — streaming telemetry (sub-second, push)

### When
- Modern Cisco (IOS-XE 17.x, IOS-XR, NX-OS)
- Sub-second interface counters, BGP, OSPF, environmental
- Better than SNMP polling for fast detection

### IOS-XE enable
```
gnm
 subscription
  update-policy every-2-seconds
 exit
!
gnmi server
 port 57400
 no-tls
!
gnmi authentication group SNMPv3-RO
```

### Subscribe with `gnmic` (Linux collector)
```bash
# Stream interface counters every 2s
gnmic -a 10.0.0.1:57400 --username admin --password '<pass>' --insecure subscribe \
  --path "/interfaces/interface/state/oper-status" \
  --path "/interfaces/interface/state/counters/in-octets" \
  --path "/interfaces/interface/state/counters/out-octets" \
  --path "/interfaces/interface/state/counters/in-discards" \
  --stream-mode sample --sample-interval 2s

# Stream BGP session state
gnmic -a 10.0.0.1:57400 ... subscribe \
  --path "/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state/session-state"
```

### Export to Prometheus
Run `gnmic` with `--exporter` to expose `/metrics`, or use `prom-gnmi-exporter`. Grafana dashboards per device.

### Caveats
- gNMI path models follow OpenConfig YANG — paths like `/interfaces/interface[name=Gi0/0]/state/...`
- TLS by default; `no-tls` for lab, keep TLS for production
- Much lighter on devices than SNMP polling (push vs poll)

---

## 3. NETCONF / RESTCONF + YANG — structured config & state

### When
- Transactional config changes (rollback on failure)
- Structured operational state queries (not text parsing)

### IOS-XE enable
```
netconf-yang
netconf-yang feature candidate-datastore
restconf
```

### NETCONF example (Python ncclient)
```python
from ncclient import manager
with manager.connect(host="10.0.0.1", port=830, username="admin", password="<pass>",
                     hostkey_verify=False, look_for_keys=False) as m:
    # Get interface state
    reply = m.get(filter=('subtree',
        '<filter><interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"/></filter>'))
    print(reply.xml)
```

### RESTCONF (HTTP/HTTPS)
```bash
# Get interface state
curl -s -k -u admin:<pass> \
  -H "Accept: application/yang-data+json" \
  https://10.0.0.1:443/restconf/data/ietf-interfaces:interfaces-state | jq .
```

---

## 4. CLI `show` commands — the reality of troubleshooting

Most real Cisco troubleshooting is still CLI. Here's a curated quick-reference.

### Interface / physical
```
show interface Gi1/0/24              ! errors, drops, duplex, last-input-output
show interface Gi1/0/24 detail       ! detailed including error counters
show interface counters errors       ! all interfaces' error counters
show interface description
show platform hardware fed switch active fwd-asic counters rewrite drop all
show controllers ethernet-controller Gi1/0/24  ! low-level phy counters
```

### Layer 2
```
show mac address-table               ! CAM table
show mac address-table address aaaa.bbbb.cccc  ! where did this MAC come from
show vlan brief
show spanning-tree                   ! STP state, blocked ports
show etherchannel summary            ! LACP bundles
show interfaces trunk                ! trunk allowed VLANs
show ip arp                          ! ARP cache
```

### Layer 3 / routing
```
show ip route                        ! routing table
show ip route 10.20.30.0             ! route for a specific prefix
show ip cef 10.20.30.0               ! FIB entry
show ip cef 10.20.30.0 detail        ! with load-share
show ip protocols                    ! routing protocols configured
show ip ospf neighbor                 ! OSPF adjacencies
show ip ospf interface brief
show ip bgp summary                   ! BGP sessions + state
show ip bgp neighbors 10.0.0.2       ! detailed BGP neighbor
show ip bgp 10.20.30.0                ! BGP path for a prefix
show ip nhrp                          ! DMVPN
show vrf                             ! VRFs
show ip route vrf MGMT                ! route in a VRF
```

### QoS / congestion
```
show policy-map interface Gi1/0/24   ! QoS stats per class
show class-map                        ! QoS class definitions
show queueing interface Gi1/0/24      ! queue drops
```

### Diagnostic / health
```
show processes cpu sorted             ! CPU hogs
show processes cpu history            ! 60s/60m/72h CPU graph
show memory statistics                 ! memory pools
show platform                          ! hardware
show inventory                         ! hardware inventory
show environment all                    ! temp, fans, power
show log                               ! syslog
show logging | inc %LINK-              ! link up/down events
```

### SPAN session verification
```
show monitor                           ! all SPAN sessions
show monitor session 1                 ! details of session 1
```

---

## 5. pyATS / Genie — automated change validation & diff

**You have a `pyats` skill.** This is the production way to validate changes: snapshot before, change, snapshot after, diff structured.

### Testbed
```yaml
# testbed.yaml
devices:
  R1:
    os: iosxe
    type: router
    credentials:
      login:
        username: admin
        password: '%ENV{PYATS_PASS}'
    connections:
      cli:
        protocol: ssh
        ip: 10.0.0.1
  C1:
    os: iosxe
    type: switch
    credentials: {login: {username: admin, password: '%ENV{PYATS_PASS}'}}
    connections: {cli: {protocol: ssh, ip: 10.0.0.11}}
```

### Pre/post diff script
```python
from genie.testbed import load
import json, sys
tb = load('testbed.yaml')
state = {}
for name, dev in tb.devices.items():
    dev.connect()
    state[name] = {
        'interfaces': dev.parse('show interfaces'),
        'route': dev.parse('show ip route'),
        'bgp': dev.parse('show ip bgp summary'),
    }
# Save baseline
with open(sys.argv[1], 'w') as f:
    json.dump(state, f, indent=2, default=str)
# To diff after a change:
#   from genie.diff import Diff
#   before = json.load(open('before.json'))
#   after  = ... (re-parse)
#   diff = Diff(before, after)
#   diff.find_diff()
#   print(diff)
```

### Genie ops (learn the whole network state, compare across runs)
```python
from genie.ops import Ops
from genie.libs.ops.interface.iosxe.interface import Interface
dev.connect()
ops = Interface(dev)
ops.learn()                          # structured dict of all interfaces
# Compare to a previous learned state with genie.diff
```

---

## Telemetry → packets escalation triggers

These telemetry findings warrant escalating to a packet sensor:

| Telemetry signal | Escalate to packet sensor because… |
|---|---|
| `show interface` shows input errors / CRC climbing | Likely physical/L1 — but need packets to confirm (frame size? duplex? cabling?) |
| BGP session `Idle`/`Active` flapping | Could be TCP reset, MTU black-hole, or routing loop — packets prove which |
| OSPF adjacency stuck in `EXSTART` | Often MTU mismatch — need to see the DBD packets |
| Interface output drops rising | Congestion/QoS misclassification — need to see the traffic mix |
| High CPU on control plane | Could be malicious traffic to CPU — packets prove it |
| Latency spikes without error counters | Bufferbloat, microbursts, or upstream issue — packets show queue depth + retransmits |
| New MAC appearing on a port | MAC flapping or ARP spoofing — packets show the frames |
| gNMI: new SNI/IP the device talks to | Possible malware — JA4 + beaconing detection on a sensor |

Telemetry gets you to the suspect in seconds; the sensor then proves the why in minutes.
