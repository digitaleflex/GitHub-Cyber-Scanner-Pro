"""Massive Data Ingestion Engine — Millions de data points en temps reel.

Sources integrees:
  abuse.ch: URLhaus (3M+), MalwareBazaar (1.5M+), ThreatFox (1M+), FeodoTracker (50K+)
  AlienVault OTX: 20M+ pulses/IOCs
  GreyNoise: billions d'evenements Internet
  urlscan.io: millions de scans publics
  OpenCVE: 200K+ CVEs en temps reel
  FIRST EPSS: scores d'exploitation probabilistes
  Shodan/Censys: billions d'hosts (optionnel, limite API gratuite)
"""

import logging
import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import Optional
from src.database import get_db_connection

# ── Configuration ──────────────────────────────────────────────────────────

ABUSE_CH_URLHAUS = "https://urlhaus-api.abuse.ch/v1/"
ABUSE_CH_MALWAREBAZAAR = "https://mb-api.abuse.ch/api/v1/"
ABUSE_CH_THREATFOX = "https://threatfox-api.abuse.ch/api/v1/"
ABUSE_CH_FEODO = "https://feodotracker.abuse.ch/downloads/malware_hashes.csv"

OTX_PULSES = "https://otx.alienvault.com/api/v1/pulses/subscribed"
GREYNOISE_API = "https://api.greynoise.io/v2/"
URLSCAN_API = "https://urlscan.io/api/v1/"
OPENCVE_API = "https://www.opencve.io/api/"
EPSS_API = "https://api.first.org/data/v1/epss"
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def _save_batch(table: str, rows: list[dict], unique_col: str = "value"):
    """Insert batch with ON CONFLICT DO NOTHING."""
    if not rows:
        return 0
    conn = get_db_connection()
    cur = conn.cursor()
    cols = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(cols))
    col_names = ", ".join(cols)
    sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT ({unique_col}) DO NOTHING"
    saved = 0
    for r in rows:
        try:
            cur.execute(sql, list(r.values()))
            if cur.rowcount > 0:
                saved += 1
        except Exception:
            conn.rollback()
    conn.commit()
    cur.close()
    conn.close()
    return saved


# ── abuse.ch Ecosystem ─────────────────────────────────────────────────────

def ingest_urlhaus(limit: int = 5000) -> int:
    """URLhaus: 3M+ malware URLs. Recupere les URLs recentes + payloads."""
    logging.info("🌐 URLhaus: fetching recent malware URLs...")
    try:
        r = requests.post(ABUSE_CH_URLHAUS + "urls/recent/", json={}, timeout=30)
        data = r.json()
        urls = data.get("urls", [])[:limit]
        rows = []
        for u in urls:
            rows.append({
                "source": "urlhaus",
                "value": u.get("url", ""),
                "ioc_type": "url",
                "threat_type": u.get("threat", ""),
                "tags": ", ".join(u.get("tags", [])),
                "first_seen": u.get("date_added"),
                "status": u.get("url_status", ""),
                "raw_json": json.dumps(u)[:2000],
            })
        saved = _save_batch("ioc_feed", rows, "value")
        logging.info(f"   ✅ URLhaus: {saved} nouvelles URLs")
        return saved
    except Exception as e:
        logging.error(f"   ❌ URLhaus: {e}")
        return 0


def ingest_malwarebazaar(limit: int = 2000) -> int:
    """MalwareBazaar: 1.5M+ malware samples. Recupere les signatures recentes."""
    logging.info("🦠 MalwareBazaar: fetching recent samples...")
    try:
        r = requests.post(ABUSE_CH_MALWAREBAZAAR, data={"query": "get_recent", "selector": "time"}, timeout=30)
        data = r.json()
        samples = data.get("data", [])[:limit]
        rows = []
        for s in samples:
            rows.append({
                "source": "malwarebazaar",
                "value": s.get("sha256_hash", ""),
                "ioc_type": "hash:sha256",
                "threat_type": s.get("signature", ""),
                "tags": ", ".join(s.get("tags", [])),
                "first_seen": s.get("first_seen"),
                "status": "active",
                "raw_json": json.dumps({k: str(v)[:200] for k, v in s.items()})[:2000],
            })
        saved = _save_batch("ioc_feed", rows, "value")
        logging.info(f"   ✅ MalwareBazaar: {saved} nouveaux hashes")
        return saved
    except Exception as e:
        logging.error(f"   ❌ MalwareBazaar: {e}")
        return 0


def ingest_threatfox(limit: int = 5000) -> int:
    """ThreatFox: 1M+ IOCs partages par la communaute."""
    logging.info("🦊 ThreatFox: fetching recent IOCs...")
    try:
        r = requests.post(ABUSE_CH_THREATFOX, json={"query": "recent", "days": 7}, timeout=30)
        data = r.json()
        iocs = []
        for key in data.get("data", {}):
            entry = data["data"][key]
            for ioc_entry in entry:
                iocs.append(ioc_entry)
        rows = []
        for i in iocs[:limit]:
            ioc_value = i.get("ioc_value", "")
            ioc_type = i.get("ioc_type", "").lower()
            rows.append({
                "source": "threatfox",
                "value": ioc_value,
                "ioc_type": ioc_type,
                "threat_type": i.get("threat_type_desc", ""),
                "tags": i.get("malware_printable", ""),
                "first_seen": i.get("first_seen"),
                "status": "active",
                "raw_json": json.dumps(i)[:2000],
            })
        saved = _save_batch("ioc_feed", rows, "value")
        logging.info(f"   ✅ ThreatFox: {saved} nouveaux IOCs")
        return saved
    except Exception as e:
        logging.error(f"   ❌ ThreatFox: {e}")
        return 0


def ingest_feodotracker() -> int:
    """FeodoTracker: C2 servers + malware hashes."""
    logging.info("🕵️ FeodoTracker: fetching C2 IPs...")
    try:
        r = requests.get(ABUSE_CH_FEODO, timeout=30)
        import csv, io
        reader = csv.DictReader(io.StringIO(r.text))
        rows = []
        for row in reader:
            ip = row.get("# C2 IP address", row.get("IP address", ""))
            if not ip or ip.startswith("#"):
                continue
            rows.append({
                "source": "feodotracker",
                "value": ip.strip(),
                "ioc_type": "ipv4",
                "threat_type": row.get("AS name", "C2"),
                "tags": row.get("Malware", ""),
                "first_seen": row.get("Firstseen (UTC)", ""),
                "status": "active",
                "raw_json": json.dumps(row)[:2000],
            })
        saved = _save_batch("ioc_feed", rows, "value")
        logging.info(f"   ✅ FeodoTracker: {saved} C2 IPs")
        return saved
    except Exception as e:
        logging.error(f"   ❌ FeodoTracker: {e}")
        return 0


# ── AlienVault OTX ─────────────────────────────────────────────────────────

def ingest_otx_pulses(limit: int = 500) -> int:
    """AlienVault OTX: 20M+ pulses/IOCs. Recupere les pulses recents."""
    logging.info("🛸 OTX: fetching recent pulses...")
    try:
        r = requests.get(OTX_PULSES, params={"limit": limit}, timeout=30)
        pulses = r.json().get("results", [])[:limit]
        total_iocs = 0
        for pulse in pulses:
            pulse_id = pulse.get("id", "")
            pulse_name = pulse.get("name", "")
            tags = ", ".join(pulse.get("tags", []))
            created = pulse.get("created", "")
            indicators = pulse.get("indicators", [])[:50]
            rows = []
            for ind in indicators:
                rows.append({
                    "source": "otx",
                    "value": ind.get("indicator", ""),
                    "ioc_type": ind.get("type", ""),
                    "threat_type": pulse_name,
                    "tags": tags,
                    "first_seen": created,
                    "status": "active",
                    "raw_json": json.dumps(ind)[:2000],
                })
            total_iocs += _save_batch("ioc_feed", rows, "value")
        logging.info(f"   ✅ OTX: {total_iocs} nouveaux IOCs from {len(pulses)} pulses")
        return total_iocs
    except Exception as e:
        logging.error(f"   ❌ OTX: {e}")
        return 0


# ── OpenCVE ────────────────────────────────────────────────────────────────

def ingest_opencve(limit: int = 1000) -> int:
    """OpenCVE: 200K+ CVEs en temps reel avec vendors/products."""
    logging.info("📚 OpenCVE: fetching recent CVEs...")
    try:
        r = requests.get(OPENCVE_API + "cve", params={"limit": limit}, timeout=30)
        cves = r.json().get("results", [])[:limit]
        rows = []
        for cve in cves:
            rows.append({
                "source": "opencve",
                "value": cve.get("id", ""),
                "ioc_type": "cve",
                "threat_type": cve.get("summary", "")[:200],
                "tags": str(cve.get("cvss", {}).get("v3", "?")),
                "first_seen": cve.get("created_at"),
                "status": "active",
                "raw_json": json.dumps(cve)[:2000],
            })
        saved = _save_batch("ioc_feed", rows, "value")
        logging.info(f"   ✅ OpenCVE: {saved} nouvelles CVEs")
        return saved
    except Exception as e:
        logging.error(f"   ❌ OpenCVE: {e}")
        return 0


# ── FIRST EPSS ─────────────────────────────────────────────────────────────

def ingest_epss() -> int:
    """FIRST EPSS: scores d'exploitation probabilistes pour toutes les CVEs."""
    logging.info("📊 EPSS: fetching exploitation scores...")
    try:
        r = requests.get(EPSS_API, params={"limit": 50000}, timeout=60)
        data = r.json().get("data", [])[:50000]
        conn = get_db_connection()
        cur = conn.cursor()
        saved = 0
        for entry in data:
            cve_id = entry.get("cve", "")
            epss_score = entry.get("epss", "0")
            percentile = entry.get("percentile", "0")
            try:
                cur.execute(
                    "UPDATE cve_entries SET cvss_score = GREATEST(COALESCE(cvss_score, 0), %s) WHERE cve_id = %s",
                    (float(epss_score) * 10, cve_id.upper()),
                )
                saved += cur.rowcount
            except Exception:
                conn.rollback()
        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"   ✅ EPSS: {saved} CVEs updated with exploitation scores")
        return saved
    except Exception as e:
        logging.error(f"   ❌ EPSS: {e}")
        return 0


# ── urlscan.io ─────────────────────────────────────────────────────────────

def ingest_urlscan(limit: int = 500) -> int:
    """urlscan.io: millions de scans publics. Recupere les resultats recents."""
    logging.info("🔍 urlscan.io: fetching recent scans...")
    try:
        r = requests.get(URLSCAN_API + "search/", params={"q": "task.method:automatic", "size": limit}, timeout=30)
        results = r.json().get("results", [])[:limit]
        rows = []
        for scan in results:
            page = scan.get("page", {})
            rows.append({
                "source": "urlscan",
                "value": page.get("url", ""),
                "ioc_type": "url",
                "threat_type": page.get("server", ""),
                "tags": scan.get("task", {}).get("tags", ""),
                "first_seen": scan.get("task", {}).get("time"),
                "status": scan.get("verdicts", {}).get("overall", {}).get("malicious", False) and "malicious" or "clean",
                "raw_json": json.dumps({"url": page.get("url"), "screenshot": page.get("screenshot"), "ip": page.get("ip")})[:2000],
            })
        saved = _save_batch("ioc_feed", rows, "value")
        logging.info(f"   ✅ urlscan.io: {saved} nouveaux scans")
        return saved
    except Exception as e:
        logging.error(f"   ❌ urlscan.io: {e}")
        return 0


# ── GreyNoise ──────────────────────────────────────────────────────────────

def ingest_greynoise(api_key: str = "") -> int:
    """GreyNoise: billions d'evenements. Recupere les IPs malveillantes recentes."""
    if not api_key:
        api_key = os.getenv("GREYNOISE_API_KEY", "")
    if not api_key:
        logging.warning("⚠️ GreyNoise: pas d'API key, skip")
        return 0
    logging.info("🌊 GreyNoise: fetching malicious IPs...")
    try:
        headers = {"key": api_key}
        r = requests.get(GREYNOISE_API + "noise/multi/quick", params={"limit": 1000}, headers=headers, timeout=30)
        ips = r.json().get("data", [])[:1000]
        rows = []
        for ip_data in ips:
            rows.append({
                "source": "greynoise",
                "value": ip_data.get("ip", ""),
                "ioc_type": "ipv4",
                "threat_type": ip_data.get("classification", ""),
                "tags": ip_data.get("name", ""),
                "first_seen": ip_data.get("last_seen"),
                "status": "active",
                "raw_json": json.dumps(ip_data)[:2000],
            })
        saved = _save_batch("ioc_feed", rows, "value")
        logging.info(f"   ✅ GreyNoise: {saved} nouvelles IPs")
        return saved
    except Exception as e:
        logging.error(f"   ❌ GreyNoise: {e}")
        return 0


# ── Pipeline Orchestrator ──────────────────────────────────────────────────

def run_massive_ingestion(full: bool = False) -> dict:
    """Execute le pipeline d'ingestion complet. Retourne les stats."""
    results = {}
    start = time.time()

    # Tier 1: abuse.ch (gratuit, massif)
    results["urlhaus"] = ingest_urlhaus(5000)
    results["malwarebazaar"] = ingest_malwarebazaar(2000)
    results["threatfox"] = ingest_threatfox(5000)
    results["feodotracker"] = ingest_feodotracker()

    # Tier 2: OTX + OpenCVE (gratuit)
    results["otx"] = ingest_otx_pulses(500)
    results["opencve"] = ingest_opencve(1000)

    # Tier 3: EPSS (gratuit, enrichissement)
    results["epss"] = ingest_epss()

    if full:
        # Tier 4: urlscan + greynoise (optionnel)
        results["urlscan"] = ingest_urlscan(500)
        results["greynoise"] = ingest_greynoise()

    elapsed = time.time() - start
    total = sum(v for v in results.values() if isinstance(v, int))
    results["total_new"] = total
    results["elapsed_seconds"] = round(elapsed, 1)

    logging.info(f"🎯 Ingestion massive terminee: {total} nouveaux IOCs en {elapsed:.1f}s")
    return results


def get_ioc_stats() -> dict:
    """Retourne les stats de volumetrie IOC."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM ioc_feed")
    total = cur.fetchone()[0]

    cur.execute("SELECT source, COUNT(*) as cnt FROM ioc_feed GROUP BY source ORDER BY cnt DESC")
    by_source = [{"source": r[0], "count": r[1]} for r in cur.fetchall()]

    cur.execute("SELECT ioc_type, COUNT(*) as cnt FROM ioc_feed GROUP BY ioc_type ORDER BY cnt DESC")
    by_type = [{"type": r[0], "count": r[1]} for r in cur.fetchall()]

    cur.execute("SELECT COUNT(*) FROM ioc_feed WHERE first_seen > NOW() - INTERVAL '24 hours'")
    last_24h = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "total_iocs": total,
        "iocs_24h": last_24h,
        "by_source": by_source,
        "by_type": by_type,
        "sources_available": [
            {"name": "URLhaus", "endpoint": "urlhaus", "type": "malware_urls", "volume": "3M+"},
            {"name": "MalwareBazaar", "endpoint": "malwarebazaar", "type": "malware_hashes", "volume": "1.5M+"},
            {"name": "ThreatFox", "endpoint": "threatfox", "type": "iocs", "volume": "1M+"},
            {"name": "FeodoTracker", "endpoint": "feodotracker", "type": "c2_ips", "volume": "50K+"},
            {"name": "AlienVault OTX", "endpoint": "otx", "type": "pulses", "volume": "20M+"},
            {"name": "OpenCVE", "endpoint": "opencve", "type": "cves", "volume": "200K+"},
            {"name": "FIRST EPSS", "endpoint": "epss", "type": "exploit_scores", "volume": "200K+"},
            {"name": "urlscan.io", "endpoint": "urlscan", "type": "scans", "volume": "10M+"},
            {"name": "GreyNoise", "endpoint": "greynoise", "type": "noise_ips", "volume": "10B+"},
        ],
    }
