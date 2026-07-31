# Secator Complete Reference

Full CLI and Python library reference for Secator v0.31.0 — the task and workflow runner for security assessments.

## Installation

```bash
pip install secator
secator install tools   # Install all supported tools
secator install addons worker  # Optional: distributed worker support
```

## CLI Commands

### Global Syntax
```bash
secator [command] [subcommand] [target] [options]
```

### Commands Overview

| Command | Alias | Purpose |
|---------|-------|---------|
| `secator x` | execute | Run individual tasks |
| `secator w` | workflow | Run predefined workflows |
| `secator s` | scan | Run predefined scans |
| `secator u` | utility | Run utilities |
| `secator c` | config | Manage configuration |

---

## Tasks (secator x)

### Recon Tasks

| Task | Category | Description | Example |
|------|----------|-------------|---------|
| `subfinder` | recon/dns | Subdomain discovery | `secator x subfinder target.com` |
| `dnsx` | recon/dns | DNS toolkit | `secator x dnsx target.com -a -cname -txt` |
| `dnsxbrute` | recon/dns | DNS brute force | `secator x dnsxbrute target.com -w subdomains.txt` |
| `httpx` | http | HTTP prober | `secator x httpx target.com -td -ss` |
| `fping` | recon/ip | Alive host discovery | `secator x fping 10.0.0.0/24` |
| `mapcidr` | recon/ip | CIDR expansion | `secator x mapcidr 10.0.0.0/16` |
| `naabu` | recon/port | Port discovery | `secator x naabu target.com -p-` |
| `maigret` | recon/user | User account hunting | `secator x maigret username` |

### Crawler Tasks

| Task | Category | Description | Example |
|------|----------|-------------|---------|
| `katana` | http/crawler | Next-gen crawler | `secator x katana target.com -jc -js-crawl -d 5` |
| `gospider` | http/crawler | Fast web spider | `secator x gospider target.com` |
| `cariddi` | http/crawler | Crawler + secrets matcher | `secator x cariddi target.com -s -e` |
| `gau` | http/crawler | Offline URL crawler | `secator x gau target.com` |

### Fuzzer Tasks

| Task | Category | Description | Example |
|------|----------|-------------|---------|
| `ffuf` | http/fuzzer | Fast web fuzzer | `secator x ffuf https://target.com/FUZZ -w wordlist.txt` |
| `feroxbuster` | http/fuzzer | Recursive content discovery | `secator x feroxbuster https://target.com` |
| `dirsearch` | http/fuzzer | Web path discovery | `secator x dirsearch https://target.com` |

### Vulnerability Scanner Tasks

| Task | Category | Description | Example |
|------|----------|-------------|---------|
| `nuclei` | vuln/multi | YAML-based vuln scanner | `secator x nuclei target.com -tags cve -severity critical,high` |
| `nmap` | vuln/multi | Network scanner with NSE | `secator x nmap target.com -sV --script vuln` |
| `dalfox` | vuln/http | XSS scanner | `secator x dalfox https://target.com` |
| `wpscan` | vuln/multi | WordPress scanner | `secator x wpscan target.com -e ap,at` |
| `msfconsole` | vuln/http | Metasploit CLI | `secator x msfconsole -x "use exploit/..."` |
| `grype` | vuln/code | Container/filesystem vuln scanner | `secator x grype /path/to/code` |

### OSINT Tasks

| Task | Category | Description | Example |
|------|----------|-------------|---------|
| `h8mail` | osint | Email breach hunting | `secator x h8mail user@target.com` |

### Tagging Tasks

| Task | Category | Description | Example |
|------|----------|-------------|---------|
| `gf` | tagger | Pattern-based grep | `secator x gf target.com` |

---

## Workflows (secator w)

### Predefined Workflows

| Workflow | Description | Example |
|----------|-------------|---------|
| `host_recon` | Open ports + network + HTTP vulns | `secator w host_recon 192.168.1.18` |
| `subdomain_recon` | Subdomain + root URLs | `secator w subdomain_recon target.com` |
| `url_crawl` | URL crawling | `secator w url_crawl https://target.com/` |
| `url_fuzz` | URL fuzzing | `secator w url_fuzz https://target.com/` |
| `code_scan` | Code vulnerability scan | `secator w code_scan /path/to/repo` |
| `user_hunt` | User account hunting | `secator w user_hunt username` |

### Piping Tasks
```bash
# Chain subfinder output into httpx
secator x subfinder -raw target.com | secator x httpx -rl 10 -ss
```

---

## Scans (secator s)

| Scan | Description | Example |
|------|-------------|---------|
| `domain` | Full domain assessment | `secator s domain target.com` |
| `subdomain` | Subdomain assessment | `secator s subdomain sub.target.com` |
| `network` | Network assessment | `secator s network 10.0.0.0/24` |
| `url` | URL assessment | `secator s url https://target.com` |

---

## Global Options

| Option | Description |
|--------|-------------|
| `-json` | JSON output |
| `-jsonl` | JSON lines output |
| `-txt` | Plain text output |
| `-csv` | CSV output |
| `-table` | Table output |
| `-o DIR` | Output directory |
| `-rl N` | Rate limit (requests/second) |
| `-threads N` | Thread count |
| `-proxy URL` | Proxy URL (e.g., socks5://127.0.0.1:9050) |
| `-timeout N` | Timeout in seconds |
| `-mc CODES` | Match HTTP status codes |
| `-fc CODES` | Filter HTTP status codes |
| `-quiet` | Quiet mode |
| `-ss` | Take screenshots |
| `-w PATH` | Custom wordlist |

---

## Python Library Usage

### Running Tasks Programmatically
```python
from secator.tasks import subfinder, httpx, nuclei, nmap, naabu

# Simple task
results = subfinder('target.com').run()
for r in results:
    print(r)

# Consuming results live (realtime)
for result in httpx(['target.com'], rate_limit=10, screenshot=True):
    print(result)

# Accessing typed results
hosts = [r.host for r in results if r._type == 'subdomain']
```

### Running Workflows Programmatically
```python
from secator.workflows import host_recon, subdomain_recon, url_fuzz

# Live result consumption
for result in host_recon('target.com'):
    print(f"[{result._type}] {result}")

# With exporters
for result in host_recon('target.com', exporters=['table']):
    pass  # Results printed + summary table at end
```

### Custom Configuration
```python
from secator.workflows import url_fuzz

opts = {
    'match_codes': '200, 302',
    'rate_limit': 1,
    'ffuf.wordlist': 'custom-wordlist.txt',
    'quiet': True,
}

for result in url_fuzz('target.com', exporters=['table'], **opts):
    print(result)
```

---

## Utilities (secator u)

| Utility | Description | Example |
|---------|-------------|---------|
| `proxy` | Get random proxy | `secator u proxy -n 5` |
| `revshell` | Reverse shell generator | `secator u revshell bash -h LHOST -p LPORT -l` |
| `serve` | HTTP payload server | `secator u serve` |
| `record` | Session recording | `secator u record -i session_name` |

---

## Configuration

```bash
secator c get                  # Full config with defaults
secator c get --user           # User config
secator c get wordlists.defaults.http   # Specific config key
secator c set wordlists.defaults.http rockyou.txt  # Set config key
secator c edit                # Edit user config YAML
secator c default             # Default config
```

---

## Distributed Execution

```bash
# Start Celery worker
secator install addons worker
secator worker

# All tasks/workflows/scans automatically route to workers
secator s domain target.com   # Runs distributed
```

## Output Types

Secator normalizes output across all tools into unified types:

| Type | Description |
|------|-------------|
| `subdomain` | Discovered subdomain |
| `url` | Discovered URL |
| `port` | Open port |
| `vulnerability` | Found vulnerability |
| `info` | Informational finding |
| `tag` | Tagged pattern match |

## VAPT Integration Patterns

### Full Blackbox External Assessment
```bash
secator s domain target.com -json -o /tmp/vapt/target-com/
secator s network 10.0.0.0/24 -json -o /tmp/vapt/target-network/
```

### Targeted Vulnerability Scan
```bash
secator x nuclei target.com -tags cve,exposure,misconfig -severity critical,high,medium -json
```

### Web Application Deep Scan
```bash
secator w url_crawl https://target.com/ -json -o /tmp/vapt/crawl/
secator w url_fuzz https://target.com/ -mc 200,302 -json -o /tmp/vapt/fuzz/
secator x dalfox https://target.com -b https://callback.example.com -json
```

### Python Orchestration
```python
from secator.tasks import subfinder, httpx, nuclei, naabu, nmap

# Phase 1: Recon
subs = subfinder('target.com').run()
hosts = [h.host for h in subs if h._type == 'subdomain']

# Phase 2: Probing
probed = []
for r in httpx(hosts, rate_limit=10, screenshot=True):
    probed.append(r)

# Phase 3: Port scanning
for r in naabu('target.com', ports='80,443,445,3389'):
    print(f"Open port: {r.port}")

# Phase 4: Vulnerability scanning
for vuln in nuclei('target.com', tags='cve', severity='critical,high'):
    print(f"Vulnerability: {vuln.name} [{vuln.severity}]")
```