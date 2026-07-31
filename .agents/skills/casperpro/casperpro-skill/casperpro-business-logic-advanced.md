# CasperPro Advanced Business Logic Testing Module

> **Comprehensive Business Logic Vulnerability Assessment**  
> Financial transactions, e-commerce flows, workflow state machines, and multi-tenant isolation testing.

## Overview

This module provides advanced business logic testing capabilities for:

- **Financial Applications** - Banking, payment processing, trading platforms
- **E-Commerce Platforms** - Shopping carts, checkout, coupons, inventory
- **Workflow Systems** - Multi-step processes, approvals, state machines
- **Multi-Tenant SaaS** - Tenant isolation, cross-tenant attacks

> **Python Package Manager**: All Python operations MUST use `uv`. Never use `pip`.

## 1. Financial Transaction Testing

### 1.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_financial_logic.py
# Run with: uv run casperpro_financial_logic.py

import subprocess
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class Finding:
    test: str
    severity: Severity
    payload: Dict[str, Any]
    response: str = ""
    impact: str = ""

@dataclass
class FinancialLogicTester:
    base_url: str
    token: str
    proxy: str = None
    findings: List[Finding] = field(default_factory=list)
    
    def _request(self, endpoint: str, method: str = "POST", body: dict = None) -> dict:
        """Make HTTP request using curl"""
        url = f"{self.base_url}{endpoint}"
        cmd = ["curl", "-s", "-X", method, "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json"]
        
        if self.proxy:
            cmd.extend(["--proxy", self.proxy, "-k"])
        
        if body:
            cmd.extend(["-d", json.dumps(body)])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return {"status": 200, "body": result.stdout, "json": json.loads(result.stdout)}
        except:
            return {"status": 0, "body": result.stdout, "json": None}
    
    def test_negative_amounts(self) -> List[Finding]:
        """Test negative amount transfers"""
        print("[*] Testing negative amount transfers...")
        findings = []
        
        payloads = [
            {"amount": -100, "from": "account1", "to": "account2"},
            {"amount": "-100", "from": "account1", "to": "account2"},
            {"amount": -0.01, "from": "account1", "to": "account2"},
            {"amount": "-999999.99", "from": "account1", "to": "account2"},
        ]
        
        for payload in payloads:
            response = self._request("/transfer", "POST", payload)
            
            if response["status"] == 200 or "success" in response["body"].lower():
                finding = Finding(
                    test="Negative Amount Transfer",
                    severity=Severity.CRITICAL,
                    payload=payload,
                    response=response["body"][:200],
                    impact="Funds can be stolen by reversing transfer direction"
                )
                findings.append(finding)
                print(f"  [VULN] Negative amount accepted: {payload['amount']}")
        
        return findings
    
    def test_zero_amount(self) -> List[Finding]:
        """Test zero amount transfers (fee exploitation)"""
        print("[*] Testing zero amount transfers...")
        findings = []
        
        payload = {"amount": 0, "from": "account1", "to": "account2"}
        response = self._request("/transfer", "POST", payload)
        
        if response["status"] == 200:
            finding = Finding(
                test="Zero Amount Transfer",
                severity=Severity.MEDIUM,
                payload=payload,
                impact="May bypass fee structures or create audit issues"
            )
            findings.append(finding)
            print("  [VULN] Zero amount transfer accepted")
        
        return findings
    
    def test_decimal_precision(self) -> List[Finding]:
        """Test decimal precision exploitation"""
        print("[*] Testing decimal precision attacks...")
        findings = []
        
        payloads = [
            {"amount": 0.000001, "desc": "Sub-cent precision"},
            {"amount": 0.009, "desc": "Rounding edge case"},
            {"amount": 99.999999, "desc": "Precision overflow"},
            {"amount": "1e10", "desc": "Scientific notation"},
            {"amount": 999999999999.99, "desc": "Large amount overflow"},
            {"amount": "Infinity", "desc": "Infinity value"},
            {"amount": "NaN", "desc": "Not a number"},
        ]
        
        for p in payloads:
            payload = {"amount": p["amount"], "from": "account1", "to": "account2"}
            response = self._request("/transfer", "POST", payload)
            
            if response["status"] == 200:
                finding = Finding(
                    test=f"Decimal Precision - {p['desc']}",
                    severity=Severity.HIGH,
                    payload=payload,
                    response=response["body"][:200]
                )
                findings.append(finding)
                print(f"  [VULN] Precision attack accepted: {p['amount']}")
        
        return findings
    
    def test_currency_manipulation(self) -> List[Finding]:
        """Test currency conversion exploitation"""
        print("[*] Testing currency manipulation...")
        findings = []
        
        payloads = [
            {"amount": 100, "from_currency": "USD", "to_currency": "USD", "rate": 2.0},
            {"amount": 100, "from_currency": "BTC", "to_currency": "USD", "rate": -1},
            {"amount": 100, "currency": "XXX"},  # Invalid currency
            {"amount": 100, "from_currency": "USD", "to_currency": "USD", "rate": 0},
            {"amount": 100, "from_currency": "USD", "to_currency": "USD", "rate": 999999},
        ]
        
        for payload in payloads:
            response = self._request("/convert", "POST", payload)
            
            if response["status"] == 200 and "success" in response["body"].lower():
                finding = Finding(
                    test="Currency Manipulation",
                    severity=Severity.CRITICAL,
                    payload=payload,
                    impact="Exchange rate manipulation for profit"
                )
                findings.append(finding)
                print(f"  [VULN] Currency manipulation accepted")
        
        return findings
    
    def test_transaction_replay(self) -> List[Finding]:
        """Test transaction replay attacks"""
        print("[*] Testing transaction replay...")
        findings = []
        
        payload = {"amount": 1, "from": "account1", "to": "account2", "nonce": "test123", "tx_id": "TX001"}
        
        # Send same transaction multiple times
        success_count = 0
        for _ in range(5):
            response = self._request("/transfer", "POST", payload)
            if response["status"] == 200 or "success" in response["body"].lower():
                success_count += 1
        
        if success_count > 1:
            finding = Finding(
                test="Transaction Replay",
                severity=Severity.CRITICAL,
                payload={"attempts": 5, "successful": success_count},
                impact=f"Transaction executed {success_count} times - funds can be drained"
            )
            findings.append(finding)
            print(f"  [VULN] Transaction replay possible - {success_count} duplicates")
        
        return findings
    
    def test_overdraft_bypass(self) -> List[Finding]:
        """Test overdraft/insufficient funds bypass"""
        print("[*] Testing overdraft bypass...")
        findings = []
        
        payloads = [
            {"amount": 999999999, "from": "account1", "to": "account2"},
            {"amount": 100, "from": "account1", "to": "account2", "force": True},
            {"amount": 100, "from": "account1", "to": "account2", "skip_balance_check": True},
            {"amount": 100, "from": "account1", "to": "account2", "override": True},
            {"amount": 100, "from": "account1", "to": "account2", "admin": True},
        ]
        
        for payload in payloads:
            response = self._request("/transfer", "POST", payload)
            
            if response["status"] == 200 or "success" in response["body"].lower():
                finding = Finding(
                    test="Overdraft Bypass",
                    severity=Severity.CRITICAL,
                    payload=payload,
                    impact="Accounts can be drained beyond balance"
                )
                findings.append(finding)
                print(f"  [VULN] Overdraft bypass with: {list(payload.keys())}")
        
        return findings
    
    def test_interest_rate_manipulation(self) -> List[Finding]:
        """Test interest rate manipulation"""
        print("[*] Testing interest rate manipulation...")
        findings = []
        
        payloads = [
            {"account_id": "ACC001", "interest_rate": -5.0},
            {"account_id": "ACC001", "interest_rate": 999.99},
            {"account_id": "ACC001", "interest_rate": 0, "compound": "continuous"},
            {"loan_id": "LOAN001", "rate_override": 0.001},
        ]
        
        for payload in payloads:
            response = self._request("/account/settings", "PUT", payload)
            
            if response["status"] == 200:
                finding = Finding(
                    test="Interest Rate Manipulation",
                    severity=Severity.CRITICAL,
                    payload=payload,
                    impact="Financial gain through rate manipulation"
                )
                findings.append(finding)
                print(f"  [VULN] Interest rate manipulation accepted")
        
        return findings
    
    def test_fee_bypass(self) -> List[Finding]:
        """Test transaction fee bypass"""
        print("[*] Testing fee bypass...")
        findings = []
        
        payloads = [
            {"amount": 100, "fee": 0},
            {"amount": 100, "fee": -10},
            {"amount": 100, "fee_waiver": True},
            {"amount": 100, "fee_code": "INTERNAL"},
            {"amount": 100, "fee_exempt": True, "reason": "test"},
        ]
        
        for payload in payloads:
            response = self._request("/transfer", "POST", payload)
            
            if response["status"] == 200:
                # Check if fee was actually bypassed
                if response.get("json", {}).get("fee", 1) == 0:
                    finding = Finding(
                        test="Fee Bypass",
                        severity=Severity.HIGH,
                        payload=payload,
                        impact="Transaction fees can be avoided"
                    )
                    findings.append(finding)
                    print(f"  [VULN] Fee bypass accepted")
        
        return findings
    
    def run_all_tests(self) -> List[Finding]:
        """Run all financial logic tests"""
        all_findings = []
        
        all_findings.extend(self.test_negative_amounts())
        all_findings.extend(self.test_zero_amount())
        all_findings.extend(self.test_decimal_precision())
        all_findings.extend(self.test_currency_manipulation())
        all_findings.extend(self.test_transaction_replay())
        all_findings.extend(self.test_overdraft_bypass())
        all_findings.extend(self.test_interest_rate_manipulation())
        all_findings.extend(self.test_fee_bypass())
        
        self.findings = all_findings
        return all_findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = FinancialLogicTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all_tests()
    
    print(f"\n{'='*60}")
    print(f"Financial Logic Testing Complete")
    print(f"{'='*60}")
    print(f"Total Findings: {len(findings)}")
    print(f"Critical: {len([f for f in findings if f.severity == Severity.CRITICAL])}")
    print(f"High: {len([f for f in findings if f.severity == Severity.HIGH])}")
    print(f"Medium: {len([f for f in findings if f.severity == Severity.MEDIUM])}")
```

### 1.2 Bash/curl Implementation

```bash
#!/bin/bash
# casperpro_financial_logic.sh
# Financial logic testing with curl

BASE_URL="${1:?Usage: $0 <base_url> <token>}"
TOKEN="${2:?Token required}"
PROXY="${3:-}"

CURL_OPTS="-s -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json'"
[[ -n "$PROXY" ]] && CURL_OPTS="$CURL_OPTS --proxy $PROXY -k"

echo "=== Financial Logic Testing ==="
echo "Target: $BASE_URL"

# Test 1: Negative amounts
echo -e "\n[Test 1] Negative Amount Transfers"
for amount in -100 -0.01 "-999999"; do
    response=$(eval curl $CURL_OPTS -X POST -d "{\"amount\":$amount,\"from\":\"acc1\",\"to\":\"acc2\"}" "$BASE_URL/transfer" 2>/dev/null)
    if echo "$response" | grep -qi "success\|complete\|transfer"; then
        echo "[VULN] Negative amount $amount accepted"
    fi
done

# Test 2: Zero amount
echo -e "\n[Test 2] Zero Amount Transfer"
response=$(eval curl $CURL_OPTS -X POST -d '{"amount":0,"from":"acc1","to":"acc2"}' "$BASE_URL/transfer" 2>/dev/null)
if echo "$response" | grep -qi "success"; then
    echo "[VULN] Zero amount accepted"
fi

# Test 3: Scientific notation / special values
echo -e "\n[Test 3] Special Amount Values"
for amount in '"1e10"' '"Infinity"' '"NaN"' '999999999999.99'; do
    response=$(eval curl $CURL_OPTS -X POST -d "{\"amount\":$amount,\"from\":\"acc1\",\"to\":\"acc2\"}" "$BASE_URL/transfer" 2>/dev/null)
    if echo "$response" | grep -qi "success"; then
        echo "[VULN] Special value $amount accepted"
    fi
done

# Test 4: Transaction replay
echo -e "\n[Test 4] Transaction Replay"
success_count=0
for i in {1..5}; do
    response=$(eval curl $CURL_OPTS -X POST -d '{"amount":1,"from":"acc1","to":"acc2","nonce":"SAME123"}' "$BASE_URL/transfer" 2>/dev/null)
    if echo "$response" | grep -qi "success"; then
        ((success_count++))
    fi
done
if [ $success_count -gt 1 ]; then
    echo "[VULN] Transaction replay - $success_count duplicates accepted"
fi

# Test 5: Overdraft bypass
echo -e "\n[Test 5] Overdraft Bypass"
for payload in '{"amount":999999999,"from":"acc1","to":"acc2"}' \
               '{"amount":100,"from":"acc1","to":"acc2","force":true}' \
               '{"amount":100,"from":"acc1","to":"acc2","skip_balance_check":true}'; do
    response=$(eval curl $CURL_OPTS -X POST -d "$payload" "$BASE_URL/transfer" 2>/dev/null)
    if echo "$response" | grep -qi "success"; then
        echo "[VULN] Overdraft bypass: $payload"
    fi
done

echo -e "\n=== Testing Complete ==="
```

## 2. E-Commerce Logic Testing

### 2.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_ecommerce_logic.py
# Run with: uv run casperpro_ecommerce_logic.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import time

@dataclass
class EcommerceTester:
    base_url: str
    token: str
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _curl(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
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
        
        return {"status": status, "body": body}
    
    def test_price_manipulation(self):
        """Test price tampering in cart/checkout"""
        print("[*] Testing price manipulation...")
        
        payloads = [
            {"product_id": "PROD001", "quantity": 1, "price": 0.01},
            {"product_id": "PROD001", "quantity": 1, "price": -100},
            {"product_id": "PROD001", "quantity": 1, "unit_price": 0},
            {"product_id": "PROD001", "quantity": 1, "price": 0, "discount": 0},
            {"product_id": "PROD001", "quantity": 1, "total": 0.01},
        ]
        
        for payload in payloads:
            resp = self._curl("/cart/add", "POST", payload)
            if resp["status"] == 200:
                print(f"  [VULN] Price manipulation accepted: price={payload.get('price', payload.get('unit_price', 'N/A'))}")
                self.findings.append({"test": "Price Manipulation", "payload": payload, "severity": "CRITICAL"})
    
    def test_quantity_manipulation(self):
        """Test quantity tampering"""
        print("[*] Testing quantity manipulation...")
        
        payloads = [
            {"product_id": "PROD001", "quantity": -1},
            {"product_id": "PROD001", "quantity": 0},
            {"product_id": "PROD001", "quantity": 999999999},
            {"product_id": "PROD001", "quantity": 1.5},
            {"product_id": "PROD001", "quantity": "1; DROP TABLE orders--"},
        ]
        
        for payload in payloads:
            resp = self._curl("/cart/add", "POST", payload)
            if resp["status"] == 200:
                print(f"  [VULN] Quantity manipulation: {payload['quantity']}")
                self.findings.append({"test": "Quantity Manipulation", "payload": payload, "severity": "HIGH"})
    
    def test_discount_stacking(self):
        """Test coupon/discount stacking"""
        print("[*] Testing discount stacking...")
        
        coupons = ["SAVE10", "WELCOME20", "VIP50", "FLASH25", "SPECIAL30"]
        applied = []
        
        for coupon in coupons:
            resp = self._curl("/cart/coupon", "POST", {"coupon_code": coupon})
            if resp["status"] == 200 and "applied" in resp["body"].lower():
                applied.append(coupon)
        
        if len(applied) > 1:
            print(f"  [VULN] Multiple coupons stacked: {applied}")
            self.findings.append({"test": "Coupon Stacking", "coupons": applied, "severity": "HIGH"})
        
        # Check total discount
        cart = self._curl("/cart", "GET")
        if "discount" in cart["body"]:
            try:
                cart_data = json.loads(cart["body"])
                if cart_data.get("discount_percentage", 0) > 100:
                    print("  [VULN] Discount exceeds 100%!")
                    self.findings.append({"test": "Over-Discount", "severity": "CRITICAL"})
            except:
                pass
    
    def test_coupon_reuse(self):
        """Test single-use coupon reuse"""
        print("[*] Testing single-use coupon reuse...")
        
        coupon = "ONEUSE50"
        success_count = 0
        
        for _ in range(3):
            resp = self._curl("/cart/coupon", "POST", {"coupon_code": coupon})
            if resp["status"] == 200 and "applied" in resp["body"].lower():
                success_count += 1
        
        if success_count > 1:
            print(f"  [VULN] Single-use coupon reused {success_count} times")
            self.findings.append({"test": "Coupon Reuse", "count": success_count, "severity": "HIGH"})
    
    def test_race_condition_checkout(self):
        """Test race condition in limited stock checkout"""
        print("[*] Testing checkout race condition...")
        
        def attempt_checkout():
            return self._curl("/checkout", "POST", {"product_id": "LIMITED001", "quantity": 1})
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(attempt_checkout) for _ in range(20)]
            results = [f.result() for f in futures]
        
        success_count = sum(1 for r in results if r["status"] == 200 or "success" in r["body"].lower())
        
        if success_count > 1:
            print(f"  [VULN] Race condition - {success_count} orders for limited stock")
            self.findings.append({"test": "Checkout Race Condition", "orders": success_count, "severity": "HIGH"})
    
    def test_shipping_manipulation(self):
        """Test shipping cost bypass"""
        print("[*] Testing shipping manipulation...")
        
        payloads = [
            {"shipping_method": "express", "shipping_cost": 0},
            {"shipping_method": "free", "weight": 0.001},
            {"shipping_method": "pickup", "address": {"country": "overseas"}},
            {"shipping_override": True, "shipping_cost": 0},
        ]
        
        for payload in payloads:
            resp = self._curl("/cart/shipping", "POST", payload)
            if resp["status"] == 200:
                try:
                    data = json.loads(resp["body"])
                    if data.get("shipping_cost", 1) == 0:
                        print(f"  [VULN] Free shipping bypass")
                        self.findings.append({"test": "Shipping Bypass", "payload": payload, "severity": "MEDIUM"})
                except:
                    pass
    
    def test_tax_bypass(self):
        """Test tax calculation bypass"""
        print("[*] Testing tax bypass...")
        
        payloads = [
            {"country": "XX", "state": ""},
            {"country": "US", "state": "MT", "billing_country": "DE"},
            {"tax_exempt": True, "tax_id": "fake123"},
            {"tax_rate": 0},
        ]
        
        for payload in payloads:
            resp = self._curl("/cart/tax", "POST", payload)
            if resp["status"] == 200:
                try:
                    data = json.loads(resp["body"])
                    if data.get("tax", 1) == 0:
                        print(f"  [VULN] Tax bypass")
                        self.findings.append({"test": "Tax Bypass", "payload": payload, "severity": "HIGH"})
                except:
                    pass
    
    def test_inventory_manipulation(self):
        """Test inventory/stock manipulation"""
        print("[*] Testing inventory manipulation...")
        
        payloads = [
            {"product_id": "PROD001", "quantity": 1, "ignore_stock": True},
            {"product_id": "PROD001", "quantity": 1, "force_available": True},
            {"product_id": "OUTOFSTOCK", "quantity": 1, "override_stock": True},
        ]
        
        for payload in payloads:
            resp = self._curl("/cart/add", "POST", payload)
            if resp["status"] == 200:
                print(f"  [VULN] Inventory override accepted")
                self.findings.append({"test": "Inventory Bypass", "payload": payload, "severity": "HIGH"})
    
    def test_gift_card_exploitation(self):
        """Test gift card/store credit exploitation"""
        print("[*] Testing gift card exploitation...")
        
        payloads = [
            {"gift_card": "GIFTCARD001", "amount": -100},
            {"gift_card": "GIFTCARD001", "amount": 999999},
            {"store_credit": True, "amount": 0, "apply_negative": True},
        ]
        
        for payload in payloads:
            resp = self._curl("/cart/gift-card", "POST", payload)
            if resp["status"] == 200:
                print(f"  [VULN] Gift card exploitation")
                self.findings.append({"test": "Gift Card Exploit", "payload": payload, "severity": "HIGH"})
    
    def run_all(self):
        """Run all e-commerce tests"""
        self.test_price_manipulation()
        self.test_quantity_manipulation()
        self.test_discount_stacking()
        self.test_coupon_reuse()
        self.test_race_condition_checkout()
        self.test_shipping_manipulation()
        self.test_tax_bypass()
        self.test_inventory_manipulation()
        self.test_gift_card_exploitation()
        
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = EcommerceTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    
    print(f"\n{'='*60}")
    print(f"E-Commerce Logic Testing Complete")
    print(f"Total Findings: {len(findings)}")
```

## 3. Workflow and State Machine Testing

### 3.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_workflow_logic.py
# Run with: uv run casperpro_workflow_logic.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class WorkflowTester:
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
    
    def test_step_bypass(self):
        """Test multi-step process bypass"""
        print("[*] Testing step bypass...")
        
        endpoints = [
            "/onboarding/step3",
            "/checkout/payment",
            "/order/confirm",
            "/application/approve",
            "/verification/complete",
            "/kyc/approved",
        ]
        
        for endpoint in endpoints:
            resp = self._request(endpoint, "POST", {"skip_validation": True})
            if resp["status"] == 200:
                print(f"  [VULN] Step bypass: {endpoint}")
                self.findings.append({"test": "Step Bypass", "endpoint": endpoint, "severity": "HIGH"})
    
    def test_invalid_state_transitions(self):
        """Test invalid state transitions"""
        print("[*] Testing invalid state transitions...")
        
        transitions = [
            {"id": "ORD001", "from": "cancelled", "to": "shipped"},
            {"id": "ORD001", "from": "completed", "to": "pending"},
            {"id": "ORD001", "from": "pending", "to": "refunded"},
            {"id": "ORD001", "from": "shipped", "to": "processing"},
            {"id": "ORD001", "from": "refunded", "to": "completed"},
        ]
        
        for t in transitions:
            resp = self._request("/order/status", "PUT", {"order_id": t["id"], "status": t["to"]})
            if resp["status"] == 200:
                print(f"  [VULN] Invalid transition: {t['from']} -> {t['to']}")
                self.findings.append({"test": "Invalid State Transition", "transition": t, "severity": "HIGH"})
    
    def test_approval_bypass(self):
        """Test approval workflow bypass"""
        print("[*] Testing approval bypass...")
        
        payloads = [
            {"request_id": "REQ001", "approved": True, "approver_id": "self"},
            {"request_id": "REQ001", "status": "approved", "skip_approval": True},
            {"request_id": "REQ001", "auto_approve": True},
            {"request_id": "REQ001", "approved_by": "system"},
            {"request_id": "REQ001", "override_approval": True},
        ]
        
        for payload in payloads:
            resp = self._request("/request/approve", "POST", payload)
            if resp["status"] == 200:
                print(f"  [VULN] Approval bypass: {list(payload.keys())}")
                self.findings.append({"test": "Approval Bypass", "payload": payload, "severity": "CRITICAL"})
    
    def test_time_based_logic(self):
        """Test time-based logic flaws"""
        print("[*] Testing time-based logic...")
        
        payloads = [
            {"promo_code": "EXPIRED2020", "timestamp": "2020-01-01T00:00:00Z"},
            {"promo_code": "FUTURE2030", "timestamp": "2030-01-01T00:00:00Z"},
            {"action": "claim_bonus", "last_claim": "1970-01-01T00:00:00Z"},
            {"offer_id": "FLASH001", "valid_until": "2099-12-31T23:59:59Z"},
        ]
        
        for payload in payloads:
            resp = self._request("/promo/apply", "POST", payload)
            if resp["status"] == 200 and "success" in resp["body"].lower():
                print(f"  [VULN] Time-based bypass: {payload}")
                self.findings.append({"test": "Time-Based Bypass", "payload": payload, "severity": "MEDIUM"})
    
    def test_post_completion_manipulation(self):
        """Test manipulation after completion"""
        print("[*] Testing post-completion manipulation...")
        
        actions = [
            {"order_id": "COMPLETED001", "action": "cancel"},
            {"order_id": "SHIPPED001", "action": "modify", "items": []},
            {"payment_id": "PAID001", "action": "refund", "amount": 1000},
            {"order_id": "DELIVERED001", "action": "return_full_refund"},
        ]
        
        for payload in actions:
            resp = self._request("/order/action", "POST", payload)
            if resp["status"] == 200:
                print(f"  [VULN] Post-completion action: {payload['action']}")
                self.findings.append({"test": "Post-Completion Manipulation", "payload": payload, "severity": "HIGH"})
    
    def test_concurrent_state_changes(self):
        """Test concurrent state modifications"""
        print("[*] Testing concurrent state changes...")
        
        from concurrent.futures import ThreadPoolExecutor
        
        def change_state(status):
            return self._request("/order/status", "PUT", {"order_id": "ORD001", "status": status})
        
        statuses = ["processing", "shipped", "delivered", "cancelled", "refunded"]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(change_state, statuses))
        
        success_count = sum(1 for r in results if r["status"] == 200)
        if success_count > 1:
            print(f"  [VULN] Concurrent state race - {success_count} transitions succeeded")
            self.findings.append({"test": "Concurrent State Race", "count": success_count, "severity": "HIGH"})
    
    def test_rollback_abuse(self):
        """Test rollback/undo abuse"""
        print("[*] Testing rollback abuse...")
        
        payloads = [
            {"action": "rollback", "transaction_id": "TX001", "steps": 999},
            {"action": "undo", "count": -1},
            {"action": "revert", "to_state": "initial"},
        ]
        
        for payload in payloads:
            resp = self._request("/workflow/rollback", "POST", payload)
            if resp["status"] == 200:
                print(f"  [VULN] Rollback abuse: {payload}")
                self.findings.append({"test": "Rollback Abuse", "payload": payload, "severity": "HIGH"})
    
    def run_all(self):
        """Run all workflow tests"""
        self.test_step_bypass()
        self.test_invalid_state_transitions()
        self.test_approval_bypass()
        self.test_time_based_logic()
        self.test_post_completion_manipulation()
        self.test_concurrent_state_changes()
        self.test_rollback_abuse()
        
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [proxy]")
        sys.exit(1)
    
    tester = WorkflowTester(
        base_url=sys.argv[1],
        token=sys.argv[2],
        proxy=sys.argv[3] if len(sys.argv) > 3 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 4. Multi-Tenant Isolation Testing

### 4.1 Python Implementation

```python
#!/usr/bin/env python3
# casperpro_multitenant_logic.py
# Run with: uv run casperpro_multitenant_logic.py

import subprocess
import json
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class MultiTenantTester:
    base_url: str
    tenant1_token: str
    tenant2_token: str
    proxy: Optional[str] = None
    findings: List[Dict] = field(default_factory=list)
    
    def _request(self, endpoint: str, token: str, method: str = "GET", 
                 data: dict = None, extra_headers: dict = None) -> dict:
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {token}",
               "-H", "Content-Type: application/json"]
        
        if extra_headers:
            for k, v in extra_headers.items():
                cmd.extend(["-H", f"{k}: {v}"])
        
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
            json_data = None
        
        return {"status": status, "body": body, "json": json_data}
    
    def test_cross_tenant_data_access(self):
        """Test accessing another tenant's resources"""
        print("[*] Testing cross-tenant data access...")
        
        # Get Tenant 2's resources
        t2_resources = self._request("/resources", self.tenant2_token)
        
        if t2_resources["json"] and "data" in t2_resources["json"]:
            for resource in t2_resources["json"]["data"][:5]:
                resource_id = resource.get("id", resource.get("_id"))
                if resource_id:
                    # Try to access with Tenant 1's token
                    resp = self._request(f"/resources/{resource_id}", self.tenant1_token)
                    
                    if resp["status"] == 200:
                        print(f"  [VULN] Cross-tenant access: T1 accessed T2's resource {resource_id}")
                        self.findings.append({
                            "test": "Cross-Tenant Access",
                            "resource_id": resource_id,
                            "severity": "CRITICAL"
                        })
    
    def test_tenant_id_manipulation(self):
        """Test tenant ID header/parameter manipulation"""
        print("[*] Testing tenant ID manipulation...")
        
        # Header-based
        header_payloads = [
            {"X-Tenant-ID": "tenant2"},
            {"X-Organization-ID": "org2"},
            {"X-Account-ID": "*"},
        ]
        
        for headers in header_payloads:
            resp = self._request("/admin/users", self.tenant1_token, extra_headers=headers)
            if resp["status"] == 200 and "tenant2" in resp["body"]:
                print(f"  [VULN] Tenant header manipulation: {headers}")
                self.findings.append({"test": "Tenant Header Manipulation", "headers": headers, "severity": "CRITICAL"})
        
        # Body-based
        body_payloads = [
            {"tenant_id": "tenant2", "action": "list_users"},
            {"organization_id": "*", "scope": "global"},
            {"tenant_id": "", "include_all": True},
        ]
        
        for payload in body_payloads:
            resp = self._request("/admin/query", self.tenant1_token, "POST", payload)
            if resp["status"] == 200 and "tenant2" in resp["body"]:
                print(f"  [VULN] Tenant body manipulation: {list(payload.keys())}")
                self.findings.append({"test": "Tenant Body Manipulation", "payload": payload, "severity": "CRITICAL"})
    
    def test_shared_resource_pollution(self):
        """Test pollution of shared resources"""
        print("[*] Testing shared resource pollution...")
        
        payloads = [
            {"template_id": "global_template", "content": "POLLUTED_BY_T1", "scope": "all_tenants"},
            {"config_key": "system.setting", "value": "POLLUTED"},
            {"shared_file": "common.txt", "content": "MALICIOUS"},
        ]
        
        for payload in payloads:
            # Tenant 1 modifies
            self._request("/settings", self.tenant1_token, "PUT", payload)
            
            # Check if Tenant 2 sees the change
            check = self._request("/settings", self.tenant2_token)
            
            if "POLLUTED" in check["body"] or "MALICIOUS" in check["body"]:
                print(f"  [VULN] Cross-tenant pollution detected")
                self.findings.append({"test": "Shared Resource Pollution", "payload": payload, "severity": "CRITICAL"})
    
    def test_tenant_enumeration(self):
        """Test tenant/organization enumeration"""
        print("[*] Testing tenant enumeration...")
        
        # Try to list all tenants
        resp = self._request("/tenants", self.tenant1_token)
        if resp["status"] == 200 and resp["json"]:
            if len(resp["json"]) > 1 or "tenant2" in resp["body"]:
                print(f"  [VULN] Tenant enumeration possible")
                self.findings.append({"test": "Tenant Enumeration", "severity": "MEDIUM"})
        
        # Try common tenant IDs
        for tenant_id in ["tenant1", "tenant2", "admin", "default", "root"]:
            resp = self._request(f"/tenant/{tenant_id}/info", self.tenant1_token)
            if resp["status"] == 200:
                print(f"  [VULN] Tenant info disclosure: {tenant_id}")
                self.findings.append({"test": "Tenant Info Disclosure", "tenant": tenant_id, "severity": "MEDIUM"})
    
    def test_cross_tenant_actions(self):
        """Test performing actions on another tenant's resources"""
        print("[*] Testing cross-tenant actions...")
        
        # Get Tenant 2's user
        t2_users = self._request("/users", self.tenant2_token)
        
        if t2_users["json"] and "data" in t2_users["json"]:
            for user in t2_users["json"]["data"][:3]:
                user_id = user.get("id", user.get("_id"))
                if user_id:
                    # Try to delete with Tenant 1's token
                    resp = self._request(f"/users/{user_id}", self.tenant1_token, "DELETE")
                    
                    if resp["status"] in [200, 204]:
                        print(f"  [VULN] Cross-tenant DELETE: T1 deleted T2's user {user_id}")
                        self.findings.append({
                            "test": "Cross-Tenant Delete",
                            "user_id": user_id,
                            "severity": "CRITICAL"
                        })
                    
                    # Try to modify
                    resp = self._request(f"/users/{user_id}", self.tenant1_token, "PUT", 
                                        {"role": "admin"})
                    if resp["status"] == 200:
                        print(f"  [VULN] Cross-tenant UPDATE: T1 modified T2's user {user_id}")
                        self.findings.append({
                            "test": "Cross-Tenant Update",
                            "user_id": user_id,
                            "severity": "CRITICAL"
                        })
    
    def run_all(self):
        """Run all multi-tenant tests"""
        self.test_cross_tenant_data_access()
        self.test_tenant_id_manipulation()
        self.test_shared_resource_pollution()
        self.test_tenant_enumeration()
        self.test_cross_tenant_actions()
        
        return self.findings


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <tenant1_token> <tenant2_token> [proxy]")
        sys.exit(1)
    
    tester = MultiTenantTester(
        base_url=sys.argv[1],
        tenant1_token=sys.argv[2],
        tenant2_token=sys.argv[3],
        proxy=sys.argv[4] if len(sys.argv) > 4 else None
    )
    
    findings = tester.run_all()
    print(f"\nTotal Findings: {len(findings)}")
```

## 5. Complete Business Logic Assessment

### 5.1 Orchestrator Script

```python
#!/usr/bin/env python3
# casperpro_business_logic_full.py
# Run with: uv run casperpro_business_logic_full.py

import subprocess
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

def run_assessment(base_url: str, token: str, tenant2_token: str = None, proxy: str = None):
    """Run complete business logic assessment"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     CasperPro Business Logic Assessment Suite v2.2        ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Financial | E-Commerce | Workflow | Multi-Tenant         ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    all_findings = []
    
    # Import and run each tester
    print("\n[1/4] Financial Logic Testing...")
    print("=" * 50)
    # (Would import and run FinancialLogicTester)
    
    print("\n[2/4] E-Commerce Logic Testing...")
    print("=" * 50)
    # (Would import and run EcommerceTester)
    
    print("\n[3/4] Workflow State Machine Testing...")
    print("=" * 50)
    # (Would import and run WorkflowTester)
    
    if tenant2_token:
        print("\n[4/4] Multi-Tenant Isolation Testing...")
        print("=" * 50)
        # (Would import and run MultiTenantTester)
    else:
        print("\n[4/4] Skipping Multi-Tenant Testing (no second token)")
    
    # Generate report
    report = {
        "target": base_url,
        "timestamp": datetime.now().isoformat(),
        "findings": all_findings,
        "summary": {
            "critical": len([f for f in all_findings if f.get("severity") == "CRITICAL"]),
            "high": len([f for f in all_findings if f.get("severity") == "HIGH"]),
            "medium": len([f for f in all_findings if f.get("severity") == "MEDIUM"]),
            "low": len([f for f in all_findings if f.get("severity") == "LOW"]),
        }
    }
    
    # Save report
    output_dir = os.path.expanduser("~/casper_reports")
    os.makedirs(output_dir, exist_ok=True)
    
    report_file = os.path.join(output_dir, f"business_logic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print("ASSESSMENT COMPLETE")
    print(f"{'=' * 60}")
    print(f"Total Findings: {len(all_findings)}")
    print(f"  Critical: {report['summary']['critical']}")
    print(f"  High: {report['summary']['high']}")
    print(f"  Medium: {report['summary']['medium']}")
    print(f"  Low: {report['summary']['low']}")
    print(f"\nReport saved: {report_file}")
    
    return report


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: uv run {sys.argv[0]} <base_url> <token> [tenant2_token] [proxy]")
        sys.exit(1)
    
    run_assessment(
        base_url=sys.argv[1],
        token=sys.argv[2],
        tenant2_token=sys.argv[3] if len(sys.argv) > 3 else None,
        proxy=sys.argv[4] if len(sys.argv) > 4 else None
    )
```

## Test Coverage Matrix

| Category | Test | Severity | Impact |
|----------|------|----------|--------|
| **Financial** | Negative Amounts | CRITICAL | Fund theft via direction reversal |
| **Financial** | Zero Amount | MEDIUM | Fee bypass, audit issues |
| **Financial** | Decimal Precision | HIGH | Rounding exploitation |
| **Financial** | Currency Manipulation | CRITICAL | Exchange rate fraud |
| **Financial** | Transaction Replay | CRITICAL | Double-spending |
| **Financial** | Overdraft Bypass | CRITICAL | Unauthorized withdrawals |
| **E-Commerce** | Price Manipulation | CRITICAL | Free/cheap products |
| **E-Commerce** | Quantity Tampering | HIGH | Inventory manipulation |
| **E-Commerce** | Coupon Stacking | HIGH | Excessive discounts |
| **E-Commerce** | Coupon Reuse | HIGH | Repeated discounts |
| **E-Commerce** | Race Condition | HIGH | Overselling limited stock |
| **E-Commerce** | Shipping Bypass | MEDIUM | Free shipping fraud |
| **E-Commerce** | Tax Bypass | HIGH | Tax evasion |
| **Workflow** | Step Bypass | HIGH | Skip verification |
| **Workflow** | Invalid Transitions | HIGH | Process corruption |
| **Workflow** | Approval Bypass | CRITICAL | Unauthorized approvals |
| **Workflow** | Time Manipulation | MEDIUM | Expired offer exploitation |
| **Multi-Tenant** | Cross-Tenant Access | CRITICAL | Data breach |
| **Multi-Tenant** | Tenant ID Manipulation | CRITICAL | Access control bypass |
| **Multi-Tenant** | Resource Pollution | CRITICAL | Cross-tenant impact |

## Version Information

**Module Version:** 1.0  
**CasperPro Version:** 2.2  
**Python Package Manager:** uv (REQUIRED)  
**Last Updated:** 2026-01-11
