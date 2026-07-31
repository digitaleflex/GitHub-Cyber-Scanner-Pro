# False-Positive Resistance & Verification Procedures

Every finding MUST be independently verified before inclusion in the final report. This document defines the multi-method verification framework that eliminates false positives and ensures every reported vulnerability is confirmed exploitable.

## Verification Principles

1. **Two-method minimum**: Every finding requires confirmation from at least 2 independent methods
2. **Reproduce before report**: If you cannot reproduce it, do not report it
3. **Impact demonstration**: Show what an attacker can actually achieve, not just theoretical possibility
4. **Evidence chain**: Maintain timestamps, raw output, screenshots, and command logs
5. **Hash integrity**: SHA-256 hash all evidence files at collection time

## Verification Framework

### Level 1: Automated Scanner → Manual Confirmation
```
Scanner Finding → Manual Reproduction → Documented
```

### Level 2: Tool A → Tool B → Cross-Validation
```
Nuclei Finding → curl/Burp Replay → Match → Confirmed
Nmap Vuln Script → Manual Exploit → Shell Obtained → Confirmed
```

### Level 3: Exploit → Re-Exploit → Consistent Result
```
Initial Exploit → Clean Environment → Re-Exploit → Same Result → Confirmed
```

---

## Verification Procedures by Vulnerability Class

### SQL Injection Verification

**Method 1 (Scanner)**:
```bash
secator x nuclei target.com -tags sqli -severity critical
```

**Method 2 (Manual curl)**:
```bash
# True condition
curl -s "https://target.com/api/users?id=1' OR '1'='1" | python3 -m json.tool
# False condition
curl -s "https://target.com/api/users?id=1' OR '1'='2" | python3 -m json.tool
# If true returns different results than false: CONFIRMED
```

**Method 3 (Python verification)**:
```python
import requests

def verify_sqli(url, param):
    """Triple-verify SQLi with true/false/time-based conditions."""
    results = {}
    
    # Test 1: Boolean-based
    r_normal = requests.get(f"{url}?{param}=1")
    r_true = requests.get(f"{url}?{param}=1' OR '1'='1")
    r_false = requests.get(f"{url}?{param}=1' OR '1'='2")
    
    results['boolean'] = (
        len(r_true.text) != len(r_false.text) and
        len(r_true.text) != len(r_normal.text)
    )
    
    # Test 2: Error-based
    r_error = requests.get(f"{url}?{param}=1'")
    results['error'] = any(x in r_error.text.lower() for x in 
        ['sql', 'mysql', 'postgresql', 'syntax error', 'ora-', 'microsoft sql'])
    
    # Test 3: Time-based (5 second delay)
    import time
    start = time.time()
    requests.get(f"{url}?{param}=1'; WAITFOR DELAY '0:0:5'--")
    elapsed = time.time() - start
    results['time_based'] = elapsed >= 4.5
    
    # CONFIRMED if 2+ methods positive
    confirmed = sum(results.values()) >= 2
    return confirmed, results

confirmed, details = verify_sqli("https://target.com/api/users", "id")
print(f"SQLi Confirmed: {confirmed}, Methods: {details}")
```

**Confidence Levels**:
- 3/3 methods positive → **Critical** (confirmed, exploitable)
- 2/3 methods positive → **High** (confirmed, likely exploitable)
- 1/3 methods positive → **Medium** (suspicious, needs investigation)
- 0/3 methods positive → **Discard** (false positive)

---

### XSS Verification

**Method 1 (Scanner)**:
```bash
secator x dalfox https://target.com/search?q=FUZZ -b https://callback.example.com
```

**Method 2 (Manual browser test)**:
```bash
# Test in actual browser with DevTools open
# Navigate to: https://target.com/search?q=<script>alert(document.domain)</script>
# Expected: Alert box with domain name
```

**Method 3 (curl + response analysis)**:
```python
import requests
import html

def verify_xss(url, param, payload):
    """Verify XSS by checking if payload appears unescaped in response."""
    r = requests.get(f"{url}?{param}={payload}")
    
    # Check 1: Payload appears unescaped
    raw_present = payload in r.text
    
    # Check 2: Payload appears in dangerous context (inside script, event handler)
    in_script = f"<script>{payload}</script>" in r.text.lower()
    in_event = any(f"on{e}=" in r.text.lower() for e in 
        ['click','load','error','mouseover','focus','blur'])
    
    # Check 3: Compare with HTML-escaped version
    escaped = html.escape(payload)
    escaped_present = escaped in r.text
    not_escaped = raw_present and not escaped_present
    
    confirmed = raw_present and not_escaped
    return confirmed, {
        'raw_in_response': raw_present,
        'in_script_context': in_script,
        'in_event_handler': in_event,
        'properly_escaped': escaped_present
    }

confirmed, details = verify_xss(
    "https://target.com/search", "q", 
    '<script>alert(document.domain)</script>'
)
print(f"XSS Confirmed: {confirmed}, Details: {details}")
```

---

### Authentication Bypass Verification

**Method 1 (Scanner)**:
```bash
secator x nuclei target.com -tags auth-bypass
```

**Method 2 (Manual curl)**:
```bash
# Test 1: Default credentials
curl -v -u admin:admin https://target.com/api/dashboard

# Test 2: JWT none algorithm
curl -s -H "Authorization: Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4ifQ." https://target.com/api/dashboard

# Test 3: Force browsing
curl -s https://target.com/admin/dashboard -H "Cookie: session=standard_user_session"
```

**Method 3 (Python automation)**:
```python
import requests

def verify_auth_bypass(base_url, user_token, admin_path):
    """Verify authentication bypass on admin paths."""
    findings = []
    
    # Test with no auth
    r_noauth = requests.get(f"{base_url}{admin_path}")
    if r_noauth.status_code == 200:
        findings.append("No authentication required for admin path")
    
    # Test with standard user
    r_user = requests.get(f"{base_url}{admin_path}", 
        headers={"Authorization": f"Bearer {user_token}"})
    if r_user.status_code == 200:
        findings.append("Standard user can access admin path")
    
    # Test HTTP method bypass
    for method in ['PUT', 'PATCH', 'DELETE', 'OPTIONS']:
        r = requests.request(method, f"{base_url}{admin_path}",
            headers={"Authorization": f"Bearer {user_token}"})
        if r.status_code == 200:
            findings.append(f"Method {method} bypasses auth")
    
    return len(findings) > 0, findings
```

---

### SMB/Network Vulnerability Verification

**Method 1 (NetExec scan)**:
```bash
nxc smb target -u '' -p '' -M ms17-010
nxc smb target -u '' -p '' -M enum_vulnerability
```

**Method 2 (Nmap NSE)**:
```bash
nmap --script smb-vuln-ms17-010 target -p 445
```

**Method 3 (Metasploit check)**:
```bash
msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS target; check"
```

**Confirmation Matrix**:

| NetExec | Nmap | MSF Check | Result |
|---------|------|-----------|--------|
| ✅ | ✅ | ✅ | **CONFIRMED** — Report as finding |
| ✅ | ✅ | ❌ | **Likely** — Investigate version/patch level |
| ✅ | ❌ | ❌ | **Suspicious** — Verify target OS version |
| ❌ | ✅ | ❌ | **Suspicious** — Re-run NetExec with verbose |
| ❌ | ❌ | ✅ | **Suspicious** — Verify scanner versions |

---

### Port/Service Verification

**Method 1 (Nmap)**:
```bash
nmap -sV -p PORT target
```

**Method 2 (Raw Python socket)**:
```python
import socket

def verify_port(host, port, timeout=5):
    """Raw socket verification independent of nmap."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((host, port))
        if result == 0:
            # Grab banner
            s.send(b"HEAD / HTTP/1.0\r\n\r\n")
            banner = s.recv(1024).decode('utf-8', errors='ignore')
            s.close()
            return True, banner
        s.close()
        return False, ""
    except Exception as e:
        return False, str(e)

open, banner = verify_port("target", 443)
print(f"Port 443: Open={open}, Banner={banner[:100]}")
```

**Method 3 (curl for HTTP)**:
```bash
curl -sI https://target:PORT/ -m 5
```

---

### Vulnerability Scanner False Positive Patterns

Common false positives from automated scanners and how to eliminate them:

| Scanner | False Positive Type | Elimination Method |
|---------|---------------------|-------------------|
| Nuclei | Template mismatch on custom app | Manually replay request; compare with known-good response |
| Nmap NSE | Script timeout interpreted as vulnerable | Run with `--script-timeout 30s`; verify with Metasploit `check` |
| Dalfox | DOM XSS in non-executable context | Test in browser with DevTools; check if payload fires |
| nikto | Default file in custom app | Verify file actually serves content (not custom 404) |
| wpscan | Plugin version mismatch | Verify plugin is actually installed and active |

### Nuclei False Positive Reduction
```bash
# Use severity filtering
secator x nuclei target.com -severity critical,high -tags cve

# Use interactive mode for verification
nuclei -t cves/ -u target.com -interactsh-url https://interactsh.com

# Compare against known false positive patterns
# Check nuclei template for verification method (e.g., DNS interaction, HTTP interaction)
```

---

## Evidence Collection Standards

### Required Evidence Per Finding

1. **Raw Tool Output** (timestamped)
   ```bash
   date +%Y-%m-%dT%H:%M:%S%z > evidence/timestamp.txt
   nxc smb target -u admin -p 'P@ss' --shares 2>&1 | tee evidence/smb-shares-raw.txt
   ```

2. **Screenshots** (with visible URL/IP and timestamp)
   ```bash
   # macOS
   screencapture -x evidence/screenshot-$(date +%s).png
   # Linux
   import -window root evidence/screenshot-$(date +%s).png
   ```

3. **Command Log**
   ```bash
   script evidence/session-$(date +%Y%m%d).log
   # ... run all commands ...
   exit
   ```

4. **Network Capture** (when applicable)
   ```bash
   tcpdump -i any host target -w evidence/capture-$(date +%Y%m%d).pcap
   ```

5. **Evidence Integrity**
   ```bash
   # Hash all evidence files
   find evidence/ -type f -exec sh -c 'sha256sum "$1" > "$1.sha256"' _ {} \;
   ```

### Evidence Redaction

- **Never** include full password hashes in reports — show first 8 chars + `...`
- **Never** include full credit card numbers or PII
- **Always** redact sensitive data: `P@ssw0rd` → `P@ss****`
- **Mark** all evidence with finding ID for traceability

---

## Verification Checklist (Per Finding)

Before adding any finding to the report, complete this checklist:

- [ ] **Reproduced**: Finding reproduced at least 2 times
- [ ] **Two-method**: Confirmed by 2+ independent methods
- [ ] **Impact shown**: Demonstrated what attacker can achieve (not just "vulnerable")
- [ ] **Scope confirmed**: Target is within authorized assessment scope
- [ ] **Raw output captured**: Tool output saved with timestamps
- [ ] **Screenshots taken**: Visual evidence of exploitation
- [ ] **Evidence hashed**: SHA-256 hashes computed for all evidence files
- [ ] **Remediation documented**: Step-by-step fix instructions with exact commands
- [ ] **Verification of fix**: How to confirm remediation is effective
- [ ] **CVSS scored**: Proper CVSS v3.1 calculation with justification
- [ ] **No PII**: Sensitive data redacted from evidence