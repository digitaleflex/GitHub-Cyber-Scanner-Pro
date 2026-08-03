"""Premium Threat Intelligence APIs — VirusTotal, SecurityTrails, Shodan.

Three industry-standard APIs bringing billions of data points:
  VirusTotal:     2B+ files, 70+ AV engines, IP/domain/URL analysis
  SecurityTrails: 4B+ DNS records, 1B+ domains, 500M+ certificates  
  Shodan:         5B+ internet-connected devices, banners, vulns

Free tiers: VT (500 req/day, 4/min), ST (50 req/month), Shodan (50 req)
Pro tiers:  VT Enterprise ($100K/yr), ST API ($49/mo), Shodan ($69/mo)
"""

import os
import json
import logging
import hashlib
import requests
import time
from datetime import datetime
from typing import Optional
from src.database import get_db_connection

# ── API Keys (from env) ─────────────────────────────────────────────────

_LAST_VT_CALL = 0.0

def _vt_rate_limit():
    """Respect VirusTotal free tier: 4 req/min."""
    global _LAST_VT_CALL
    elapsed = time.time() - _LAST_VT_CALL
    if elapsed < 15:  # 4/min = 15s between calls
        time.sleep(15 - elapsed)
    _LAST_VT_CALL = time.time()


# ══════════════════════════════════════════════════════════════════════════
# VIRUSTOTAL API
# ══════════════════════════════════════════════════════════════════════════

def virustotal_lookup(identifier: str, resource_type: str = "auto") -> dict:
    """Lookup IP, domain, URL, or hash on VirusTotal."""
    api_key = os.getenv("VIRUSTOTAL_API_KEY", "")
    if not api_key:
        return {"error": "VIRUSTOTAL_API_KEY not configured"}

    _vt_rate_limit()
    base = "https://www.virustotal.com/api/v3"

    try:
        if resource_type == "auto":
            if "." in identifier and not identifier.startswith("http"):
                resource_type = "ip_address" if all(p.isdigit() for p in identifier.split(".") if p) else "domain"
            elif len(identifier) in (32, 40, 64) and all(c in "0123456789abcdefABCDEF" for c in identifier):
                resource_type = "file"
            else:
                resource_type = "url"
                identifier = identifier if identifier.startswith("http") else f"https://{identifier}"

        if resource_type == "url":
            url_id = hashlib.sha256(identifier.encode()).hexdigest()[:64]
            endpoint = f"{base}/urls/{url_id}"
        else:
            endpoint = f"{base}/{resource_type}s/{identifier}"

        r = requests.get(endpoint, headers={"x-apikey": api_key, "Accept": "application/json"}, timeout=15)
        if r.status_code == 404:
            return {"error": "Not found on VirusTotal", "identifier": identifier}
        data = r.json()

        attrs = data.get("data", {}).get("attributes", {})
        stats = attrs.get("last_analysis_stats", {})
        total = sum(stats.values()) if stats else 0

        result = {
            "identifier": identifier,
            "type": resource_type,
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless": stats.get("harmless", 0),
            "undetected": stats.get("undetected", 0),
            "total_engines": total,
            "reputation": attrs.get("reputation", 0),
            "last_analysis_date": attrs.get("last_analysis_date"),
            "categories": attrs.get("categories", {}),
            "tags": attrs.get("tags", []),
            "country": attrs.get("country"),
            "as_owner": attrs.get("as_owner"),
        }
        return result
    except Exception as e:
        return {"error": str(e), "identifier": identifier}


def virustotal_enrich_iocs(limit: int = 20) -> int:
    """Enrichir les IOCs existants (IPs, domaines) via VirusTotal."""
    api_key = os.getenv("VIRUSTOTAL_API_KEY", "")
    if not api_key:
        logging.warning("⚠️ VirusTotal: pas d'API key")
        return 0

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, value, ioc_type FROM ioc_feed WHERE source != 'virustotal' AND ioc_type IN ('ipv4', 'domain', 'url') LIMIT %s",
        (limit,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    enriched = 0
    for row in rows:
        ioc_id, value, ioc_type = row
        result = virustotal_lookup(value, ioc_type if ioc_type != "ipv4" else "ip_address")
        if "error" not in result:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO ioc_feed (source, value, ioc_type, threat_type, tags, status, raw_json) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (value) DO UPDATE SET threat_type = EXCLUDED.threat_type, tags = EXCLUDED.tags",
                ("virustotal", value, ioc_type,
                 f"{result.get('malicious',0)}/{result.get('total_engines',0)} engines",
                 json.dumps(result.get("tags", [])),
                 "malicious" if result.get("malicious", 0) > 5 else "clean",
                 json.dumps(result)[:2000])
            )
            conn.commit()
            cur.close()
            conn.close()
            enriched += 1
    logging.info(f"🛡️ VirusTotal: {enriched} IOCs enriched")
    return enriched


# ══════════════════════════════════════════════════════════════════════════
# SECURITYTRAILS API
# ══════════════════════════════════════════════════════════════════════════

def securitytrails_domain(domain: str) -> dict:
    """Passive DNS, subdomains, WHOIS, history for a domain."""
    api_key = os.getenv("SECURITYTRAILS_API_KEY", "")
    if not api_key:
        return {"error": "SECURITYTRAILS_API_KEY not configured"}

    base = "https://api.securitytrails.com/v1"
    headers = {"APIKEY": api_key, "Accept": "application/json"}

    result = {"domain": domain}

    # Passive DNS
    try:
        r = requests.get(f"{base}/domain/{domain}", headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            result["alexa_rank"] = data.get("alexa_rank")
            result["host_provider"] = ", ".join(data.get("host_provider", []))
            result["mx_records"] = data.get("current_dns", {}).get("mx", {}).get("values", [])[:5]
            result["ns_records"] = data.get("current_dns", {}).get("ns", {}).get("values", [])[:5]
            result["a_records"] = data.get("current_dns", {}).get("a", {}).get("values", [])[:10]
    except Exception as e:
        result["dns_error"] = str(e)

    # Subdomains
    try:
        r = requests.get(f"{base}/domain/{domain}/subdomains", headers=headers, timeout=15)
        if r.status_code == 200:
            subs = r.json().get("subdomains", [])
            result["subdomain_count"] = len(subs)
            result["subdomains"] = [f"{s}.{domain}" for s in subs[:30]]
    except Exception as e:
        result["subdomains_error"] = str(e)

    # WHOIS
    try:
        r = requests.get(f"{base}/domain/{domain}/whois", headers=headers, timeout=15)
        if r.status_code == 200:
            whois = r.json().get("data", {})
            result["whois"] = {
                "registrar": whois.get("registrar"),
                "created": whois.get("createdDate"),
                "expires": whois.get("expiresDate"),
                "registrant": whois.get("registrant", {}).get("organization", "private"),
            }
    except Exception as e:
        result["whois_error"] = str(e)

    return result


def securitytrails_ip(ip: str) -> dict:
    """Reverse DNS, hosted domains, geolocation for an IP."""
    api_key = os.getenv("SECURITYTRAILS_API_KEY", "")
    if not api_key:
        return {"error": "SECURITYTRAILS_API_KEY not configured"}

    base = "https://api.securitytrails.com/v1"
    headers = {"APIKEY": api_key}

    result = {"ip": ip}
    try:
        r = requests.get(f"{base}/ips/nearby/{ip}", headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            result["hostname"] = data.get("hostname")
            result["hosting"] = data.get("current_service", {}).get("provider", "")
            result["domains_hosted"] = [d.get("hostname", "") for d in data.get("blocks", [])][:20]
    except Exception as e:
        result["error"] = str(e)

    return result


def securitytrails_ingest(limit: int = 50) -> int:
    """Ingest passive DNS data for top domains."""
    api_key = os.getenv("SECURITYTRAILS_API_KEY", "")
    if not api_key:
        logging.warning("⚠️ SecurityTrails: pas d'API key")
        return 0

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT value FROM ioc_feed WHERE ioc_type = 'domain' LIMIT %s",
        (limit,)
    )
    domains = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()

    ingested = 0
    for domain in domains[:limit]:
        data = securitytrails_domain(domain)
        if "error" not in data:
            a_records = data.get("a_records", [])
            for rec in a_records:
                if isinstance(rec, dict):
                    ip = rec.get("ip", "")
                else:
                    ip = str(rec)
                if ip:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO ioc_feed (source, value, ioc_type, threat_type, tags, raw_json) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (value) DO NOTHING",
                        ("securitytrails", ip, "ipv4", f"DNS for {domain}", f"subdomains:{data.get('subdomain_count', 0)}", json.dumps(data)[:2000])
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    ingested += 1
    logging.info(f"🔐 SecurityTrails: {ingested} IPs/resolved from {len(domains)} domains")
    return ingested


# ══════════════════════════════════════════════════════════════════════════
# SHODAN API
# ══════════════════════════════════════════════════════════════════════════

def shodan_host(ip: str) -> dict:
    """Get all Shodan information on a specific IP."""
    api_key = os.getenv("SHODAN_API_KEY", "")
    if not api_key:
        return {"error": "SHODAN_API_KEY not configured"}

    try:
        r = requests.get(
            f"https://api.shodan.io/shodan/host/{ip}",
            params={"key": api_key, "minify": "false"},
            timeout=15
        )
        if r.status_code == 404:
            return {"error": "Not found on Shodan", "ip": ip}
        data = r.json()

        services = []
        for svc in data.get("data", []):
            services.append({
                "port": svc.get("port"),
                "transport": svc.get("transport"),
                "product": svc.get("product", ""),
                "version": svc.get("version", ""),
                "banner": (svc.get("data", "") or "")[:200],
            })

        vulns = data.get("vulns", [])
        result = {
            "ip": ip,
            "org": data.get("org", ""),
            "isp": data.get("isp", ""),
            "os": data.get("os"),
            "country": data.get("country_name", ""),
            "city": data.get("city", ""),
            "ports": data.get("ports", []),
            "services_count": len(services),
            "services": services[:20],
            "vulnerabilities": [str(v) for v in vulns[:20]],
            "vulns_count": len(vulns),
            "last_update": data.get("last_update", ""),
            "hostnames": data.get("hostnames", [])[:10],
        }
        return result
    except Exception as e:
        return {"error": str(e), "ip": ip}


def shodan_search(query: str, limit: int = 10) -> dict:
    """Search Shodan for hosts matching a query."""
    api_key = os.getenv("SHODAN_API_KEY", "")
    if not api_key:
        return {"error": "SHODAN_API_KEY not configured"}

    try:
        r = requests.get(
            "https://api.shodan.io/shodan/host/search",
            params={"key": api_key, "query": query, "limit": limit, "minify": "true"},
            timeout=15
        )
        data = r.json()
        matches = []
        for m in data.get("matches", []):
            matches.append({
                "ip": m.get("ip_str"),
                "port": m.get("port"),
                "org": m.get("org", ""),
                "hostnames": m.get("hostnames", []),
                "product": m.get("product", ""),
                "os": m.get("os"),
                "timestamp": m.get("timestamp", ""),
            })
        return {"query": query, "total": data.get("total", 0), "matches": matches}
    except Exception as e:
        return {"error": str(e), "query": query}


def shodan_ingest(limit: int = 50) -> int:
    """Enrichir les IPs existantes via Shodan."""
    api_key = os.getenv("SHODAN_API_KEY", "")
    if not api_key:
        logging.warning("⚠️ Shodan: pas d'API key")
        return 0

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT value FROM ioc_feed WHERE ioc_type = 'ipv4' AND source != 'shodan' LIMIT %s",
        (limit,)
    )
    ips = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()

    ingested = 0
    for ip in ips[:limit]:
        try:
            data = shodan_host(ip)
            if "error" not in data:
                vulns = data.get("vulnerabilities", [])
                conn = get_db_connection()
                cur = conn.cursor()
                for vuln in vulns:
                    cur.execute(
                        "INSERT INTO ioc_feed (source, value, ioc_type, threat_type, tags, raw_json) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (value) DO NOTHING",
                        ("shodan", vuln, "cve", f"Shodan vuln on {ip}", f"ports:{','.join(map(str, data.get('ports',[])))}", "")
                    )
                cur.execute(
                    "INSERT INTO ioc_feed (source, value, ioc_type, threat_type, tags, status, raw_json) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (value) DO UPDATE SET threat_type = EXCLUDED.threat_type",
                    ("shodan", ip, "ipv4",
                     data.get("org", ""),
                     f"ports:{len(data.get('ports',[]))} vulns:{len(vulns)}",
                     "active" if data.get("services_count", 0) > 0 else "idle",
                     json.dumps(data)[:2000])
                )
                conn.commit()
                cur.close()
                conn.close()
                ingested += 1
        except Exception as e:
            logging.error(f"Shodan ingest error for {ip}: {e}")

    logging.info(f"🌐 Shodan: {ingested} IPs enriched")
    return ingested


# ══════════════════════════════════════════════════════════════════════════
# UNIFIED ENRICHMENT
# ══════════════════════════════════════════════════════════════════════════

def enrich_all(limit: int = 20) -> dict:
    """Run all premium API enrichments on existing IOCs."""
    results = {}
    results["virustotal"] = virustotal_enrich_iocs(limit)
    results["securitytrails"] = securitytrails_ingest(limit)
    results["shodan"] = shodan_ingest(limit)
    results["total"] = sum(results.values())
    logging.info(f"💎 Premium enrichment: {results}")
    return results

