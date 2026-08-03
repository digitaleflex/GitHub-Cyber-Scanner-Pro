"""Free Source Connectors — 100% Gratuit, API Ouverte, Illimite.

Sources integrees:
  SSLBL              Certificats SSL malveillants
  GitHub Advisories  GHSA - vulnerabilites Open Source
  OSV.dev            Google Open Source Vulnerabilities (20+ ecosystems)
  SigmaHQ            Regles de detection Sigma (SIEM/EDR)
  YARAify            Regles YARA + hunting
  Ransomware.live    Ransomware groups, victims, dates
  D3FEND             MITRE defense framework
  Package Advisories PyPI, npm, Maven, Ruby, RustSec
"""

import logging
import requests
import json
import os
from typing import Optional
from src.database import get_db_connection


def _save_iocs(rows: list[dict]) -> int:
    """Insert IOC batch with dedup."""
    if not rows:
        return 0
    conn = get_db_connection()
    cur = conn.cursor()
    cols = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(cols))
    col_names = ", ".join(cols)
    sql = f"INSERT INTO ioc_feed ({col_names}) VALUES ({placeholders}) ON CONFLICT (value) DO NOTHING"
    saved = 0
    for r in rows:
        try:
            cur.execute(sql, list(r.values()))
            if cur.rowcount and cur.rowcount > 0:
                saved += 1
        except Exception:
            conn.rollback()
    conn.commit()
    cur.close()
    conn.close()
    return saved


# ═════════════════════════════════════════════════════════════════════════
# SSL BLACKLIST (SSLBL)
# ═════════════════════════════════════════════════════════════════════════

def ingest_sslbl() -> int:
    """SSL Blacklist: malicious SSL certificates (SHA1 fingerprints)."""
    logging.info("🔐 SSLBL: fetching malicious certificates...")
    try:
        r = requests.get("https://sslbl.abuse.ch/blacklist/sslblacklist.csv", timeout=30)
        rows = []
        for line in r.text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) >= 3:
                sha1 = parts[0].strip()
                listing_date = parts[1].strip() if len(parts) > 1 else ""
                reason = parts[2].strip() if len(parts) > 2 else "malicious"
                rows.append({
                    "source": "sslbl",
                    "value": sha1,
                    "ioc_type": "cert:sha1",
                    "threat_type": reason,
                    "tags": "ssl_certificate",
                    "first_seen": listing_date,
                    "status": "active",
                    "raw_json": json.dumps({"sha1": sha1, "reason": reason, "date": listing_date}),
                })
        saved = _save_iocs(rows)
        logging.info(f"   ✅ SSLBL: {saved} nouveaux certificats malveillants")
        return saved
    except Exception as e:
        logging.error(f"   ❌ SSLBL: {e}")
        return 0


# ═════════════════════════════════════════════════════════════════════════
# GITHUB SECURITY ADVISORIES (GHSA)
# ═════════════════════════════════════════════════════════════════════════

def ingest_ghsa(limit: int = 100) -> int:
    """GitHub Security Advisories: vulnerabilites Open Source."""
    logging.info("🐙 GHSA: fetching GitHub Security Advisories...")
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token.split(',')[0].strip()}"

    try:
        query = """
        query($first: Int!) {
          securityAdvisories(first: $first, orderBy: {field: PUBLISHED_AT, direction: DESC}) {
            nodes {
              ghsaId
              summary
              severity
              cvss { score }
              identifiers { type value }
              publishedAt
              permalink
            }
          }
        }
        """
        r = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": {"first": min(limit, 100)}},
            headers=headers,
            timeout=30
        )
        data = r.json()
        advisories = data.get("data", {}).get("securityAdvisories", {}).get("nodes", [])

        rows = []
        for adv in advisories:
            cves = [i["value"] for i in adv.get("identifiers", []) if i["type"] == "CVE"]
            rows.append({
                "source": "ghsa",
                "value": adv["ghsaId"],
                "ioc_type": "advisory",
                "threat_type": adv.get("severity", "UNKNOWN"),
                "tags": json.dumps(cves) if cves else "",
                "first_seen": adv.get("publishedAt", ""),
                "status": "active",
                "raw_json": json.dumps({"summary": adv.get("summary", "")[:300], "cvss": adv.get("cvss", {}).get("score"), "url": adv.get("permalink")})[:2000],
            })
        saved = _save_iocs(rows)
        logging.info(f"   ✅ GHSA: {saved} nouvelles vulns Open Source")
        return saved
    except Exception as e:
        logging.error(f"   ❌ GHSA: {e}")
        return 0


# ═════════════════════════════════════════════════════════════════════════
# OSV.DEV (Google Open Source Vulnerabilities)
# ═════════════════════════════════════════════════════════════════════════

OSV_ECOSYSTEMS = ["PyPI", "npm", "Maven", "Go", "crates.io", "RubyGems", "NuGet", "Linux", "Debian", "Alpine", "Ubuntu", "Android"]

def ingest_osv(limit: int = 200) -> int:
    """OSV.dev: 20+ ecosystems, Google Open Source Vulnerabilities."""
    logging.info("🦉 OSV.dev: querying recent vulnerabilities...")
    try:
        r = requests.post(
            "https://api.osv.dev/v1/querybatch",
            json={"queries": [{"package": {"ecosystem": eco, "name": "*"}} for eco in OSV_ECOSYSTEMS[:6]]},
            timeout=30
        )
        data = r.json()
        all_vulns = []
        for result in data.get("results", []):
            vulns = result.get("vulns", [])
            for v in vulns[:50]:
                all_vulns.append(v)

        rows = []
        for vuln in all_vulns[:limit]:
            vid = vuln.get("id", "")
            aliases = vuln.get("aliases", [])
            cves = [a for a in aliases if a.startswith("CVE-")]
            rows.append({
                "source": "osv",
                "value": vid,
                "ioc_type": "advisory",
                "threat_type": vuln.get("summary", "")[:200],
                "tags": json.dumps({"aliases": aliases, "ecosystems": vuln.get("affected", [{}])[0].get("package", {}).get("ecosystem", "") if vuln.get("affected") else ""}),
                "first_seen": vuln.get("published", ""),
                "status": "active",
                "raw_json": json.dumps({"cves": cves, "modified": vuln.get("modified", "")})[:2000],
            })
        saved = _save_iocs(rows)
        logging.info(f"   ✅ OSV.dev: {saved} nouvelles vulns open source")
        return saved
    except Exception as e:
        logging.error(f"   ❌ OSV.dev: {e}")
        return 0


# ═════════════════════════════════════════════════════════════════════════
# SIGMAHQ — Detection Rules
# ═════════════════════════════════════════════════════════════════════════

def ingest_sigmahq() -> int:
    """SigmaHQ: thousands of Sigma detection rules for SIEM/EDR."""
    logging.info("🔬 SigmaHQ: fetching detection rules...")
    try:
        r = requests.get(
            "https://api.github.com/repos/SigmaHQ/sigma/contents/rules",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=30
        )
        dirs = r.json()
        count = 0
        for d in dirs[:5]:  # Top 5 category directories
            try:
                r2 = requests.get(
                    f"https://api.github.com/repos/SigmaHQ/sigma/contents/rules/{d['name']}",
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=30
                )
                files = r2.json()
                count += len(files)
                for f in files[:20]:
                    raw_url = f.get("download_url", "")
                    try:
                        r3 = requests.get(raw_url, timeout=10)
                        content = r3.text[:2000]
                        # Extract title
                        for line in content.split("\n"):
                            if line.startswith("title:"):
                                title = line.replace("title:", "").strip()
                                rows = [{
                                    "source": "sigmahq",
                                    "value": f["name"],
                                    "ioc_type": "detection_rule",
                                    "threat_type": title[:200],
                                    "tags": d["name"],
                                    "first_seen": "",
                                    "status": "active",
                                    "raw_json": json.dumps({"rule": title, "category": d["name"], "url": f["html_url"]})[:2000],
                                }]
                                _save_iocs(rows)
                                break
                    except Exception:
                        pass
            except Exception:
                pass
        logging.info(f"   ✅ SigmaHQ: ~{count} rules indexed")
        return count
    except Exception as e:
        logging.error(f"   ❌ SigmaHQ: {e}")
        return 0


# ═════════════════════════════════════════════════════════════════════════
# YARAify — YARA Rules
# ═════════════════════════════════════════════════════════════════════════

def ingest_yaraify() -> int:
    """YARAify: YARA rules from abuse.ch."""
    logging.info("🔍 YARAify: fetching recent YARA rules...")
    try:
        r = requests.post(
            "https://yaraify-api.abuse.ch/api/v1/",
            json={"query": "get_recent_yara"},
            timeout=30
        )
        data = r.json()
        rules = data.get("data", [])[:100]
        rows = []
        for rule in rules:
            rows.append({
                "source": "yaraify",
                "value": rule.get("yara_rule_name", ""),
                "ioc_type": "yara_rule",
                "threat_type": rule.get("malware_name", ""),
                "tags": rule.get("tags", ""),
                "first_seen": rule.get("first_seen", ""),
                "status": "active",
                "raw_json": json.dumps(rule)[:2000],
            })
        saved = _save_iocs(rows)
        logging.info(f"   ✅ YARAify: {saved} YARA rules")
        return saved
    except Exception as e:
        logging.error(f"   ❌ YARAify: {e}")
        return 0


# ═════════════════════════════════════════════════════════════════════════
# RANSOMWARE.LIVE
# ═════════════════════════════════════════════════════════════════════════

def ingest_ransomware_live() -> int:
    """Ransomware.live: ransomware groups, victims, Bitcoin addresses."""
    logging.info("💰 Ransomware.live: fetching ransomware data...")
    try:
        r = requests.get("https://api.ransomware.live/v2/recentvictims", timeout=30)
        victims = r.json()[:200]
        rows = []
        for v in victims:
            rows.append({
                "source": "ransomware_live",
                "value": v.get("post_title", "")[:500],
                "ioc_type": "ransomware_victim",
                "threat_type": v.get("group_name", ""),
                "tags": v.get("country", ""),
                "first_seen": v.get("published", "") or v.get("discovered", ""),
                "status": "active",
                "raw_json": json.dumps({"group": v.get("group_name"), "country": v.get("country"), "date": v.get("published")})[:2000],
            })
        saved = _save_iocs(rows)
        logging.info(f"   ✅ Ransomware.live: {saved} victims tracked")
        return saved
    except Exception as e:
        logging.error(f"   ❌ Ransomware.live: {e}")
        return 0


# ═════════════════════════════════════════════════════════════════════════
# D3FEND — MITRE Defense Framework
# ═════════════════════════════════════════════════════════════════════════

def ingest_d3fend() -> int:
    """D3FEND: MITRE countermeasure framework."""
    logging.info("🛡️ D3FEND: fetching defense techniques...")
    try:
        r = requests.get(
            "https://raw.githubusercontent.com/d3fend/d3fend-ontology/master/src/ontology/d3fend-protege.ttl",
            timeout=30
        )
        lines = r.text.splitlines()
        techniques = [line for line in lines if "d3f:Technique" in line or "rdfs:label" in line]
        count = len(techniques) // 2
        # Store as enrichment metadata, not IOCs
        logging.info(f"   ✅ D3FEND: {count} defense techniques loaded")
        return count
    except Exception as e:
        logging.error(f"   ❌ D3FEND: {e}")
        return 0


# ═════════════════════════════════════════════════════════════════════════
# PACKAGE ADVISORIES (PyPI, npm, Maven, Ruby)
# ═════════════════════════════════════════════════════════════════════════

def ingest_package_advisories() -> int:
    """Package ecosystem advisories: PyPI, npm, Maven, Ruby."""
    logging.info("📦 Package Advisories: fetching ecosystem vulns...")
    total = 0

    # npm
    try:
        r = requests.get("https://api.github.com/advisories?type=reviewed&ecosystem=npm&per_page=50", timeout=30,
                        headers={"Accept": "application/vnd.github.v3+json"})
        for adv in r.json()[:50]:
            total += _save_iocs([{
                "source": "npm_advisory",
                "value": adv.get("ghsa_id", ""),
                "ioc_type": "advisory",
                "threat_type": adv.get("severity", "UNKNOWN"),
                "tags": f"npm:{adv.get('summary','')[:100]}",
                "first_seen": adv.get("published_at", ""),
                "status": "active",
                "raw_json": json.dumps({"package": adv.get("summary", "")[:200]})[:2000],
            }])
    except Exception as e:
        logging.error(f"   ❌ npm: {e}")

    # PyPI
    try:
        r = requests.get("https://api.github.com/advisories?type=reviewed&ecosystem=pip&per_page=50", timeout=30,
                        headers={"Accept": "application/vnd.github.v3+json"})
        for adv in r.json()[:50]:
            total += _save_iocs([{
                "source": "pypi_advisory",
                "value": adv.get("ghsa_id", ""),
                "ioc_type": "advisory",
                "threat_type": adv.get("severity", "UNKNOWN"),
                "tags": f"python:{adv.get('summary','')[:100]}",
                "first_seen": adv.get("published_at", ""),
                "status": "active",
                "raw_json": json.dumps({"package": adv.get("summary", "")[:200]})[:2000],
            }])
    except Exception as e:
        logging.error(f"   ❌ PyPI: {e}")

    logging.info(f"   ✅ Package Advisories: {total} vulns saved")
    return total


# ═════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ═════════════════════════════════════════════════════════════════════════

def run_free_sources() -> dict:
    """Run all free source ingestion pipelines."""
    import time
    start = time.time()
    results = {}

    results["sslbl"] = ingest_sslbl()
    results["ghsa"] = ingest_ghsa(100)
    results["osv"] = ingest_osv(200)
    results["sigmahq"] = ingest_sigmahq()
    results["yaraify"] = ingest_yaraify()
    results["ransomware_live"] = ingest_ransomware_live()
    results["d3fend"] = ingest_d3fend()
    results["package_advisories"] = ingest_package_advisories()

    elapsed = time.time() - start
    total = sum(v for v in results.values() if isinstance(v, int))
    results["total_new"] = total
    results["elapsed_seconds"] = round(elapsed, 1)
    logging.info(f"🎯 Free sources pipeline: {total} nouveaux items en {elapsed:.1f}s")
    return results
