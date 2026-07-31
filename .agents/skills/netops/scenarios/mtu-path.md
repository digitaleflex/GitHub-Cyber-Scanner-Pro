# Scenario — MTU / Path MTU Discovery / Fragmentation

One of the most under-diagnosed causes of "intermittent hangs" and "large transfers fail but small ones work." Classic symptoms: SSH works but `scp` of a large file stalls; HTTPS to some sites hangs on handshake; VPN tunnels drop large packets.

---

## How PMTUD works (and breaks)

Hosts discover the path MTU by sending a packet with the Don't-Fragment (DF) bit set. When it hits a link with a smaller MTU, the router should send back **ICMP Type 3 Code 4 (Fragmentation Needed)**. The host then lowers its path MTU.

**It breaks when:**
- ICMP Type 3 Code 4 is filtered/blocked by a firewall (common! "block all ICMP" policies)
- A tunnel (GRE/IPsec) reduces MTU but doesn't propagate ICMP back correctly
- An intermediate link has a lower MTU than expected

Result: the host never learns the real MTU, keeps sending oversized DF packets that get silently dropped → large packets die, small ones live → "intermittent."

---

## Triage

```bash
# 1. Does ICMP-based PMTUD work?
tracepath example.com                  # reports "pmtu N" when it discovers a bottleneck
tracepath -n example.com
# 2. Force a specific packet size with DF set (Linux)
ping -c 3 -M do -s 1472 example.com    # 1472 + 28 (ICMP+IP hdr) = 1500. "do" = don't fragment
#   - If it works → MTU 1500 is fine end-to-end
#   - If "Frag needed and DF set" (or message too long) → PMTUD is reporting back; lower the size until it works
ping -c 3 -M do -s 1452 example.com    # try 1480 total (common for GRE tunnels)
ping -c 3 -M do -s 1372 example.com     # try 1400 total (common for IPsec)
# 3. On Windows
ping -f -l 1472 example.com            # -f = don't fragment, -l = payload size
# 4. Find the exact bottleneck hop
tracepath -n example.com | grep pmtu   # shows which hop reported the smaller MTU
```

---

## Symptom → cause map

| Symptom | Likely cause | Confirm with |
|---|---|---|
| `scp`/`rsync` stalls, `ssh` interactive fine | PMTUD black hole on large packets | `tracepath`; ping with `-M do` |
| HTTPS handshake hangs for some sites | Large ClientHello/ServerHello exceeds path MTU | tls-https.md + capture |
| Works after `ping -M do -s 1452` succeeds but `-s 1472` fails | A hop has MTU 1480 (typical GRE) | `tracepath`; check tunnel MTU |
| ICMP Type 3 Code 4 filtered | Firewall "block all ICMP" policy | Capture on the return path |
| Only fails through VPN/IPsec | Tunnel overhead reduces MTU | Set MSS clamp on tunnel |
| `show interface` MTU mismatch | One side jumbo, other side 1500 | Align MTUs |

---

## Playbook: "large file transfers stall, small work fine"

### Step 1 — Confirm it's MTU
```bash
ping -c 3 -M do -s 1472 target       # fails
ping -c 3 -M do -s 1452 target       # works? → path MTU ~1480 (GRE)
ping -c 3 -M do -s 1372 target       # works? → path MTU ~1400 (IPsec)
tracepath -n target                   # shows "pmtu N" and the bottleneck hop
```

### Step 2 — Capture the ICMP frag-needed (or its absence)
SPAN the path or run host-based and look for ICMP Type 3 Code 4:
```bash
sudo tshark -i eth0 -Y "icmp.type == 3 && icmp.code == 4"
# If you see it → PMTUD is reporting; the sender should lower MTU
# If you DON'T see it (but you see the big DF packets getting dropped) → ICMP is filtered
```
With ngrep (hex ICMP type 3):
```bash
sudo ngrep -d eth0 -X '0304' 'icmp'       # ICMP unreachable, frag needed (raw hex on type+code)
# (tshark is more reliable for this — use tshark)
```

### Step 3 — Find the ICMP-filtering firewall
```
! On Cisco devices along the path
show ip access-lists | inc icmp
show running-config | inc icmp
! Look for "deny icmp any any" or overly-broad ICMP blocks
```
> **Fix:** allow ICMP Type 3 Code 4 (fragmentation needed) explicitly. It is **not** a security risk; blocking it breaks PMTUD for everyone.
```
access-list 101 permit icmp any any packet-too-big    ! Type 3 Code 4
! Or more specific: allow from your internal subnets
```

### Step 4 — Mitigate with TCP MSS clamping (if you can't fix ICMP filtering)
On the router/tunnel endpoint, clamp TCP MSS so TCP never sends oversized segments:
```
! IOS-XE — on the tunnel or the interface facing the smaller-MTU path
interface Tunnel0
 ip tcp adjust-mss 1360                ! for IPsec (1400 MTU - 40 TCP/IP)
! Or for a GRE tunnel:
interface Tunnel0
 ip tcp adjust-mss 1436                ! 1480 MTU - 40
```
> MSS clamp doesn't fix UDP/ICMP PMTUD — only TCP. For UDP you must fix the ICMP filtering or set a smaller MTU on the tunnel.

### Step 5 — Check tunnel MTUs
```
show interface Tunnel0 | inc MTU
show ip route <remote>
```
```bash
# On Linux GRE/IPsec tunnels, verify the tunnel MTU
ip link show tun0 | grep mtu
# Lower if needed:
sudo ip link set dev tun0 mtu 1400
```

---

## Playbook: "jumbo frames (9000 MTU) end-to-end"

If you run jumbo frames internally and something doesn't work:

### Check every hop's MTU
```
show interface Gi1/0/24 | inc MTU      ! each switch/router
```
```bash
ip link show eth0 | grep mtu           # each Linux host
sudo ethtool -G eth0 rx 4096           # ring buffers (jumbo often needs larger)
# Set jumbo on a NIC:
sudo ip link set dev eth0 mtu 9000
# Verify end-to-end with a 9000-byte ping:
ping -c 3 -M do -s 8972 target         # 8972 + 28 = 9000
```

### Common jumbo pitfalls
- One switch port still at 1500 → silent drops of 9000-byte frames (no fragmentation with jumbo + DF)
- LACP bundles with mismatched member MTUs
- VMs with MTU 1500 on a 9000 vSwitch → guest sends 1500, host forwards 9000 (works) but reverse can break
- Set MTU consistently on the **whole path** or don't use jumbo at all

---

## Playbook: "VPN/IPsec — large packets die"

IPsec adds overhead (ESP + UDP encapsulation) reducing effective MTU to ~1400 or less.

```
! On the IPsec tunnel / crypto interface
interface Tunnel0
 ip tcp adjust-mss 1360                ! TCP MSS clamp for the typical 1400 IPsec MTU
! Or set the tunnel MTU explicitly:
interface Tunnel0
 ip mtu 1400
```
```bash
# Linux (StrongSwan/WireGuard) — set MTU on the interface
sudo ip link set dev wg0 mtu 1280      # WireGuard default-safe
# Test
ping -c 3 -M do -s 1372 target
```
> If `ping -M do` works at 1372 but the app still stalls on large UDP, you have a UDP path-MTU issue that MSS clamping can't fix → fix ICMP filtering (Step 3) so PMTUD works for UDP.

---

## Quick MTU reference (payload sizes for `ping -s`)

| Path MTU | `ping -s` value (ping payload; +28 = full packet) | Typical scenario |
|---|---|---|
| 1500 | 1472 | Standard Ethernet |
| 1480 | 1452 | GRE tunnel (~20 overhead) |
| 1400 | 1372 | IPsec (~100 overhead) |
| 1280 | 1252 | WireGuard / IPv6 minimum |
| 9000 | 8972 | Jumbo frames |

---

## Evidence checklist

- [ ] `tracepath` output showing the bottleneck hop and reduced MTU
- [ ] `ping -M do -s <size>` results (binary search for the working size)
- [ ] Capture showing ICMP Type 3 Code 4 either present (PMTUD works) or absent (filtered)
- [ ] `show ip access-lists` showing any ICMP filtering
- [ ] MTU on every hop (`show interface MTU`, `ip link show mtu`)
- [ ] The fix: ICMP unblock + MSS clamp + tunnel MTU setting
