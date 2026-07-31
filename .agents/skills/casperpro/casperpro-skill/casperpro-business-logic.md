# CasperPro Business Logic Testing Module

> Advanced Business Logic Vulnerability Testing for Enterprise Applications

## Overview

This module covers comprehensive business logic vulnerability testing for financial applications, e-commerce platforms, SaaS systems, and enterprise workflows.

---

## 1. Financial Application Testing

### Transaction Manipulation

```python
# financial_testing.py
import subprocess
import json
import time
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

class FinancialSecurityTester:
    """Financial application business logic testing"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.findings = []
    
    def curl(self, endpoint: str, method: str = "GET", 
             data: Dict = None) -> Dict:
        """Execute API request"""
        url = f"{self.base_url}{endpoint}"
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json"]
        
        if data:
            cmd.extend(["-d", json.dumps(data)])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        lines = output.rsplit("\n", 1)
        
        try:
            body = json.loads(lines[0]) if len(lines) > 1 else {}
        except:
            body = {"raw": lines[0] if lines else ""}
        
        return {
            "status": int(lines[-1]) if lines[-1].isdigit() else 0,
            "body": body
        }
    
    # ==================
    # Amount Manipulation
    # ==================
    
    def test_negative_amounts(self, transfer_endpoint: str) -> List[Dict]:
        """Test if negative amounts are accepted"""
        print("[*] Testing negative amount transfers...")
        
        findings = []
        test_amounts = [-1, -100, -0.01, -999999]
        
        for amount in test_amounts:
            response = self.curl(transfer_endpoint, "POST", {
                "amount": amount,
                "from_account": "user_account",
                "to_account": "target_account"
            })
            
            if response["status"] == 200:
                findings.append({
                    "type": "Negative Amount Transfer",
                    "severity": "CRITICAL",
                    "endpoint": transfer_endpoint,
                    "payload": {"amount": amount},
                    "description": "Application accepts negative amounts, allowing reverse transfers"
                })
                print(f"[!] Negative amount {amount} accepted!")
        
        return findings
    
    def test_float_precision(self, transfer_endpoint: str) -> List[Dict]:
        """Test floating point precision issues"""
        print("[*] Testing float precision manipulation...")
        
        findings = []
        
        # Precision attacks
        test_amounts = [
            0.00000001,  # Very small
            0.1 + 0.2,   # Classic float issue (0.30000000000000004)
            99999999999999.99,  # Very large
            1e308,  # Near max float
            "1e-308",  # String scientific notation
        ]
        
        for amount in test_amounts:
            response = self.curl(transfer_endpoint, "POST", {
                "amount": amount,
                "from_account": "user_account",
                "to_account": "target_account"
            })
            
            if response["status"] == 200:
                findings.append({
                    "type": "Float Precision Vulnerability",
                    "severity": "HIGH",
                    "endpoint": transfer_endpoint,
                    "payload": {"amount": amount}
                })
        
        return findings
    
    def test_currency_rounding(self, endpoint: str) -> List[Dict]:
        """Test currency rounding exploitation"""
        print("[*] Testing currency rounding issues...")
        
        findings = []
        
        # Perform many small transactions that might round favorably
        small_amount = 0.001  # Below display precision
        
        # Check initial balance
        balance_before = self.curl("/api/account/balance")
        
        # Perform 1000 micro-transactions
        for _ in range(100):
            self.curl(endpoint, "POST", {"amount": small_amount})
        
        # Check final balance
        balance_after = self.curl("/api/account/balance")
        
        # Analyze for rounding profit
        # Would compare expected vs actual
        
        return findings
    
    # ==================
    # Race Conditions
    # ==================
    
    def test_race_condition(self, endpoint: str, data: Dict,
                           threads: int = 50) -> Dict:
        """Test for race condition vulnerabilities"""
        print(f"[*] Testing race condition with {threads} parallel requests...")
        
        results = []
        
        def make_request():
            return self.curl(endpoint, "POST", data)
        
        start = time.time()
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(make_request) for _ in range(threads)]
            results = [f.result() for f in futures]
        elapsed = time.time() - start
        
        successful = sum(1 for r in results if r["status"] == 200)
        
        finding = {
            "type": "Race Condition",
            "endpoint": endpoint,
            "threads": threads,
            "successful": successful,
            "time": elapsed,
            "vulnerable": successful > 1
        }
        
        if successful > 1:
            finding["severity"] = "CRITICAL"
            finding["description"] = f"Race condition allowed {successful} successful operations instead of 1"
            print(f"[!] Race condition: {successful}/{threads} requests succeeded!")
        
        return finding
    
    def test_double_spending(self, balance: float) -> Dict:
        """Test for double-spending vulnerability"""
        print("[*] Testing double-spending...")
        
        # Try to spend entire balance multiple times simultaneously
        return self.test_race_condition(
            "/api/transfer",
            {"amount": balance, "to_account": "attacker"},
            threads=20
        )
    
    def test_overdraft(self, transfer_endpoint: str) -> List[Dict]:
        """Test for overdraft/insufficient funds bypass"""
        print("[*] Testing overdraft bypass...")
        
        findings = []
        
        # Get current balance
        balance = self.curl("/api/account/balance")
        current_balance = balance["body"].get("balance", 0)
        
        # Try to transfer more than balance
        test_amounts = [
            current_balance + 1,
            current_balance + 100,
            current_balance * 2,
            current_balance + 0.01,
            999999999
        ]
        
        for amount in test_amounts:
            response = self.curl(transfer_endpoint, "POST", {
                "amount": amount,
                "to_account": "target"
            })
            
            if response["status"] == 200:
                findings.append({
                    "type": "Overdraft/Insufficient Funds Bypass",
                    "severity": "CRITICAL",
                    "endpoint": transfer_endpoint,
                    "balance": current_balance,
                    "amount_transferred": amount
                })
                print(f"[!] Overdraft: transferred {amount} with balance {current_balance}!")
        
        return findings
    
    # ==================
    # Transaction Integrity
    # ==================
    
    def test_transaction_replay(self, transaction_id: str) -> Dict:
        """Test if transactions can be replayed"""
        print("[*] Testing transaction replay...")
        
        # Attempt to replay the transaction
        for _ in range(5):
            response = self.curl(f"/api/transaction/{transaction_id}/execute", "POST")
            
            if response["status"] == 200:
                return {
                    "type": "Transaction Replay",
                    "severity": "CRITICAL",
                    "transaction_id": transaction_id,
                    "description": "Transaction can be executed multiple times"
                }
        
        return {"vulnerable": False}
    
    def test_parameter_tampering(self, endpoint: str) -> List[Dict]:
        """Test for parameter tampering in transactions"""
        print("[*] Testing parameter tampering...")
        
        findings = []
        
        # Hidden/extra parameters that might affect transaction
        tamper_params = [
            {"fee": 0},
            {"fee": -10},
            {"commission": 0},
            {"tax": 0},
            {"exchange_rate": 0.01},
            {"currency": "XXX"},
            {"priority": "high"},
            {"verified": True},
            {"approved": True},
            {"status": "completed"}
        ]
        
        base_transaction = {
            "amount": 100,
            "to_account": "target"
        }
        
        for params in tamper_params:
            test_data = {**base_transaction, **params}
            response = self.curl(endpoint, "POST", test_data)
            
            if response["status"] == 200:
                # Check if param was accepted
                if any(k in str(response["body"]) for k in params.keys()):
                    findings.append({
                        "type": "Parameter Tampering",
                        "severity": "HIGH",
                        "endpoint": endpoint,
                        "tampered_params": params
                    })
        
        return findings
```

---

## 2. E-Commerce Testing

### Shopping Cart & Checkout

```python
# ecommerce_testing.py
import subprocess
import json
from typing import Dict, List

class ECommerceSecurityTester:
    """E-commerce business logic testing"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.findings = []
    
    def curl(self, endpoint: str, method: str = "GET",
             data: Dict = None) -> Dict:
        """Execute API request"""
        url = f"{self.base_url}{endpoint}"
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json"]
        
        if data:
            cmd.extend(["-d", json.dumps(data)])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        lines = output.rsplit("\n", 1)
        
        try:
            body = json.loads(lines[0]) if len(lines) > 1 else {}
        except:
            body = {"raw": lines[0] if lines else ""}
        
        return {
            "status": int(lines[-1]) if lines[-1].isdigit() else 0,
            "body": body
        }
    
    # ==================
    # Price Manipulation
    # ==================
    
    def test_price_manipulation(self, add_to_cart_endpoint: str,
                                product_id: str) -> List[Dict]:
        """Test for price manipulation in cart"""
        print("[*] Testing price manipulation...")
        
        findings = []
        
        # Get actual product price
        product = self.curl(f"/api/products/{product_id}")
        actual_price = product["body"].get("price", 100)
        
        # Try to add with different price
        test_prices = [0, 0.01, 1, -10, actual_price - 50, "free"]
        
        for price in test_prices:
            response = self.curl(add_to_cart_endpoint, "POST", {
                "product_id": product_id,
                "quantity": 1,
                "price": price
            })
            
            if response["status"] == 200:
                # Check cart to see if price was accepted
                cart = self.curl("/api/cart")
                cart_price = cart["body"].get("items", [{}])[0].get("price")
                
                if cart_price != actual_price:
                    findings.append({
                        "type": "Price Manipulation",
                        "severity": "CRITICAL",
                        "endpoint": add_to_cart_endpoint,
                        "actual_price": actual_price,
                        "manipulated_price": price
                    })
                    print(f"[!] Price manipulation: {actual_price} -> {price}")
        
        return findings
    
    def test_quantity_manipulation(self, endpoint: str,
                                   product_id: str) -> List[Dict]:
        """Test for quantity manipulation attacks"""
        print("[*] Testing quantity manipulation...")
        
        findings = []
        
        test_quantities = [
            -1,           # Negative
            0,            # Zero
            0.5,          # Decimal
            9999999,      # Very large
            "1",          # String
            {"$gt": 0},   # NoSQL injection
        ]
        
        for qty in test_quantities:
            response = self.curl(endpoint, "POST", {
                "product_id": product_id,
                "quantity": qty
            })
            
            if response["status"] == 200:
                findings.append({
                    "type": "Quantity Manipulation",
                    "severity": "HIGH" if qty < 0 else "MEDIUM",
                    "endpoint": endpoint,
                    "quantity": qty
                })
        
        return findings
    
    # ==================
    # Discount & Coupon Abuse
    # ==================
    
    def test_coupon_stacking(self, apply_coupon_endpoint: str,
                             coupons: List[str]) -> Dict:
        """Test if multiple coupons can be stacked"""
        print("[*] Testing coupon stacking...")
        
        # Clear cart and add item
        self.curl("/api/cart", "DELETE")
        self.curl("/api/cart", "POST", {"product_id": "test_product", "quantity": 1})
        
        # Apply multiple coupons
        applied = []
        for coupon in coupons:
            response = self.curl(apply_coupon_endpoint, "POST", {"code": coupon})
            if response["status"] == 200:
                applied.append(coupon)
        
        if len(applied) > 1:
            return {
                "type": "Coupon Stacking",
                "severity": "HIGH",
                "coupons_applied": applied,
                "description": f"Successfully stacked {len(applied)} coupons"
            }
        
        return {"vulnerable": False}
    
    def test_coupon_reuse(self, apply_coupon_endpoint: str,
                          coupon: str) -> Dict:
        """Test if single-use coupons can be reused"""
        print("[*] Testing coupon reuse...")
        
        successful_uses = 0
        
        for i in range(5):
            # New cart each time
            self.curl("/api/cart", "DELETE")
            self.curl("/api/cart", "POST", {"product_id": "test", "quantity": 1})
            
            response = self.curl(apply_coupon_endpoint, "POST", {"code": coupon})
            
            if response["status"] == 200:
                # Complete checkout
                self.curl("/api/checkout", "POST")
                successful_uses += 1
        
        if successful_uses > 1:
            return {
                "type": "Coupon Reuse",
                "severity": "HIGH",
                "coupon": coupon,
                "uses": successful_uses
            }
        
        return {"vulnerable": False}
    
    def test_discount_bypass(self, checkout_endpoint: str) -> List[Dict]:
        """Test for discount calculation bypass"""
        print("[*] Testing discount bypass...")
        
        findings = []
        
        # Try to set discount directly
        tamper_params = [
            {"discount": 100},
            {"discount_percent": 100},
            {"total": 0},
            {"final_price": 0.01},
            {"promo_applied": True},
            {"coupon_discount": 9999}
        ]
        
        for params in tamper_params:
            response = self.curl(checkout_endpoint, "POST", params)
            
            if response["status"] == 200:
                order = response["body"]
                if order.get("total", 100) < 1:
                    findings.append({
                        "type": "Discount Bypass",
                        "severity": "CRITICAL",
                        "params": params,
                        "final_total": order.get("total")
                    })
        
        return findings
    
    # ==================
    # Inventory Manipulation
    # ==================
    
    def test_limited_stock_bypass(self, product_id: str,
                                   stock_limit: int = 1) -> Dict:
        """Test if limited stock can be bypassed via race condition"""
        print("[*] Testing limited stock bypass...")
        
        from concurrent.futures import ThreadPoolExecutor
        
        def add_to_cart():
            return self.curl("/api/cart", "POST", {
                "product_id": product_id,
                "quantity": 1
            })
        
        # Race to add limited item
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(add_to_cart) for _ in range(20)]
            results = [f.result() for f in futures]
        
        successful = sum(1 for r in results if r["status"] == 200)
        
        if successful > stock_limit:
            return {
                "type": "Limited Stock Bypass",
                "severity": "HIGH",
                "product_id": product_id,
                "stock_limit": stock_limit,
                "successful_adds": successful
            }
        
        return {"vulnerable": False}
    
    # ==================
    # Checkout Flow
    # ==================
    
    def test_checkout_step_skip(self, steps: List[str]) -> List[Dict]:
        """Test if checkout steps can be skipped"""
        print("[*] Testing checkout step bypass...")
        
        findings = []
        
        # Try to access each step directly
        for i, step in enumerate(steps):
            # Skip earlier steps, go directly to this one
            response = self.curl(step, "POST", {"skip_validation": True})
            
            if response["status"] == 200:
                findings.append({
                    "type": "Checkout Step Bypass",
                    "severity": "HIGH",
                    "skipped_steps": steps[:i],
                    "accessed_step": step
                })
        
        # Try to access final step (order confirmation) directly
        response = self.curl("/api/checkout/complete", "POST")
        if response["status"] == 200:
            findings.append({
                "type": "Checkout Bypass",
                "severity": "CRITICAL",
                "description": "Order can be completed without payment"
            })
        
        return findings
    
    def test_payment_amount_mismatch(self) -> Dict:
        """Test if payment amount can differ from cart total"""
        print("[*] Testing payment amount mismatch...")
        
        # Get cart total
        cart = self.curl("/api/cart")
        cart_total = cart["body"].get("total", 100)
        
        # Try to pay less
        response = self.curl("/api/payment/process", "POST", {
            "amount": 0.01,
            "cart_id": cart["body"].get("id")
        })
        
        if response["status"] == 200:
            return {
                "type": "Payment Amount Mismatch",
                "severity": "CRITICAL",
                "cart_total": cart_total,
                "paid_amount": 0.01
            }
        
        return {"vulnerable": False}
```

---

## 3. Workflow Testing

### State Machine Analysis

```python
# workflow_testing.py
import subprocess
import json
from typing import Dict, List, Set
from collections import defaultdict

class WorkflowSecurityTester:
    """Workflow and state machine testing"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.state_transitions = defaultdict(list)
        self.findings = []
    
    def curl(self, endpoint: str, method: str = "GET",
             data: Dict = None) -> Dict:
        """Execute API request"""
        url = f"{self.base_url}{endpoint}"
        cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
               "-H", f"Authorization: Bearer {self.token}",
               "-H", "Content-Type: application/json"]
        
        if data:
            cmd.extend(["-d", json.dumps(data)])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        lines = output.rsplit("\n", 1)
        
        try:
            body = json.loads(lines[0]) if len(lines) > 1 else {}
        except:
            body = {}
        
        return {
            "status": int(lines[-1]) if lines[-1].isdigit() else 0,
            "body": body
        }
    
    # ==================
    # State Manipulation
    # ==================
    
    def test_state_tampering(self, resource_endpoint: str,
                             valid_states: List[str]) -> List[Dict]:
        """Test if resource state can be directly manipulated"""
        print("[*] Testing state tampering...")
        
        findings = []
        
        for state in valid_states:
            response = self.curl(resource_endpoint, "PATCH", {"status": state})
            
            if response["status"] == 200:
                new_state = response["body"].get("status")
                if new_state == state:
                    findings.append({
                        "type": "State Tampering",
                        "severity": "HIGH",
                        "endpoint": resource_endpoint,
                        "tampered_state": state
                    })
        
        return findings
    
    def test_state_skip(self, resource_endpoint: str,
                        workflow_actions: Dict[str, str]) -> List[Dict]:
        """Test if workflow states can be skipped"""
        print("[*] Testing workflow state skip...")
        
        findings = []
        
        # workflow_actions = {
        #   "submit": "/api/orders/{id}/submit",
        #   "approve": "/api/orders/{id}/approve",
        #   "ship": "/api/orders/{id}/ship",
        #   "complete": "/api/orders/{id}/complete"
        # }
        
        # Create new resource
        create_response = self.curl(resource_endpoint, "POST", {"name": "test"})
        resource_id = create_response["body"].get("id")
        
        if not resource_id:
            return findings
        
        # Try to skip to each action without completing prior steps
        actions = list(workflow_actions.items())
        
        for i, (action_name, action_endpoint) in enumerate(actions):
            if i == 0:
                continue  # Skip first action
            
            endpoint = action_endpoint.replace("{id}", str(resource_id))
            response = self.curl(endpoint, "POST")
            
            if response["status"] == 200:
                skipped = [a[0] for a in actions[:i]]
                findings.append({
                    "type": "Workflow State Skip",
                    "severity": "HIGH",
                    "action": action_name,
                    "skipped_actions": skipped
                })
                print(f"[!] Skipped to {action_name}, bypassing {skipped}")
        
        return findings
    
    def test_reverse_state_transition(self, resource_endpoint: str,
                                       resource_id: str,
                                       transitions: Dict) -> List[Dict]:
        """Test if state can be reversed after progression"""
        print("[*] Testing reverse state transitions...")
        
        findings = []
        
        # Get current state
        resource = self.curl(f"{resource_endpoint}/{resource_id}")
        current_state = resource["body"].get("status")
        
        # Try to revert to previous states
        for state, action in transitions.items():
            if state == current_state:
                continue
            
            response = self.curl(f"{resource_endpoint}/{resource_id}", "PATCH", 
                               {"status": state})
            
            if response["status"] == 200:
                findings.append({
                    "type": "Reverse State Transition",
                    "severity": "MEDIUM",
                    "from_state": current_state,
                    "to_state": state
                })
        
        return findings
    
    # ==================
    # Time-Based Logic
    # ==================
    
    def test_expiration_bypass(self, resource_endpoint: str,
                               resource_id: str) -> Dict:
        """Test if time-based expirations can be bypassed"""
        print("[*] Testing expiration bypass...")
        
        # Try to use expired resource
        response = self.curl(f"{resource_endpoint}/{resource_id}/use", "POST")
        
        if response["status"] == 200:
            return {
                "type": "Expiration Bypass",
                "severity": "HIGH",
                "resource_id": resource_id,
                "description": "Expired resource still usable"
            }
        
        # Try to extend expiration
        response = self.curl(f"{resource_endpoint}/{resource_id}", "PATCH", {
            "expires_at": "2099-12-31T23:59:59Z"
        })
        
        if response["status"] == 200:
            return {
                "type": "Expiration Tampering",
                "severity": "HIGH",
                "description": "Expiration date can be modified"
            }
        
        return {"vulnerable": False}
    
    def test_time_window_bypass(self, action_endpoint: str,
                                 valid_window: Dict) -> Dict:
        """Test if time window restrictions can be bypassed"""
        print("[*] Testing time window bypass...")
        
        # Try action outside valid window
        response = self.curl(action_endpoint, "POST", {
            "timestamp": "2020-01-01T00:00:00Z"  # Past time
        })
        
        if response["status"] == 200:
            return {
                "type": "Time Window Bypass",
                "severity": "MEDIUM",
                "description": "Action accepted with manipulated timestamp"
            }
        
        return {"vulnerable": False}
    
    # ==================
    # Approval Workflow
    # ==================
    
    def test_self_approval(self, approval_endpoint: str,
                           resource_id: str) -> Dict:
        """Test if users can approve their own requests"""
        print("[*] Testing self-approval...")
        
        response = self.curl(f"{approval_endpoint}/{resource_id}/approve", "POST")
        
        if response["status"] == 200:
            return {
                "type": "Self-Approval",
                "severity": "HIGH",
                "resource_id": resource_id,
                "description": "User can approve their own request"
            }
        
        return {"vulnerable": False}
    
    def test_approval_bypass(self, create_endpoint: str,
                             resource_data: Dict) -> Dict:
        """Test if approval requirements can be bypassed"""
        print("[*] Testing approval bypass...")
        
        # Try to create with pre-approved status
        data_with_approved = {
            **resource_data,
            "status": "approved",
            "approved": True,
            "approval_status": "approved"
        }
        
        response = self.curl(create_endpoint, "POST", data_with_approved)
        
        if response["status"] == 200:
            status = response["body"].get("status")
            if status == "approved":
                return {
                    "type": "Approval Bypass",
                    "severity": "CRITICAL",
                    "description": "Resource created with pre-approved status"
                }
        
        return {"vulnerable": False}
```

---

## 4. Integrated Business Logic Tester

```python
# business_logic_test.py
"""
Comprehensive business logic testing
"""

import json
import sys
from typing import Dict, List

def run_business_logic_tests(target: str, token: str,
                             app_type: str = "ecommerce") -> Dict:
    """Run comprehensive business logic tests"""
    
    all_findings = []
    
    if app_type == "financial":
        print("\n" + "="*60)
        print("FINANCIAL APPLICATION TESTING")
        print("="*60)
        
        from financial_testing import FinancialSecurityTester
        tester = FinancialSecurityTester(target, token)
        
        # Amount manipulation
        all_findings.extend(tester.test_negative_amounts("/api/transfer"))
        all_findings.extend(tester.test_float_precision("/api/transfer"))
        
        # Race conditions
        race_result = tester.test_race_condition("/api/transfer", {
            "amount": 100,
            "to_account": "target"
        })
        if race_result.get("vulnerable"):
            all_findings.append(race_result)
        
        # Overdraft
        all_findings.extend(tester.test_overdraft("/api/transfer"))
        
    elif app_type == "ecommerce":
        print("\n" + "="*60)
        print("E-COMMERCE APPLICATION TESTING")
        print("="*60)
        
        from ecommerce_testing import ECommerceSecurityTester
        tester = ECommerceSecurityTester(target, token)
        
        # Price manipulation
        all_findings.extend(tester.test_price_manipulation(
            "/api/cart/add", "test_product"
        ))
        
        # Quantity manipulation
        all_findings.extend(tester.test_quantity_manipulation(
            "/api/cart/add", "test_product"
        ))
        
        # Coupon abuse
        coupon_stack = tester.test_coupon_stacking(
            "/api/cart/apply-coupon",
            ["DISCOUNT10", "WELCOME20", "SAVE30"]
        )
        if coupon_stack.get("vulnerable", True):
            all_findings.append(coupon_stack)
        
        # Checkout bypass
        all_findings.extend(tester.test_checkout_step_skip([
            "/api/checkout/cart",
            "/api/checkout/shipping",
            "/api/checkout/payment",
            "/api/checkout/confirm"
        ]))
    
    elif app_type == "workflow":
        print("\n" + "="*60)
        print("WORKFLOW APPLICATION TESTING")
        print("="*60)
        
        from workflow_testing import WorkflowSecurityTester
        tester = WorkflowSecurityTester(target, token)
        
        # State tampering
        all_findings.extend(tester.test_state_tampering(
            "/api/orders/123",
            ["pending", "approved", "shipped", "completed", "cancelled"]
        ))
        
        # Workflow skip
        all_findings.extend(tester.test_state_skip(
            "/api/orders",
            {
                "submit": "/api/orders/{id}/submit",
                "approve": "/api/orders/{id}/approve",
                "ship": "/api/orders/{id}/ship",
                "complete": "/api/orders/{id}/complete"
            }
        ))
    
    # Save findings
    with open("/tmp/casperpro/business_logic_findings.json", "w") as f:
        json.dump(all_findings, f, indent=2)
    
    print(f"\n[+] Business logic testing complete")
    print(f"    Findings: {len(all_findings)}")
    
    return {"findings": all_findings}

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    token = sys.argv[2] if len(sys.argv) > 2 else ""
    app_type = sys.argv[3] if len(sys.argv) > 3 else "ecommerce"
    
    run_business_logic_tests(target, token, app_type)
```

---

## Summary

| Test Category | Attack Types | Severity |
|---------------|--------------|----------|
| **Amount Manipulation** | Negative amounts, float precision, rounding | Critical |
| **Race Conditions** | Double spending, inventory bypass | Critical |
| **Price Manipulation** | Direct price change, discount bypass | Critical |
| **Coupon Abuse** | Stacking, reuse, code enumeration | High |
| **Workflow Bypass** | State skip, reverse transitions | High |
| **Approval Bypass** | Self-approval, pre-approved creation | Critical |

---

**This module covers comprehensive business logic testing for enterprise applications with complex financial, e-commerce, and workflow requirements.**
