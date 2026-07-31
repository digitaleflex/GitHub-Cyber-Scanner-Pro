# Scenario — DNS Troubleshooting

DNS is the #1 silent killer of connectivity. "Can't reach X" is often "can't resolve X." Always check DNS first in the 30-second triage.

---

## Triage

```bash
# 1. Does the host resolve the name correctly?
getent hosts example.com             # what the app actually sees (NSS: /etc/hosts first, then DNS)
dig example.com                      # detailed: query + answer + AUTHORITY + ADDITIONAL
dig +short example.com               # just the IP
dig +trace example.com               # full iterative resolution from root → TLD → authoritative
dig example.com @8.8.8.8             # via a public resolver — compare to internal
dig example.com @10.0.0.1            # via your internal resolver
dig example.com AAAA                 # IPv6 specifically
dig -x 10.20.30.40                   # reverse lookup
dig example.com MX NS SOA            # specific record types

# 2. Is the resolver reachable?
dig @10.0.0.1 example.com +time=2 +tries=1    # timeout in 2s if resolver down

# 3. What's the host configured to use?
cat /etc/resolv.conf
resolvectl status                     # systemd-resolved
# Windows:
Get-DnsClientServerAddress
ipconfig /all | findstr "DNS Server"
Resolve-DnsName example.com
```

---

## Symptom → cause map

| Symptom | Likely cause | Confirm with |
|---|---|---|
| `NXDOMAIN` | Name doesn't exist OR resolver can't reach authoritative | `dig +trace` from root |
| `SERVFAIL` | Resolver failing (overload, zone timeout, DNSSEC fail) | Check resolver logs; `dig +cd` to bypass DNSSEC |
| Timeout | Resolver unreachable / firewall / UDP 53 blocked | `dig +time=2`; SPAN resolver's port |
| Works via 8.8.8.8 but not internal | Split-horizon or internal resolver down/misconfigured | Compare `dig @8.8.8.8` vs `dig @internal` |
| Works for IP but not name | DNS only | Fix DNS (this file) |
| Intermittent NXDOMAIN | Split-horizon flapping, race in resolver cluster | Capture DNS on the client |
| Very slow first lookup, fast after | Caching off / far resolver | Check TTL; move resolver closer |
| Wrong IP returned | Hijack, split-horizon, stale cache, spoofing | `dig +trace`; check cache; security-ids.md |
| IPv4 works, IPv6 fails | AAAA returns unreachable IPv6, happy-eyeballs broken | `dig AAAA`; test IPv6 reachability |

---

## Playbook: "DNS resolves slowly / intermittently"

### Step 1 — Time the resolution
```bash
dig example.com | grep "Query time"             # > 100ms repeatedly = problem
for i in {1..10}; do dig example.com | grep "Query time"; sleep 1; done
```

### Step 2 — Trace where the delay is
```bash
dig +trace example.com                          # iterative — see each hop's RTT
dig +trace example.com @8.8.8.8                 # from a public root
dig example.com @10.0.0.1 +stats               # your resolver — RTT to it
```

### Step 3 — Capture DNS on the client (host-based)
```bash
sudo tshark -i any -Y "dns" -T fields -e frame.time -e dns.qry.name -e dns.flags.response -e dns.time
# dns.time = time between query and response (per query)
# High dns.time = resolver or authoritative is slow

# Or with ngrep (readable DNS query/response lines):
sudo ngrep -d eth0 -W byline -i 'example.com' 'udp port 53'
# Look for repeated queries (retransmissions = lost responses)
```

### Step 4 — Check the resolver
```
! If the resolver is a Cisco device (rare) or you manage it
show run | inc dns
show ip dns
```
```bash
# On a BIND/unbound resolver:
dig @resolver-ip example.com +stats
# Check resolver's own logs for timeouts, SERVFAIL, rate limits
```

### Fix
- Move the resolver closer (or use a local caching resolver like `dnsmasq`/`systemd-resolved`)
- If authoritative is slow → that's upstream; contact the zone owner or use a backup
- Check for DNSSEC validation failures (`dig +cd` bypasses — if it works with `+cd`, DNSSEC is misconfigured on the authoritative)

---

## Playbook: "internal DNS returns wrong IP (split-horizon)"

```bash
dig example.com @8.8.8.8 | grep -A1 ANSWER     # public answer
dig example.com @10.0.0.1 | grep -A1 ANSWER    # internal answer — compare
getent hosts example.com                        # what the app uses (NSS order)
```
If they differ → split-horizon is intended OR someone misconfigured the internal zone. Confirm with the resolver config. If the internal answer is wrong → fix the internal zone; if the public answer is wrong but internal is right → ensure hosts use the internal resolver.

---

## Playbook: "DNS over TCP / tunneling suspicion" (security)

DNS tunneling exfiltrates data over DNS queries (long subdomain labels, TXT records, high query rate). See security-ids.md for full detection; quick checks:

```bash
# Long labels in DNS queries = suspicious (data encoded in subdomain)
sudo tshark -i eth0 -Y "dns.flags.response == 0" -T fields -e dns.qry.name | awk '{print length($0)}' | sort -n | tail
# High query rate from one host:
sudo tshark -i eth0 -Y "dns.flags.response == 0" -T fields -e ip.src | sort | uniq -c | sort -rn | head
# TXT queries (common for tunneling):
sudo tshark -i eth0 -Y "dns.qry.type == 16"   # TXT
# ngrep for long DNS names:
sudo ngrep -d eth0 -W byline '.{40,}' 'udp port 53'    # names > 40 chars
```

---

## Playbook: "DNS server down — emergency"

```bash
# Point the host at a working resolver temporarily
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
# Or systemd-resolved:
resolvectl dns eth0 8.8.8.8 1.1.1.1
# Windows:
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 8.8.8.8
# Then verify:
dig example.com
```
> Note: pointing internal hosts at public resolvers breaks split-horizon names. Use only as emergency until the internal resolver is fixed.

---

## DNS capture on a sensor (SPAN to a Linux sensor)

If you want fleet-wide DNS visibility:
```
monitor session 1 source interface Gi1/0/10 both         ! client uplink
monitor session 1 destination interface Gi1/0/48         ! Linux sensor
```
```bash
# On the sensor — all DNS, summarized
sudo tshark -i eth0 -Y "dns" -q -z dns,tree
# Or live readable with ngrep:
sudo ngrep -d eth0 -W byline 'A |AAAA|MX' 'udp port 53'
```

---

## Evidence checklist

- [ ] `dig +trace` showing the resolution path and where it breaks/slows
- [ ] Query times (repeated) showing the latency
- [ ] Comparison: internal vs public resolver answers
- [ ] DNS capture (tshark/ngrep) during the problem — query/response timing
- [ ] Resolver config (`/etc/resolv.conf`, systemd-resolved, Windows DNS settings)
