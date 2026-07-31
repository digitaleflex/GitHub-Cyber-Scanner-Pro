# CasperPro Discovery Module

> Traffic Interception and API Discovery using mitmproxy + Playwright

## Overview

The discovery phase uses mitmproxy to intercept all traffic while Playwright automates browser interactions. This combination reveals hidden APIs, authentication mechanisms, and application structure.

## mitmproxy Addon Scripts

### Basic Capture Addon

```python
# basic_capture.py
import json
import mitmproxy.http
from datetime import datetime

class BasicCapture:
    def __init__(self):
        self.output_file = "/tmp/traffic_capture.json"
        self.traffic = []
    
    def request(self, flow: mitmproxy.http.HTTPFlow):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "headers": dict(flow.request.headers),
            "body": flow.request.get_text() if flow.request.content else None,
            "content_type": flow.request.headers.get("content-type", "")
        }
        self.traffic.append(entry)
        self._save()
    
    def response(self, flow: mitmproxy.http.HTTPFlow):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "url": flow.request.pretty_url,
            "status_code": flow.response.status_code,
            "headers": dict(flow.response.headers),
            "body_size": len(flow.response.content) if flow.response.content else 0,
            "content_type": flow.response.headers.get("content-type", "")
        }
        self.traffic.append(entry)
        self._save()
    
    def _save(self):
        with open(self.output_file, "w") as f:
            json.dump(self.traffic, f, indent=2)

addons = [BasicCapture()]
```

### Advanced API Discovery Addon

```python
# api_discovery.py
import json
import re
import mitmproxy.http
from urllib.parse import urlparse, parse_qs

class APIDiscovery:
    def __init__(self):
        self.apis = {}
        self.tokens = []
        self.graphql_schemas = []
        
    def request(self, flow: mitmproxy.http.HTTPFlow):
        url = flow.request.pretty_url
        parsed = urlparse(url)
        
        # Detect API endpoints
        api_patterns = [
            r'/api/',
            r'/v\d+/',
            r'/graphql',
            r'/rest/',
            r'/ajax/',
            r'/json/',
            r'/rpc/'
        ]
        
        is_api = any(re.search(p, url.lower()) for p in api_patterns)
        
        if is_api:
            endpoint_key = f"{flow.request.method} {parsed.path}"
            
            if endpoint_key not in self.apis:
                self.apis[endpoint_key] = {
                    "method": flow.request.method,
                    "path": parsed.path,
                    "host": parsed.netloc,
                    "params": list(parse_qs(parsed.query).keys()),
                    "headers": {},
                    "body_format": None,
                    "samples": []
                }
            
            # Track headers of interest
            for h in ["Authorization", "X-API-Key", "X-Auth-Token", "Cookie"]:
                if h in flow.request.headers:
                    self.apis[endpoint_key]["headers"][h] = flow.request.headers[h]
                    
                    # Extract tokens
                    if h == "Authorization":
                        self.tokens.append({
                            "type": "bearer" if "Bearer" in flow.request.headers[h] else "other",
                            "value": flow.request.headers[h],
                            "endpoint": url
                        })
            
            # Detect body format
            content_type = flow.request.headers.get("content-type", "")
            if "json" in content_type:
                self.apis[endpoint_key]["body_format"] = "json"
                if flow.request.content:
                    try:
                        body = json.loads(flow.request.get_text())
                        self.apis[endpoint_key]["samples"].append(body)
                        
                        # Detect GraphQL
                        if "query" in body or "mutation" in body:
                            self.graphql_schemas.append({
                                "endpoint": url,
                                "query": body.get("query", ""),
                                "variables": body.get("variables", {})
                            })
                    except:
                        pass
            elif "form" in content_type:
                self.apis[endpoint_key]["body_format"] = "form"
            elif "xml" in content_type:
                self.apis[endpoint_key]["body_format"] = "xml"
        
        self._save()
    
    def _save(self):
        output = {
            "apis": list(self.apis.values()),
            "tokens": self.tokens,
            "graphql": self.graphql_schemas
        }
        with open("/tmp/api_discovery.json", "w") as f:
            json.dump(output, f, indent=2)

addons = [APIDiscovery()]
```

### Security Header Analysis Addon

```python
# security_headers.py
import json
import mitmproxy.http

class SecurityHeaderAnalysis:
    def __init__(self):
        self.findings = []
        self.checked_hosts = set()
        
        self.security_headers = {
            "Strict-Transport-Security": {
                "severity": "medium",
                "description": "HSTS not set - vulnerable to protocol downgrade"
            },
            "X-Content-Type-Options": {
                "severity": "low",
                "description": "X-Content-Type-Options not set - MIME sniffing possible"
            },
            "X-Frame-Options": {
                "severity": "medium",
                "description": "X-Frame-Options not set - clickjacking possible"
            },
            "Content-Security-Policy": {
                "severity": "medium",
                "description": "CSP not set - XSS mitigation missing"
            },
            "X-XSS-Protection": {
                "severity": "low",
                "description": "X-XSS-Protection not set"
            },
            "Referrer-Policy": {
                "severity": "low",
                "description": "Referrer-Policy not set - referrer leakage possible"
            }
        }
    
    def response(self, flow: mitmproxy.http.HTTPFlow):
        host = flow.request.host
        
        if host in self.checked_hosts:
            return
        
        self.checked_hosts.add(host)
        
        for header, info in self.security_headers.items():
            if header not in flow.response.headers:
                self.findings.append({
                    "host": host,
                    "url": flow.request.pretty_url,
                    "missing_header": header,
                    "severity": info["severity"],
                    "description": info["description"]
                })
        
        # Check for sensitive headers in response
        sensitive_headers = ["Server", "X-Powered-By", "X-AspNet-Version"]
        for h in sensitive_headers:
            if h in flow.response.headers:
                self.findings.append({
                    "host": host,
                    "url": flow.request.pretty_url,
                    "exposed_header": h,
                    "value": flow.response.headers[h],
                    "severity": "info",
                    "description": f"Server information disclosure via {h} header"
                })
        
        self._save()
    
    def _save(self):
        with open("/tmp/security_headers.json", "w") as f:
            json.dump(self.findings, f, indent=2)

addons = [SecurityHeaderAnalysis()]
```

## Playwright Discovery Scripts

### Full Application Crawl

```python
# full_crawl.py
from playwright.sync_api import sync_playwright
import json
import time

class ApplicationCrawler:
    def __init__(self, target, proxy_port=8082):
        self.target = target
        self.proxy_port = proxy_port
        self.visited = set()
        self.forms = []
        self.api_calls = []
        
    def crawl(self, max_pages=50):
        with sync_playwright() as p:
            browser = p.chromium.launch(
                proxy={"server": f"http://127.0.0.1:{self.proxy_port}"},
                headless=True
            )
            context = browser.new_context(ignore_https_errors=True)
            
            # Intercept network requests
            page = context.new_page()
            page.on("request", self._on_request)
            page.on("response", self._on_response)
            
            # Start crawling
            self._crawl_page(page, self.target, max_pages)
            
            # Save results
            self._save_results()
            
            browser.close()
    
    def _crawl_page(self, page, url, remaining):
        if remaining <= 0 or url in self.visited:
            return
        
        if not url.startswith(self.target):
            return
        
        self.visited.add(url)
        
        try:
            page.goto(url, timeout=10000)
            page.wait_for_load_state("networkidle", timeout=5000)
        except:
            return
        
        # Extract forms
        forms = page.query_selector_all("form")
        for form in forms:
            form_data = {
                "url": url,
                "action": form.get_attribute("action") or url,
                "method": form.get_attribute("method") or "GET",
                "inputs": []
            }
            
            inputs = form.query_selector_all("input, select, textarea")
            for inp in inputs:
                form_data["inputs"].append({
                    "name": inp.get_attribute("name"),
                    "type": inp.get_attribute("type"),
                    "id": inp.get_attribute("id")
                })
            
            self.forms.append(form_data)
        
        # Extract links
        links = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.href)"
        )
        
        for link in links:
            self._crawl_page(page, link, remaining - 1)
    
    def _on_request(self, request):
        if "/api/" in request.url or "graphql" in request.url:
            self.api_calls.append({
                "url": request.url,
                "method": request.method,
                "headers": request.headers,
                "post_data": request.post_data
            })
    
    def _on_response(self, response):
        pass
    
    def _save_results(self):
        results = {
            "target": self.target,
            "pages_visited": len(self.visited),
            "visited_urls": list(self.visited),
            "forms": self.forms,
            "api_calls": self.api_calls
        }
        
        with open("/tmp/crawl_results.json", "w") as f:
            json.dump(results, f, indent=2)

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    crawler = ApplicationCrawler(target)
    crawler.crawl()
```

### Authentication Flow Capture

```python
# auth_capture.py
from playwright.sync_api import sync_playwright
import json

def capture_auth_flow(target, login_url, username, password, 
                      username_selector, password_selector, submit_selector,
                      proxy_port=8082):
    """
    Capture the full authentication flow including tokens
    """
    auth_data = {
        "cookies": [],
        "local_storage": {},
        "session_storage": {},
        "tokens": [],
        "requests": []
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            proxy={"server": f"http://127.0.0.1:{proxy_port}"},
            headless=False  # Set to True for automation
        )
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        # Capture all requests
        def on_request(request):
            if any(x in request.url for x in ["login", "auth", "token", "session"]):
                auth_data["requests"].append({
                    "url": request.url,
                    "method": request.method,
                    "headers": dict(request.headers),
                    "post_data": request.post_data
                })
        
        page.on("request", on_request)
        
        # Navigate to login page
        page.goto(login_url)
        page.wait_for_load_state("networkidle")
        
        # Fill credentials
        page.fill(username_selector, username)
        page.fill(password_selector, password)
        
        # Submit
        page.click(submit_selector)
        page.wait_for_load_state("networkidle")
        
        # Wait for redirect/response
        time.sleep(2)
        
        # Capture cookies
        auth_data["cookies"] = context.cookies()
        
        # Capture storage
        auth_data["local_storage"] = page.evaluate(
            "() => Object.fromEntries(Object.entries(localStorage))"
        )
        auth_data["session_storage"] = page.evaluate(
            "() => Object.fromEntries(Object.entries(sessionStorage))"
        )
        
        # Extract tokens from storage
        for key, value in auth_data["local_storage"].items():
            if any(x in key.lower() for x in ["token", "auth", "jwt", "session"]):
                auth_data["tokens"].append({
                    "source": "localStorage",
                    "key": key,
                    "value": value
                })
        
        for cookie in auth_data["cookies"]:
            if any(x in cookie["name"].lower() for x in ["token", "auth", "session", "jwt"]):
                auth_data["tokens"].append({
                    "source": "cookie",
                    "key": cookie["name"],
                    "value": cookie["value"]
                })
        
        # Save results
        with open("/tmp/auth_capture.json", "w") as f:
            json.dump(auth_data, f, indent=2)
        
        browser.close()
        
    return auth_data

if __name__ == "__main__":
    import time
    # Example usage
    auth = capture_auth_flow(
        target="https://example.com",
        login_url="https://example.com/login",
        username="testuser",
        password="testpass",
        username_selector='input[name="email"]',
        password_selector='input[name="password"]',
        submit_selector='button[type="submit"]'
    )
    print(json.dumps(auth, indent=2))
```

## Analysis Scripts

### Traffic Analysis

```bash
# Analyze captured traffic
cat /tmp/traffic_capture.json | jq '
  [.[] | select(.type == "request")] | 
  group_by(.method) | 
  map({method: .[0].method, count: length})
'

# Find all unique endpoints
cat /tmp/traffic_capture.json | jq -r '
  [.[] | select(.type == "request") | .url] | 
  unique | 
  .[]
' | sort

# Extract all authentication headers
cat /tmp/traffic_capture.json | jq '
  [.[] | select(.type == "request") | 
   select(.headers.Authorization != null or .headers.Cookie != null) |
   {url: .url, auth: .headers.Authorization, cookie: .headers.Cookie}]
'

# Find GraphQL operations
cat /tmp/traffic_capture.json | jq '
  [.[] | select(.type == "request") | 
   select(.url | contains("graphql")) |
   {url: .url, body: .body}]
'
```

### Generate curl Commands from Captured Traffic

```python
# generate_curl.py
import json
import shlex

def generate_curl_command(request):
    """Convert a captured request to a curl command"""
    cmd = ["curl", "-s"]
    
    # Method
    if request["method"] != "GET":
        cmd.extend(["-X", request["method"]])
    
    # Headers
    for key, value in request.get("headers", {}).items():
        # Skip some headers
        if key.lower() in ["host", "content-length", "connection"]:
            continue
        cmd.extend(["-H", f"{key}: {value}"])
    
    # Body
    if request.get("body"):
        cmd.extend(["-d", request["body"]])
    
    # URL
    cmd.append(request["url"])
    
    return " ".join(shlex.quote(c) for c in cmd)

# Load captured requests
with open("/tmp/traffic_capture.json") as f:
    traffic = json.load(f)

requests = [t for t in traffic if t["type"] == "request"]

# Generate curl commands
for req in requests:
    if "/api/" in req["url"]:
        print(f"# {req['method']} {req['url']}")
        print(generate_curl_command(req))
        print()
```

## Startup Commands

### Quick Start

```bash
# Terminal 1: Start mitmproxy with API discovery
mitmdump -p 8082 --set block_global=false -s api_discovery.py

# Terminal 2: Run Playwright crawler
uv run full_crawl.py https://target.com

# Terminal 3: Analyze results
cat /tmp/api_discovery.json | jq '.apis[] | {method, path}'
```

### Full Discovery Pipeline

```bash
#!/bin/bash
# discovery_pipeline.sh

TARGET=$1
PROXY_PORT=8082

# Start mitmproxy in background
mitmdump -p $PROXY_PORT --set block_global=false -s api_discovery.py &
MITM_PID=$!
sleep 2

# Run crawler
uv run full_crawl.py $TARGET

# Stop mitmproxy
kill $MITM_PID

# Generate report
echo "=== Discovery Report ==="
echo "APIs Found:"
cat /tmp/api_discovery.json | jq -r '.apis[] | "\(.method) \(.path)"'
echo ""
echo "Tokens Found:"
cat /tmp/api_discovery.json | jq -r '.tokens[] | "\(.type): \(.value[:50])..."'
echo ""
echo "GraphQL Queries:"
cat /tmp/api_discovery.json | jq -r '.graphql[] | .query[:100]'
```

## Output Files

| File | Description |
|------|-------------|
| `/tmp/traffic_capture.json` | Raw traffic capture |
| `/tmp/api_discovery.json` | Discovered APIs, tokens, GraphQL |
| `/tmp/security_headers.json` | Missing security headers |
| `/tmp/crawl_results.json` | Crawled pages, forms, API calls |
| `/tmp/auth_capture.json` | Authentication flow data |

---

**Next Step:** Use the discovered APIs and tokens with **casperpro-business-logic.md** to test for IDOR and access control vulnerabilities, or **casperpro-injection-advanced.md** for injection testing.
