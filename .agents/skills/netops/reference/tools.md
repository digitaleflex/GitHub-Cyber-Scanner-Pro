# Tool Reference — verified command syntax

Accuracy-verified against:
- NetWatch v0.26.1 README + `netwatch --help`
- RustNet README.md + ARCHITECTURE.md (domcyrus/rustnet)
- Wireshark/tshark 4.x man pages
- ngrep 8 man page (jpr5/ngrep, February 2026)
- Microsoft Pktmon docs (learn.microsoft.com/windows-server/networking/technologies/pktmon)

---

## 1. NetWatch — live packet-capture TUI

**Platform:** Linux (primary), macOS. Windows binary exists in releases but is **undocumented** — for Windows sensors prefer RustNet/Pktmon.
**Repo:** `matthart1983/netwatch` · v0.26.1 · MIT · Rust

### Privilege model
- `netwatch` (no sudo) → Dashboard, Connections, Interfaces, Processes, config. **No packet capture.**
- `sudo netwatch` → + live capture + health probes (Packets, Stats, Topology tabs come alive).
- Linux one-time cap grant to drop sudo: `sudo setcap 'cap_net_raw,cap_bpf,cap_perfmon+eip' "$(which netwatch)"` (re-run after every upgrade).

### ⚠ Interface selection — IMPORTANT (no `-i` flag)
NetWatch has **no `-i`/`--interface` CLI flag**. It captures on a single interface selected via:
1. **The `capture_interface` config key** in `~/.config/netwatch/config.toml` (default `""` = auto-select), OR
2. **The TUI Interfaces tab** (press `3`, navigate to the desired interface, select it).

For a bridge sensor, set the config before launching (headless-friendly):
```bash
# Pin netwatch to your bridge interface (persist across runs)
# Linux config path: $HOME/.config/netwatch/config.toml
# macOS config path: $HOME/Library/Application Support/netwatch/config.toml
sed -i 's/^capture_interface = ""/capture_interface = "br0"/' ~/.config/netwatch/config.toml
```
Or select `br0` in the Interfaces tab (press `3`) interactively.

> Why this matters: on a Linux bridge sensor you MUST capture on `br0` (sees both directions), never on the individual `eth0`/`eth1` NICs (each sees only one direction). See `reference/architectures.md` §Transparent bridge.

### Core commands
```bash
netwatch                       # unprivileged: dashboard, connections, interfaces, processes
sudo netwatch                  # full mode (+ live packet capture). Select interface in Interfaces tab (3)
# Pin to an interface via config first (recommended for sensors):
#   capture_interface = "br0"   in ~/.config/netwatch/config.toml
SSLKEYLOGFILE=/tmp/sslkeylog.txt sudo netwatch   # + live TLS 1.3 decrypt (Packets tab)
# TLS keylog also settable via config: tls_keylog_path = "/tmp/sslkeylog.txt"
```

### Daemon / headless mode
```bash
# No -i flag; pin the interface via capture_interface in config.toml BEFORE starting the daemon
netwatch daemon --metrics                              # Prometheus /metrics on 127.0.0.1:9464 + /healthz
netwatch daemon --remote https://netwatch.corp/api --api-key "$NW_KEY"   # stream to central
netwatch daemon --metrics --remote <url> --api-key <key>                # both (interface from config)
```

### Tabs (press `1`-`9`, `0`)
| Key | Tab | Purpose |
|---|---|---|
| `1` | Dashboard | Interfaces, bandwidth graph, top connections, gateway/DNS health, latency heatmap |
| `2` | Connections | Every socket + process/PID + protocol + state + GeoIP + latency sparklines |
| `3` | Interfaces | Per-iface IPv4/IPv6, MAC, MTU, RX/TX, errors, drops |
| `4` | Packets | Live L7 decode, **TLS 1.3 decryption**, JA4, per-flow stream tracking, display filters, PCAP export |
| `5` | Stats | Protocol breakdown by bytes + TCP handshake-timing histogram |
| `6` | Topology | ASCII map machine→gateway→DNS→hosts, with traceroute |
| `7` | Timeline | Connection timeline color-coded by TCP state; security alerts land here |
| `8` | Processes | Per-process bandwidth ranking, live RX/TX, connection counts |
| `9` | Insights | (opt-in) feed snapshot to local/cloud LLM for plain-language analysis |
| `0` | Egress | Learn per-process SNI/ASN/port baseline; promote to policy; warn on drift |

### Flight Recorder (evidence)
| Key | Action |
|---|---|
| `Shift+R` | Arm the rolling recorder |
| `Shift+F` | Freeze the current incident into a bundle |
| `Shift+E` | Export the bundle (packets + connections + DNS + health + alerts) |

### TUI keys
`?` help · `q` quit · `1`-`7` tabs · `/` filter · `Shift+R/F/E` Flight Recorder

### Collectors per platform (graceful degradation)
| Collector | macOS | Linux |
|---|---|---|
| Connections | `lsof` + PKTAP | `/proc/net/tcp` + eBPF kprobe |
| Packets | libpcap (BPF) | libpcap |
| Process attribution | PKTAP | `lsof`/`ss` polling + optional eBPF kprobe overlay |

### What NetWatch uniquely does (vs RustNet)
- **Live TLS 1.3 decryption** via `SSLKEYLOGFILE` (Packets tab shows plaintext)
- **JA4 fingerprinting** of TLS/QUIC clients (recognize malware by handshake)
- **Built-in threat detection**: C2 beaconing (low-jitter check-ins), port scans, DNS tunneling — auto-freezes recorder on critical alert
- **Topology tab** with traceroute from the sensor's POV
- **Flight Recorder** portable evidence bundles

### Caveats
- Landlock sandbox is **Linux-only** (drops privs + filesystem allow-list). macOS has no Landlock.
- eBPF kprobe for short-lived flows is **Linux-only**.
- Capture interface must be selected explicitly on a bridge sensor (`-i br0`), never the individual NICs.

---

## 2. RustNet — cross-platform process-attribution TUI

**Platform:** Linux, macOS, **Windows (first-class)**, FreeBSD
**Repo:** `domcyrus/rustnet` · ~4.6k stars · Apache-2.0 · Rust

### Install
```bash
# Linux (package managers)
brew install rustnet                       # macOS/Linux Homebrew
cargo install rustnet-monitor              # from source via crates.io
sudo apt install rustnet                   # Ubuntu 25.10+ (after adding PPA)
sudo dnf install rustnet                   # Fedora 42+ (after copr enable)
# Linux cap grant (drop sudo)
sudo setcap 'cap_net_raw,cap_bpf,cap_perfmon+eip' $(which rustnet)
```
```powershell
# Windows — requires Npcap (https://npcap.com) with "WinPcap API-compatible Mode" enabled
choco install rustnet
```

### Run
```bash
sudo rustnet                              # auto-select interface
sudo rustnet -i eth0                      # specific interface
rustnet --show-localhost                  # include loopback connections
rustnet --no-resolve-dns                  # disable reverse DNS (faster)
rustnet -r 500                            # refresh interval ms
rustnet --theme classic                   # full-color palette (default: muted)
sudo rustnet --pcap-export cap.pcap      # capture with process-attribute sidecar
```
Windows: run as **Administrator**; interface names like `"Ethernet"` (quoted).

### Tabs (press `1`-`5`, `Tab`/`]` next, `Shift+Tab`/`[` prev)
| Key | Tab |
|---|---|
| `1` | Overview — connections table with live stats and sparklines |
| `2` | Details — per-connection SNI, cipher, GeoIP, DPI |
| `3` | Interfaces — per-iface RX/TX history, errors, drops |
| `4` | Graph — traffic chart, app distribution, top processes |
| `5` | Help |

### Filter language (vim/fzf style — enter with `/`)
```
port:443
src:10.0.0.5
dst:8.8.8.8
sni:github.com
process:chrome
state:established
proto:tcp
/regex/                # plain regex
/(?i)pattern/         # case-insensitive regex
```
Combine by typing multiple, e.g. `port:443 process:curl`.

### Other keys
`q` quit (×2 to confirm) · `Ctrl+C` force quit · `x` clear connections (×2) · `Enter` details · `c` copy remote addr · `p` service/port toggle · `d` hostnames/IP toggle · `s`/`S` sort · `a` process grouping · `t` show historic (closed) conns · `g`/`G` first/last · `/` filter · `h` help

### DPI protocols recognized
HTTP, HTTPS/TLS+SNI, DNS, SSH, FTP, QUIC, MQTT, BitTorrent, STUN, NTP, mDNS, LLMNR, DHCP, SNMP, SSDP, NetBIOS.

### Sandboxing (drops privs immediately after libpcap init)
| Platform | Mechanism |
|---|---|
| Linux 5.13+ | Landlock filesystem allow-list |
| macOS | Seatbelt |
| Windows | Token privilege drop + job-object child-process block |
| FreeBSD | (basic) |

### Process attribution per platform
| Platform | Mechanism |
|---|---|
| Linux | **eBPF** (libbpf-rs) by default — falls back to procfs if eBPF unavailable |
| macOS | PKTAP |
| Windows | **native Windows APIs** |
| FreeBSD | procfs |

> **eBPF caveat:** kernel `comm` field is 16 chars — multi-threaded apps may show thread names ("Socket Thread", "Chrome_IOThread"). To disable eBPF and use procfs: `cargo build --release --no-default-features`.

### PCAP export with process sidecar (forensic advantage over NetWatch)
```bash
sudo rustnet --pcap-export cap.pcap
# Then enrich for Wireshark with full PID/process context:
python3 scripts/pcap_enrich.py cap.pcap cap_enriched.pcap
# Open cap_enriched.pcap in Wireshark — each packet annotated with owning process
```

### What RustNet uniquely does (vs NetWatch)
- **First-class Windows support** (documented, sandboxed, native process APIs)
- **PCAP export with process-attribute sidecar** (Wireshark sees which PID owned each packet)
- **JSON event logging** (ship to SIEM)
- TCP retransmission / out-of-order / fast-retransmit analytics (per-connection + aggregate)

### What RustNet does NOT do (NetWatch does)
- No live TLS decryption via `SSLKEYLOGFILE`
- No JA4 fingerprinting
- No built-in threat detection (C2 beaconing, port scans, DNS tunneling)
- No Topology/traceroute tab
- No Flight Recorder evidence bundles
- Positions itself as "live connection monitoring + DPI + process," **not** full forensic capture (explicitly: "for deep forensic analysis, use `--pcap-export` then Wireshark")

---

## 3. tshark / dumpcap — scriptable capture & analysis

**Platform:** all (Linux, macOS, Windows via Npcap)
**Source:** Wireshark project · GPL-2.0

### Live capture → file
```bash
sudo tshark -i eth0 -w cap.pcapng                                   # all traffic
sudo tshark -i eth0 -f "tcp port 443" -w cap.pcapng                  # BPF filter (kernel-level)
sudo tshark -i eth0 -Y "tls.handshake.type == 1" -w cap.pcapng       # display filter (post-capture, slower)
# Multiple interfaces
sudo tshark -i eth0 -i eth1 -w cap.pcapng
```

### Ring-buffer capture (24/7, rotating files)
```bash
# dumpcap is the capture core (lighter than tshark for long runs)
sudo dumpcap -i eth0 -w /data/cap.pcapng \
  -b filesize:100000   \   # 100 MB per file
  -b files:50          \   # keep last 50 files (5 GB total)
  -b duration:3600        # or rotate hourly
# tshark equivalent:
sudo tshark -i eth0 -w /data/cap.pcapng -b filesize:100000 -b files:50
```

### Reading / analyzing pcaps
```bash
tshark -r cap.pcapng                                          # replay
tshark -r cap.pcapng -Y "tcp.analysis.retransmission"         # retransmits
tshark -r cap.pcapng -Y "tcp.flags.syn==1 && tcp.flags.ack==0"  # SYNs (connection attempts)
tshark -r cap.pcapng -Y "tls.handshake.type == 2"             # ServerHellos
tshark -r cap.pcapng -Y "dns.flags.response == 0"             # DNS queries
tshark -r cap.pcapng -T fields -e frame.time -e ip.src -e ip.dst -e tcp.dstport   # tabular extract
tshark -r cap.pcapng -q -z conv,tcp                           # conversation summary
tshark -r cap.pcapng -q -z io,stat,1                          # per-second throughput
```

### TLS decryption (post-hoc and live)
```bash
# Post-hoc: feed the keylog file
tshark -r cap.pcapng -o "tls.keylog_file:/tmp/sslkeylog.txt" -Y "http"   # show decrypted HTTP
# Live: set the same option during capture
sudo tshark -i eth0 -o "tls.keylog_file:/tmp/sslkeylog.txt" -w cap.pcapng
```
> `SSLKEYLOGFILE` is exported by the **client** (browser/curl/Python). You must control the client. It never works against third-party or malware TLS.

### ERSPAN decapsulation (when sensor receives GRE-encapsulated ERSPAN)
```bash
# Native (Wireshark/tshark auto-decapsulate GRE by default, but to be explicit):
tshark -r erspan.pcap -Y "gre" -V | head          # confirm GRE present
# To extract inner packets into a new pcap:
editcap --extract-gre erspan.pcap inner.pcap      # editcap ships with Wireshark
# Or use a dedicated decap script (see scripts/erspan-decap.sh)
```

### Statistics
```bash
tshark -r cap.pcapng -q -z io,stat,0               # total summary
tshark -r cap.pcapng -q -z conv,ip                # IP conversations
tshark -r cap.pcapng -q -z endpoints,ip           # top talkers
tshark -r cap.pcapng -q -z proto,colinfo,tcp,tcp.analysis.rto_stddev   # retransmit stats
```

### Useful display filters
| Want | Filter |
|---|---|
| TCP retransmissions | `tcp.analysis.retransmission` |
| TCP out-of-order | `tcp.analysis.out_of_order` |
| DUP ACKs | `tcp.analysis.duplicate_ack` |
| Zero window | `tcp.window_size_value == 0` |
| TLS ClientHello | `tls.handshake.type == 1` |
| TLS ServerHello | `tls.handshake.type == 2` |
| TLS alert (handshake failure etc.) | `tls.alert_message` |
| DNS over TCP (possible tunneling) | `tcp.port == 53 && dns` |
| HTTP 5xx | `http.response.code >= 500` |
| ICMP unreachable | `icmp.type == 3` |
| ICMP frag-needed (PMTUD) | `icmp.type == 3 && icmp.code == 4` |

### Windows (native)
```powershell
# Requires Wireshark + Npcap installed
tshark -i "Ethernet" -f "tcp port 443" -w C:\cap.pcapng
dumpcap -i "Ethernet" -w C:\cap.pcapng -b filesize:100000 -b files:50
```

---

## 4. ngrep — network grep (regex on live payload)

**Platform:** all (Linux, macOS, Windows via WSL/Npcap-compatible builds)
**Repo:** `jpr5/ngrep` · ngrep 8 (February 2026)

### Syntax
```
ngrep <-hNXViwqpevxlDtTRMCu> <-IO pcap_dump> <-n num> <-d dev> <-A num>
       <-s snaplen> <-S limitlen> <-W normal|byline|single|none> <-c cols>
       <-P char> <-F file> <match expression> <bpf filter>
```

### Live capture
```bash
sudo ngrep -d eth0 -W byline 'GET|POST' tcp port 80          # HTTP methods, line-wrapped
sudo ngrep -d eth0 -i 'error|exception|panic' port 5432      # app error strings (case-insensitive)
sudo ngrep -d eth0 -w 'password' 'tcp port 21'                # word match (FTP password)
sudo ngrep -d eth0 -X 'cafebabe'                              # hex pattern match
sudo ngrep -d eth0 -q -t 'ERROR' 'tcp port 514'               # quiet, timestamped (syslog)
sudo ngrep -d eth0 -A 3 'HTTP/' 'tcp port 80'                 # 3 packets of context after match
sudo ngrep -d eth0 -n 50 'User-Agent' 'tcp port 80'           # stop after 50 matches
sudo ngrep -d eth0 -K 5 'evil.com' 'tcp port 443'             # kill matching conns (5 RSTs)
sudo ngrep -d eth0 -C 'admin' 'tcp port 80'                   # colorize matches
```

### Search a pcap file
```bash
ngrep -I cap.pcap 'password|secret|token'                     # search a capture
ngrep -I cap.pcap -W byline 'Host:'                           # all Host headers
ngrep -I cap.pcap -O matched.pcap 'SETCOOKIE' 'tcp port 80'  # write matched packets to new pcap
```

### Key flags (verified from man page)
| Flag | Effect |
|---|---|
| `-d dev` | Listen on interface `dev` |
| `-i` | Ignore case |
| `-w` | Match as word |
| `-X` | Treat match expression as hex |
| `-x` | Dump hex+ASCII |
| `-W byline` | Wrap on linefeeds (great for HTTP/text protocols) |
| `-W none` | One line per packet |
| `-W single` | Everything (headers+payload) on one line |
| `-q` | Quiet (no headers, just matches) |
| `-t` | Print timestamp per match |
| `-T` | Print delta between matches |
| `-A num` | `num` packets of trailing context |
| `-n num` | Stop after `num` matches |
| `-s snaplen` | BPF snaplen (default 65536) |
| `-S limitlen` | Only inspect first N bytes |
| `-I file` | Read pcap file |
| `-O file` | Write matched packets to pcap |
| `-K num` | Kill matching TCP conns (send N RSTs) |
| `-p` | Don't use promiscuous mode |
| `-C` | Colorize matches |
| `-l` | Line-buffered stdout (for piping) |
| `-D` | Replay pcap at recorded timing |
| `-v` | Invert match |
| `-F file` | Read BPF filter from file |
| `-R` | Don't drop privileges (use with caution) |

### When ngrep beats tshark
- You want a **plain regex on payload** and don't need protocol dissection
- Quick "does this string appear in traffic" answers (credentials, error messages, banners)
- `-W byline` makes text protocols (HTTP, SMTP, FTP, syslog) immediately readable
- `-K` can actively kill matching connections (tcpkill-like)

### When tshark wins
- You need structured field extraction (`-T fields -e ...`)
- Protocol-aware decode (TLS handshakes, DNS, QUIC)
- Statistics/conversation summaries
- Ring buffers and 24/7 capture

---

## 5. Pktmon (Packet Monitor) — built into Windows 10/11/Server

**Platform:** Windows 10/11, Windows Server 2019+ (built in — **zero install**)
**Source:** Microsoft (learn.microsoft.com/windows-server/networking/technologies/pktmon)

### Why it matters
Already on every modern Windows box. Kernel-level capture (sees things userspace sniffers miss via Npcap). Multi-NIC capture. Exports to pcapng for Wireshark. The zero-cost headless Windows sensor.

### List interfaces and components
```powershell
pktmon list                       # list all network interfaces
pktmon list --components          # list capture components (NICs, filters, providers)
```

### Filters (apply BEFORE start)
```powershell
pktmon filter add F1 -t TCP -p 443            # TCP port 443
pktmon filter add F2 -i 10.0.0.5              # IP address
pktmon filter add F3 -t UDP -p 53             # UDP DNS
pktmon filter remove F1                       # remove a filter
pktmon filter                                 # list filters
```

### Real-time capture (live to console)
```powershell
pktmon start --capture --comp nics -m real-time
pktmon stop
```
> `--capture` enables packet capture+counters · `--comp nics` selects NIC components · `-m real-time` is the log-mode that streams live to console instead of buffering to a file.

### Capture to ETL file (headless / 24/7)
```powershell
# Full packet capture (--pkt-size 0 = no snaplen truncation)
pktmon start --capture --comp nics --pkt-size 0 -f C:\caps\cap.etl
pktmon stop
```

### ⚠ Authoritative `pktmon start` syntax (verified — MS Learn)
```
pktmon start [--capture [--counters-only] [--comp <selector>] [--type <type>] [--pkt-size <bytes>] [--flags <mask>]]
             [--trace --provider <name> [--keywords <k>] [--level <n>] ...]
             [--file-name <name>] [--file-size <size>] [--log-mode <mode>]
```
| Flag | Meaning | Notes |
|---|---|---|
| `-c` / `--capture` | Enable packet capture + counters | NOT a component selector |
| `-o` / `--counters-only` | Counters only (no packets) | Light overhead |
| `--comp <selector>` | Component selector (`nics`, or a NIC ID) | Use `nics` for all NICs |
| `--type <type>` | Packet type filter | e.g. `tcp`, `udp` |
| `--pkt-size <bytes>` | Snaplen (0 = full packet) | 0 = no truncation |
| `--flags <mask>` | Packet flag mask | advanced |
| `-t` / `--trace` | Enable event collection | For ETW providers |
| `-p` / `--provider <name>` | **Trace provider** (in `start`!) | NOT a port — common confusion |
| `-k` / `--keywords <k>` | Provider keywords | for --trace |
| `-l` / `--level <n>` | Provider level | for --trace |
| `-f` / `--file-name <name>` | Output ETL file | |
| `-s` / `--file-size <size>` | File size limit | for rotation |
| `-m` / `--log-mode <mode>` | Log mode: `circular`, `real-time`, `multi-file`, `memory` | `real-time` = stream to console |

> **Critical flag-meaning gotcha:** `-p` means **provider** in `pktmon start` context (for `--trace`) but **port** in `pktmon filter` context. Don't confuse them. There is no port flag on `pktmon start`; filter by port using `pktmon filter add ... -p <port>` BEFORE starting.

### Convert ETL → pcapng for Wireshark/tshark
```powershell
pktmon etl2pcap C:\caps\cap.etl -o C:\caps\cap.pcapng
# Then open in Wireshark or analyze with tshark:
# tshark -r C:\caps\cap.pcapng -Y "tcp.analysis.retransmission"
```

### Counters (high-level, low-overhead — great for "is it dropping?")
```powershell
pktmon counters                       # show all counters
pktmon counters --comp nics            # NIC-level only
pktmon counters --json                 # machine-readable
# Use in a loop for trend:
while ($true) { Clear-Host; pktmon counters --comp nics; Start-Sleep 2 }
```

### View an ETL file (without converting)
```powershell
pktmon view C:\caps\cap.etl            # text dump
pktmon view C:\caps\cap.etl --json     # JSON
pktmon view C:\caps\cap.etl -p         # show payload
```

### Windows PowerShell event tracing (alternative / scriptable)
```powershell
# Set up a packet-capture session programmatically
$session = New-NetEventSession -Name "Sensor" -LocalFilePath "C:\caps\trace.etl"
Add-NetEventPacketCaptureProvider -SessionName "Sensor" -TruncateLength 0
Start-NetEventSession -Name "Sensor"
# ... capture ...
Stop-NetEventSession -Name "Sensor"
Remove-NetEventSession -Name "Sensor"
```

### Pktmon caveats
- ETL is Microsoft's format — **convert to pcapng** before any non-Microsoft tool can read it.
- No TUI/dashboard — it's a capture engine, not a monitor. Pair with Wireshark for analysis.
- For "live TUI on Windows," use **RustNet**, not Pktmon. Pktmon is for headless capture-to-disk.
- Requires **Administrator** privileges.

---

## Cross-tool decision table (quick)

| You want… | Use |
|---|---|
| Live TUI, full packets, TLS decrypt, threats | NetWatch (Linux/macOS) |
| Live TUI, process attribution, Windows | RustNet |
| Regex on payload, fast "does X appear?" | ngrep |
| Scripted 24/7 capture with ring buffers | tshark/dumpcap |
| Windows, zero install, capture to disk | Pktmon |
| Deep forensic decode of a pcap | Wireshark/tshark |
| Process-annotated pcap for Wireshark | RustNet `--pcap-export` + `pcap_enrich.py` |
| IDS / attack detection at scale | Suricata (native Windows build exists) |
