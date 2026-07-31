# CasperPro Advanced API Testing Module

> GraphQL, WebSocket, gRPC, and Modern API Security Assessment

## Overview

This module covers comprehensive security testing for modern API architectures including GraphQL, WebSocket, gRPC, and emerging protocols.

---

## 1. Advanced GraphQL Security Testing

### GraphQL Introspection & Schema Analysis

```python
# graphql_security.py
import subprocess
import json
from typing import Dict, List, Optional

class GraphQLSecurityTester:
    """Comprehensive GraphQL security testing"""
    
    def __init__(self, endpoint: str, token: str = None):
        self.endpoint = endpoint
        self.token = token
        self.schema = None
        self.findings = []
    
    def curl(self, query: str, variables: Dict = None) -> Dict:
        """Execute GraphQL query"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        cmd = [
            "curl", "-s", "-X", "POST",
            "-H", "Content-Type: application/json"
        ]
        
        if self.token:
            cmd.extend(["-H", f"Authorization: Bearer {self.token}"])
        
        cmd.extend(["-d", json.dumps(payload), self.endpoint])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        try:
            return json.loads(result.stdout)
        except:
            return {"error": result.stdout}
    
    # ==================
    # Introspection
    # ==================
    
    def full_introspection(self) -> Dict:
        """Perform full schema introspection"""
        query = """
        query IntrospectionQuery {
          __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
              ...FullType
            }
            directives {
              name
              description
              locations
              args {
                ...InputValue
              }
            }
          }
        }

        fragment FullType on __Type {
          kind
          name
          description
          fields(includeDeprecated: true) {
            name
            description
            args {
              ...InputValue
            }
            type {
              ...TypeRef
            }
            isDeprecated
            deprecationReason
          }
          inputFields {
            ...InputValue
          }
          interfaces {
            ...TypeRef
          }
          enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
          }
          possibleTypes {
            ...TypeRef
          }
        }

        fragment InputValue on __InputValue {
          name
          description
          type {
            ...TypeRef
          }
          defaultValue
        }

        fragment TypeRef on __Type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
              }
            }
          }
        }
        """
        
        print("[*] Performing full GraphQL introspection...")
        response = self.curl(query)
        
        if "data" in response and response["data"].get("__schema"):
            self.schema = response["data"]["__schema"]
            print(f"[+] Introspection successful")
            print(f"    Types: {len(self.schema.get('types', []))}")
            return self.schema
        else:
            print("[-] Introspection disabled or failed")
            return None
    
    def introspection_bypass(self) -> Dict:
        """Attempt to bypass introspection restrictions"""
        bypasses = [
            # Aliased introspection
            "query { __schema: __schema { types { name } } }",
            # Fragment-based
            "query { ...on __Schema { types { name } } }",
            # Whitespace variations
            "query{__schema{types{name}}}",
            # Case variations
            "query { __SCHEMA { types { name } } }",
            # GET request (sometimes allowed)
            "__schema { types { name } }",
            # Batched query
            "[{\"query\":\"{ __schema { types { name } } }\"}]",
        ]
        
        print("[*] Attempting introspection bypass...")
        
        for bypass in bypasses:
            response = self.curl(bypass)
            if "data" in response and "__schema" in str(response):
                print(f"[!] Introspection bypass successful!")
                return response
        
        return None
    
    # ==================
    # Authorization Testing
    # ==================
    
    def extract_sensitive_queries(self) -> List[Dict]:
        """Extract potentially sensitive queries from schema"""
        if not self.schema:
            self.full_introspection()
        
        if not self.schema:
            return []
        
        sensitive_keywords = [
            "admin", "user", "password", "secret", "token", "key",
            "credential", "auth", "permission", "role", "private",
            "internal", "delete", "remove", "update", "create"
        ]
        
        sensitive_fields = []
        
        for type_def in self.schema.get("types", []):
            if type_def["name"].startswith("__"):
                continue
            
            for field in type_def.get("fields", []) or []:
                field_name = field["name"].lower()
                type_name = type_def["name"].lower()
                
                if any(kw in field_name or kw in type_name for kw in sensitive_keywords):
                    sensitive_fields.append({
                        "type": type_def["name"],
                        "field": field["name"],
                        "args": field.get("args", []),
                        "return_type": self._get_type_name(field["type"])
                    })
        
        print(f"[+] Found {len(sensitive_fields)} potentially sensitive fields")
        return sensitive_fields
    
    def test_field_authorization(self, type_name: str, field_name: str, 
                                  args: Dict = None) -> Dict:
        """Test if a field is properly authorized"""
        # Build query dynamically
        args_str = ""
        if args:
            args_list = [f'{k}: "{v}"' if isinstance(v, str) else f'{k}: {v}' 
                        for k, v in args.items()]
            args_str = f"({', '.join(args_list)})"
        
        query = f"""
        query {{
            {field_name}{args_str} {{
                id
            }}
        }}
        """
        
        # Test without auth
        original_token = self.token
        self.token = None
        
        no_auth_response = self.curl(query)
        
        # Restore token
        self.token = original_token
        
        auth_response = self.curl(query)
        
        # Analyze responses
        result = {
            "field": field_name,
            "type": type_name,
            "no_auth_response": no_auth_response,
            "auth_response": auth_response,
            "vulnerable": False
        }
        
        if "data" in no_auth_response and no_auth_response["data"].get(field_name):
            result["vulnerable"] = True
            result["vulnerability"] = "Field accessible without authentication"
            self.findings.append({
                "type": "GraphQL Unauthorized Access",
                "severity": "HIGH",
                "field": field_name,
                "evidence": str(no_auth_response)[:500]
            })
        
        return result
    
    # ==================
    # Injection Testing
    # ==================
    
    def test_injection(self, field_name: str, arg_name: str) -> List[Dict]:
        """Test for injection vulnerabilities in GraphQL arguments"""
        findings = []
        
        payloads = {
            "sql": [
                "' OR '1'='1",
                "1; DROP TABLE users--",
                "1' UNION SELECT null--"
            ],
            "nosql": [
                '{"$ne": null}',
                '{"$gt": ""}',
                '{"$where": "sleep(5000)"}'
            ],
            "ssrf": [
                "http://169.254.169.254/latest/meta-data/",
                "http://localhost:22",
                "file:///etc/passwd"
            ]
        }
        
        for injection_type, tests in payloads.items():
            for payload in tests:
                query = f"""
                query {{
                    {field_name}({arg_name}: "{payload}") {{
                        id
                    }}
                }}
                """
                
                response = self.curl(query)
                
                # Check for injection indicators
                response_str = str(response).lower()
                
                if injection_type == "sql":
                    if any(x in response_str for x in ["sql", "syntax", "error"]):
                        findings.append({
                            "type": f"GraphQL {injection_type.upper()} Injection",
                            "severity": "CRITICAL",
                            "field": field_name,
                            "arg": arg_name,
                            "payload": payload
                        })
        
        return findings
    
    # ==================
    # DoS Testing
    # ==================
    
    def test_query_complexity(self) -> Dict:
        """Test for query complexity/depth limits"""
        print("[*] Testing query complexity limits...")
        
        # Deep nesting attack
        depths = [5, 10, 20, 50]
        results = []
        
        for depth in depths:
            # Build deeply nested query
            query = "query { users { "
            for i in range(depth):
                query += "friends { "
            query += "id " + "} " * depth + "} }"
            
            import time
            start = time.time()
            response = self.curl(query)
            elapsed = time.time() - start
            
            results.append({
                "depth": depth,
                "time": elapsed,
                "success": "errors" not in response
            })
            
            if elapsed > 5:
                print(f"[!] Query with depth {depth} took {elapsed:.2f}s")
        
        return {"depth_test": results}
    
    def test_batch_attack(self) -> Dict:
        """Test for batching attacks"""
        print("[*] Testing batch query limits...")
        
        # Create batched queries
        batch_sizes = [10, 50, 100, 500]
        results = []
        
        for size in batch_sizes:
            queries = [{"query": "{ __typename }"} for _ in range(size)]
            
            cmd = [
                "curl", "-s", "-X", "POST",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(queries),
                self.endpoint
            ]
            
            import time
            start = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True)
            elapsed = time.time() - start
            
            try:
                response = json.loads(result.stdout)
                success = isinstance(response, list) and len(response) == size
            except:
                success = False
            
            results.append({
                "batch_size": size,
                "time": elapsed,
                "success": success
            })
            
            if success:
                print(f"[!] Batch of {size} queries allowed")
        
        return {"batch_test": results}
    
    def test_field_duplication(self) -> Dict:
        """Test for field duplication attack"""
        print("[*] Testing field duplication...")
        
        # Duplicate fields many times
        duplicates = [10, 100, 1000]
        results = []
        
        for count in duplicates:
            fields = " ".join([f"field{i}: __typename" for i in range(count)])
            query = f"query {{ {fields} }}"
            
            import time
            start = time.time()
            response = self.curl(query)
            elapsed = time.time() - start
            
            results.append({
                "duplicates": count,
                "time": elapsed,
                "success": "errors" not in response
            })
        
        return {"duplication_test": results}
    
    # ==================
    # Information Disclosure
    # ==================
    
    def test_error_disclosure(self) -> Dict:
        """Test for verbose error messages"""
        print("[*] Testing error message disclosure...")
        
        test_queries = [
            "query { nonexistentField }",
            "query { __typename(invalid: true) }",
            "query { users { password } }",
            "mutation { deleteUser(id: \"invalid\") }",
        ]
        
        errors_found = []
        
        for query in test_queries:
            response = self.curl(query)
            
            if "errors" in response:
                for error in response["errors"]:
                    error_msg = error.get("message", "")
                    
                    # Check for sensitive information
                    if any(x in error_msg.lower() for x in 
                          ["stack", "trace", "sql", "database", "internal", "path", "file"]):
                        errors_found.append({
                            "query": query,
                            "error": error_msg
                        })
        
        return {"verbose_errors": errors_found}
    
    def test_field_suggestions(self) -> Dict:
        """Exploit field suggestions to enumerate schema"""
        print("[*] Testing field suggestions...")
        
        prefixes = ["user", "admin", "get", "create", "delete", "update", "list"]
        discovered = []
        
        for prefix in prefixes:
            query = f"query {{ {prefix}NONEXISTENT }}"
            response = self.curl(query)
            
            if "errors" in response:
                for error in response["errors"]:
                    msg = error.get("message", "")
                    
                    # Look for "Did you mean..." suggestions
                    if "did you mean" in msg.lower():
                        discovered.append({
                            "prefix": prefix,
                            "suggestions": msg
                        })
        
        return {"field_suggestions": discovered}
    
    # ==================
    # Helper Methods
    # ==================
    
    def _get_type_name(self, type_def: Dict) -> str:
        """Recursively get type name"""
        if type_def.get("name"):
            return type_def["name"]
        if type_def.get("ofType"):
            return self._get_type_name(type_def["ofType"])
        return "Unknown"
    
    def generate_report(self) -> Dict:
        """Generate security assessment report"""
        return {
            "endpoint": self.endpoint,
            "introspection_enabled": self.schema is not None,
            "findings": self.findings,
            "total_issues": len(self.findings)
        }
```

---

## 2. WebSocket Security Testing

### WebSocket Security Framework

```python
# websocket_security.py
import json
import ssl
import time
import threading
from typing import Dict, List, Callable, Optional

class WebSocketSecurityTester:
    """WebSocket security testing framework"""
    
    def __init__(self, url: str, token: str = None):
        self.url = url
        self.token = token
        self.messages = []
        self.findings = []
    
    def connect_with_playwright(self, intercept_callback: Callable = None):
        """Connect to WebSocket using Playwright for interception"""
        script = f'''
import asyncio
from playwright.async_api import async_playwright
import json

async def intercept_websocket():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        messages = []
        
        # Intercept WebSocket
        async def handle_websocket(ws):
            ws.on("framesent", lambda payload: messages.append({{"type": "sent", "data": payload}}))
            ws.on("framereceived", lambda payload: messages.append({{"type": "received", "data": payload}}))
        
        page.on("websocket", handle_websocket)
        
        # Navigate to page that uses WebSocket
        await page.goto("{self.url.replace('ws://', 'http://').replace('wss://', 'https://')}")
        
        # Wait for WebSocket activity
        await asyncio.sleep(5)
        
        # Save messages
        with open("/tmp/casperpro/websocket_messages.json", "w") as f:
            json.dump(messages, f, indent=2)
        
        await browser.close()

asyncio.run(intercept_websocket())
'''
        import subprocess
        subprocess.run(["uv", "run", "-c", script], capture_output=True)
        
        try:
            with open("/tmp/casperpro/websocket_messages.json") as f:
                return json.load(f)
        except:
            return []
    
    def test_authentication(self) -> Dict:
        """Test WebSocket authentication"""
        print("[*] Testing WebSocket authentication...")
        
        tests = []
        
        # Test 1: Connect without token
        tests.append({
            "test": "No authentication",
            "token": None,
            # Would attempt connection and check result
        })
        
        # Test 2: Invalid token
        tests.append({
            "test": "Invalid token",
            "token": "invalid_token_12345",
        })
        
        # Test 3: Expired token
        tests.append({
            "test": "Expired token",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjB9.xxx",
        })
        
        return {"authentication_tests": tests}
    
    def test_message_injection(self) -> List[Dict]:
        """Test for injection in WebSocket messages"""
        findings = []
        
        payloads = {
            "xss": [
                "<script>alert(1)</script>",
                "<img src=x onerror=alert(1)>",
            ],
            "sqli": [
                "' OR '1'='1",
                "1; DROP TABLE users--",
            ],
            "command": [
                "; cat /etc/passwd",
                "| id",
            ],
            "json_injection": [
                '{"__proto__": {"admin": true}}',
                '{"constructor": {"prototype": {"admin": true}}}',
            ]
        }
        
        for injection_type, tests in payloads.items():
            for payload in tests:
                # Would send via WebSocket and check response
                pass
        
        return findings
    
    def test_origin_validation(self) -> Dict:
        """Test for Cross-Site WebSocket Hijacking (CSWSH)"""
        print("[*] Testing origin validation...")
        
        origins = [
            "https://evil.com",
            "https://attacker.com",
            "null",
            "",
            "https://target.com.evil.com",
        ]
        
        results = []
        
        for origin in origins:
            # Would attempt WebSocket connection with spoofed Origin
            results.append({
                "origin": origin,
                # "connected": True/False
            })
        
        return {"origin_tests": results}
    
    def test_rate_limiting(self) -> Dict:
        """Test WebSocket message rate limiting"""
        print("[*] Testing WebSocket rate limiting...")
        
        # Would send many messages rapidly
        message_counts = [100, 500, 1000]
        results = []
        
        for count in message_counts:
            results.append({
                "messages": count,
                # "all_delivered": True/False,
                # "time": elapsed
            })
        
        return {"rate_limit_tests": results}
    
    def test_message_size(self) -> Dict:
        """Test for message size limits"""
        print("[*] Testing message size limits...")
        
        sizes = [1024, 10240, 102400, 1024000]  # 1KB, 10KB, 100KB, 1MB
        results = []
        
        for size in sizes:
            payload = "A" * size
            results.append({
                "size_bytes": size,
                # "accepted": True/False
            })
        
        return {"size_tests": results}
```

---

## 3. gRPC Security Testing

### gRPC Security Framework

```python
# grpc_security.py
import subprocess
import json
from typing import Dict, List, Optional

class GRPCSecurityTester:
    """gRPC security testing framework"""
    
    def __init__(self, host: str, port: int = 443, use_tls: bool = True):
        self.host = host
        self.port = port
        self.use_tls = use_tls
        self.services = []
        self.findings = []
    
    def grpcurl(self, args: List[str]) -> Dict:
        """Execute grpcurl command"""
        cmd = ["grpcurl"]
        
        if not self.use_tls:
            cmd.append("-plaintext")
        else:
            cmd.append("-insecure")
        
        cmd.extend(args)
        cmd.append(f"{self.host}:{self.port}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    
    # ==================
    # Reconnaissance
    # ==================
    
    def list_services(self) -> List[str]:
        """List all gRPC services"""
        print(f"[*] Listing gRPC services on {self.host}:{self.port}")
        
        result = self.grpcurl(["list"])
        
        if result["returncode"] == 0:
            self.services = result["stdout"].strip().split("\n")
            print(f"[+] Found {len(self.services)} services")
            return self.services
        else:
            print(f"[-] Failed to list services: {result['stderr']}")
            return []
    
    def describe_service(self, service: str) -> Dict:
        """Describe a gRPC service"""
        result = self.grpcurl(["describe", service])
        
        return {
            "service": service,
            "description": result["stdout"],
            "error": result["stderr"] if result["returncode"] != 0 else None
        }
    
    def describe_method(self, method: str) -> Dict:
        """Describe a gRPC method"""
        result = self.grpcurl(["describe", method])
        
        return {
            "method": method,
            "description": result["stdout"]
        }
    
    # ==================
    # Authentication Testing
    # ==================
    
    def test_no_auth(self, service: str, method: str, data: Dict = None) -> Dict:
        """Test method without authentication"""
        print(f"[*] Testing {service}/{method} without authentication")
        
        args = ["-d", json.dumps(data or {}), f"{service}/{method}"]
        result = self.grpcurl(args)
        
        vulnerable = result["returncode"] == 0 or "Unauthenticated" not in result["stderr"]
        
        if vulnerable:
            self.findings.append({
                "type": "gRPC Unauthenticated Access",
                "severity": "HIGH",
                "service": service,
                "method": method
            })
        
        return {
            "method": f"{service}/{method}",
            "vulnerable": vulnerable,
            "response": result["stdout"] or result["stderr"]
        }
    
    def test_metadata_auth_bypass(self, service: str, method: str) -> Dict:
        """Test for metadata-based auth bypass"""
        print(f"[*] Testing metadata auth bypass on {service}/{method}")
        
        bypass_metadata = [
            {"authorization": ""},
            {"authorization": "Bearer invalid"},
            {"x-api-key": ""},
            {"x-internal": "true"},
            {"x-forwarded-for": "127.0.0.1"},
        ]
        
        results = []
        
        for metadata in bypass_metadata:
            meta_args = []
            for k, v in metadata.items():
                meta_args.extend(["-H", f"{k}: {v}"])
            
            args = meta_args + ["-d", "{}", f"{service}/{method}"]
            result = self.grpcurl(args)
            
            results.append({
                "metadata": metadata,
                "success": result["returncode"] == 0
            })
        
        return {"bypass_tests": results}
    
    # ==================
    # Input Validation
    # ==================
    
    def test_injection(self, service: str, method: str, field: str) -> List[Dict]:
        """Test for injection in gRPC fields"""
        findings = []
        
        payloads = [
            "' OR '1'='1",
            "1; DROP TABLE users--",
            "../../../etc/passwd",
            "{{7*7}}",
            "; id",
        ]
        
        for payload in payloads:
            data = {field: payload}
            args = ["-d", json.dumps(data), f"{service}/{method}"]
            result = self.grpcurl(args)
            
            response = result["stdout"] + result["stderr"]
            
            # Check for injection indicators
            if any(x in response.lower() for x in ["sql", "error", "passwd", "49", "uid="]):
                findings.append({
                    "type": "gRPC Injection",
                    "method": f"{service}/{method}",
                    "field": field,
                    "payload": payload
                })
        
        return findings
    
    def test_large_payload(self, service: str, method: str, field: str) -> Dict:
        """Test for message size limits"""
        print(f"[*] Testing message size limits on {service}/{method}")
        
        sizes = [1024, 10240, 102400, 1024000]
        results = []
        
        for size in sizes:
            data = {field: "A" * size}
            args = ["-d", json.dumps(data), f"{service}/{method}"]
            result = self.grpcurl(args)
            
            results.append({
                "size": size,
                "success": result["returncode"] == 0,
                "error": result["stderr"][:200] if result["returncode"] != 0 else None
            })
        
        return {"size_tests": results}
    
    # ==================
    # Reflection Attack
    # ==================
    
    def test_reflection(self) -> Dict:
        """Test if server reflection is enabled"""
        print("[*] Testing gRPC reflection...")
        
        result = self.grpcurl(["list"])
        
        reflection_enabled = result["returncode"] == 0
        
        if reflection_enabled:
            self.findings.append({
                "type": "gRPC Reflection Enabled",
                "severity": "INFO",
                "description": "Server reflection allows schema discovery"
            })
        
        return {
            "reflection_enabled": reflection_enabled,
            "services": result["stdout"].split("\n") if reflection_enabled else []
        }
    
    # ==================
    # Enumeration
    # ==================
    
    def enumerate_all(self) -> Dict:
        """Enumerate all services and methods"""
        print("[*] Enumerating all gRPC services and methods...")
        
        enumeration = {}
        
        services = self.list_services()
        
        for service in services:
            if not service.strip():
                continue
            
            desc = self.describe_service(service)
            enumeration[service] = {
                "description": desc["description"],
                "methods": []
            }
            
            # Extract methods from description
            for line in desc["description"].split("\n"):
                if "rpc " in line:
                    method_name = line.strip().split(" ")[1].split("(")[0]
                    enumeration[service]["methods"].append(method_name)
        
        return enumeration
```

---

## 4. REST API Advanced Testing

### REST API Security Framework

```python
# rest_advanced.py
import subprocess
import json
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor

class RESTAdvancedTester:
    """Advanced REST API security testing"""
    
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.findings = []
    
    def curl(self, endpoint: str, method: str = "GET", 
             headers: Dict = None, data: str = None) -> Dict:
        """Execute REST API request"""
        url = f"{self.base_url}{endpoint}"
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method, "-k"]
        
        if self.token:
            cmd.extend(["-H", f"Authorization: Bearer {self.token}"])
        
        if headers:
            for k, v in headers.items():
                cmd.extend(["-H", f"{k}: {v}"])
        
        if data:
            cmd.extend(["-H", "Content-Type: application/json", "-d", data])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        lines = output.rsplit("\n", 1)
        
        body = lines[0] if len(lines) > 1 else ""
        status = int(lines[-1]) if lines[-1].isdigit() else 0
        
        try:
            body_json = json.loads(body)
        except:
            body_json = None
        
        return {
            "status": status,
            "body": body,
            "json": body_json
        }
    
    # ==================
    # Mass Assignment
    # ==================
    
    def test_mass_assignment(self, endpoint: str, 
                             known_fields: List[str]) -> List[Dict]:
        """Test for mass assignment vulnerabilities"""
        print(f"[*] Testing mass assignment on {endpoint}")
        
        findings = []
        
        # Fields to try injecting
        sensitive_fields = [
            "role", "isAdmin", "is_admin", "admin", "verified",
            "email_verified", "permissions", "groups", "balance",
            "credits", "subscription", "plan", "tier"
        ]
        
        for field in sensitive_fields:
            if field in known_fields:
                continue
            
            test_data = {f: True for f in known_fields}
            test_data[field] = True
            
            response = self.curl(endpoint, "POST", data=json.dumps(test_data))
            
            if response["status"] in [200, 201]:
                # Check if field was accepted
                if response["json"] and field in str(response["json"]):
                    findings.append({
                        "type": "Mass Assignment",
                        "severity": "HIGH",
                        "endpoint": endpoint,
                        "field": field
                    })
                    print(f"[!] Mass assignment: {field} accepted!")
        
        return findings
    
    # ==================
    # BOLA/IDOR
    # ==================
    
    def test_bola(self, endpoint_pattern: str, 
                  valid_id: str, test_ids: List[str]) -> List[Dict]:
        """Test for Broken Object Level Authorization"""
        print(f"[*] Testing BOLA on {endpoint_pattern}")
        
        findings = []
        
        for test_id in test_ids:
            endpoint = endpoint_pattern.replace("{id}", test_id)
            response = self.curl(endpoint)
            
            if response["status"] == 200:
                findings.append({
                    "type": "BOLA/IDOR",
                    "severity": "HIGH",
                    "endpoint": endpoint,
                    "accessed_id": test_id
                })
                print(f"[!] BOLA: Accessed {test_id}")
        
        return findings
    
    # ==================
    # BFLA
    # ==================
    
    def test_bfla(self, admin_endpoints: List[str]) -> List[Dict]:
        """Test for Broken Function Level Authorization"""
        print("[*] Testing BFLA on admin endpoints")
        
        findings = []
        
        for endpoint in admin_endpoints:
            response = self.curl(endpoint)
            
            if response["status"] == 200:
                findings.append({
                    "type": "BFLA",
                    "severity": "CRITICAL",
                    "endpoint": endpoint,
                    "description": "Admin function accessible to regular user"
                })
                print(f"[!] BFLA: {endpoint} accessible!")
        
        return findings
    
    # ==================
    # Rate Limiting
    # ==================
    
    def test_rate_limit_bypass(self, endpoint: str) -> Dict:
        """Test various rate limit bypass techniques"""
        print(f"[*] Testing rate limit bypass on {endpoint}")
        
        bypasses = [
            # IP spoofing headers
            {"X-Forwarded-For": "127.0.0.1"},
            {"X-Real-IP": "10.0.0.1"},
            {"X-Originating-IP": "192.168.1.1"},
            # Case variation
            {},  # normal, then uppercase endpoint
            # Null byte
            {},  # add %00 to endpoint
        ]
        
        results = []
        
        for headers in bypasses:
            successful = 0
            
            for _ in range(20):
                response = self.curl(endpoint, headers=headers)
                if response["status"] != 429:
                    successful += 1
            
            results.append({
                "headers": headers,
                "successful_requests": successful
            })
        
        return {"bypass_tests": results}
    
    # ==================
    # Security Headers
    # ==================
    
    def check_security_headers(self, endpoint: str = "/") -> Dict:
        """Check for security headers"""
        cmd = ["curl", "-s", "-I", "-k", f"{self.base_url}{endpoint}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        headers = {}
        for line in result.stdout.split("\n"):
            if ": " in line:
                k, v = line.split(": ", 1)
                headers[k.lower()] = v.strip()
        
        security_headers = {
            "strict-transport-security": "HSTS",
            "x-content-type-options": "X-Content-Type-Options",
            "x-frame-options": "X-Frame-Options",
            "content-security-policy": "CSP",
            "x-xss-protection": "X-XSS-Protection",
            "referrer-policy": "Referrer-Policy",
            "permissions-policy": "Permissions-Policy",
        }
        
        missing = []
        present = []
        
        for header, name in security_headers.items():
            if header in headers:
                present.append({"header": name, "value": headers[header]})
            else:
                missing.append(name)
        
        return {
            "present": present,
            "missing": missing
        }
    
    # ==================
    # API Versioning
    # ==================
    
    def test_api_versioning(self, endpoint: str) -> Dict:
        """Test for insecure API version handling"""
        print(f"[*] Testing API versioning on {endpoint}")
        
        versions = ["v1", "v2", "v3", "v0", "v999", ""]
        results = []
        
        for version in versions:
            # Try URL-based versioning
            url_version = endpoint.replace("/v2/", f"/{version}/").replace("/v1/", f"/{version}/")
            response = self.curl(url_version)
            
            results.append({
                "version": version,
                "url": url_version,
                "status": response["status"]
            })
            
            # Try header-based versioning
            response = self.curl(endpoint, headers={"API-Version": version})
            results.append({
                "version": f"Header: {version}",
                "status": response["status"]
            })
        
        return {"version_tests": results}
```

---

## 5. Integrated API Testing Script

```python
# api_security_test.py
"""
Run comprehensive API security tests
"""

import sys
import json
from graphql_security import GraphQLSecurityTester
from websocket_security import WebSocketSecurityTester
from grpc_security import GRPCSecurityTester
from rest_advanced import RESTAdvancedTester

def run_api_tests(target: str, token: str = None, api_type: str = "rest"):
    """Run API security tests based on API type"""
    
    all_findings = []
    
    if api_type == "graphql" or "graphql" in target.lower():
        print("\n" + "="*60)
        print("GRAPHQL SECURITY TESTING")
        print("="*60)
        
        tester = GraphQLSecurityTester(target, token)
        
        # Introspection
        tester.full_introspection()
        
        # Find sensitive fields
        sensitive = tester.extract_sensitive_queries()
        
        # DoS tests
        tester.test_query_complexity()
        tester.test_batch_attack()
        
        # Info disclosure
        tester.test_error_disclosure()
        tester.test_field_suggestions()
        
        all_findings.extend(tester.findings)
    
    elif api_type == "grpc":
        print("\n" + "="*60)
        print("GRPC SECURITY TESTING")
        print("="*60)
        
        host = target.replace("grpc://", "").split(":")[0]
        port = int(target.split(":")[-1]) if ":" in target else 443
        
        tester = GRPCSecurityTester(host, port)
        
        # Enumerate
        tester.enumerate_all()
        
        # Test reflection
        tester.test_reflection()
        
        all_findings.extend(tester.findings)
    
    else:  # REST API
        print("\n" + "="*60)
        print("REST API SECURITY TESTING")
        print("="*60)
        
        tester = RESTAdvancedTester(target, token)
        
        # Security headers
        headers = tester.check_security_headers()
        print(f"[*] Missing security headers: {headers['missing']}")
        
        # Test common vulnerabilities
        all_findings.extend(tester.findings)
    
    # Save results
    with open("/tmp/casperpro/api_security_findings.json", "w") as f:
        json.dump(all_findings, f, indent=2)
    
    print(f"\n[+] Total findings: {len(all_findings)}")
    return all_findings

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com/graphql"
    token = sys.argv[2] if len(sys.argv) > 2 else None
    api_type = sys.argv[3] if len(sys.argv) > 3 else "rest"
    
    run_api_tests(target, token, api_type)
```

---

## Summary

| API Type | Key Tests | Critical Findings |
|----------|-----------|-------------------|
| **GraphQL** | Introspection, complexity, batching, injection | Schema exposure, DoS, auth bypass |
| **WebSocket** | Origin validation, injection, CSWSH | Cross-site hijacking, message injection |
| **gRPC** | Reflection, auth bypass, injection | Unauthenticated access, data exposure |
| **REST** | BOLA, BFLA, mass assignment, versioning | Authorization bypass, data manipulation |

---

**Next Module:** casperpro-reporting.md for enterprise reporting with CVSS and compliance mapping
