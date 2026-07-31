"""IOC Enricher — abuse.ch APIs (ThreatFox, URLHaus, MalwareBazaar, FeodoTracker)."""
import json
import logging
import os
import time

import requests

IOC_SOURCES = {
    "threatfox": {"url": "https://threatfox-api.abuse.ch/api/v1/"},
    "urlhaus": {"url": "https://urlhaus-api.abuse.ch/v1/urls/recent/limit/50/"},
    "malwarebazaar": {"url": "https://mb-api.abuse.ch/api/v1/"},
    "feodotracker": {"url": "https://feodotracker.abuse.ch/downloads/ipblocklist.json"},
}


def run_ioc_enrichment() -> dict:
    """Execute l'enrichissement IOC complet. Retourne un resume."""
    from src import database
    results = {}

    # 1. ThreatFox — IOCs recents
    try:
        r = requests.post(
            IOC_SOURCES["threatfox"]["url"],
            json={"query": "get_iocs", "days": 1},
            timeout=20,
        )
        if r.status_code == 200 and r.text.strip():
            data = r.json()
            iocs = data.get("data", [])
            if iocs:
                conn = database.get_db_connection()
                cursor = conn.cursor()
                updated = 0
                for ioc in iocs[:100]:
                    ioc_val = ioc.get("ioc_value", "")
                    ioc_type = ioc.get("ioc_type", "")
                    ioc_id = ioc.get("id", "")
                    malware = ioc.get("malware_printable", "") or ioc.get("malware", "")
                    label = malware or f"{ioc_type}:{ioc_val}"
                    if not ioc_val:
                        continue
                    cursor.execute(
                        """UPDATE cve_entries SET weaknesses = CASE
                           WHEN weaknesses IS NULL THEN %s
                           WHEN position(%s in weaknesses) = 0 THEN weaknesses || '; ' || %s
                           ELSE weaknesses END
                           WHERE description ILIKE %s""",
                        (f"IOC:ThreatFox:{label}",
                         f"IOC:ThreatFox:{label}",
                         f"IOC:ThreatFox:{label}",
                         f"%{malware}%" if malware else "%"),
                    )
                    if cursor.rowcount:
                        updated += 1
                conn.commit()
                cursor.close()
                conn.close()
                results["threatfox"] = updated
                logging.info(f"🦊 ThreatFox: {updated} CVEs enrichies avec IOCs")
    except Exception as e:
        logging.warning(f"ThreatFox: {e}")

    # 2. URLHaus — URLs malveillantes -> keywords
    try:
        r = requests.get(IOC_SOURCES["urlhaus"]["url"], timeout=15)
        if r.status_code == 200 and r.text.strip():
            urls = r.json().get("urls", [])
            if urls:
                keywords = list(dict.fromkeys(
                    u.get("url", "")[:60] for u in urls[:50] if u.get("url")
                ))[:30]
                entries = [{
                    "term": kw, "category_guess": "malicious_url",
                    "score": 0.75, "sources": 1,
                    "source_samples": "URLHaus abuse.ch",
                } for kw in keywords if len(kw) > 3]
                if entries:
                    saved = database.save_discovered_keywords(entries)
                    results["urlhaus"] = saved
                    logging.info(f"🏠 URLHaus: {saved} URLs malveillantes importees")
    except Exception as e:
        logging.warning(f"URLHaus: {e}")

    # 3. MalwareBazaar — hashes malwares -> keywords
    try:
        r = requests.post(
            IOC_SOURCES["malwarebazaar"]["url"],
            json={"query": "get_recent", "selector": "time"},
            timeout=20,
        )
        if r.status_code == 200 and r.text.strip():
            data = r.json()
            if data.get("query_status") == "ok":
                samples = data.get("data", [])
                keywords = list(dict.fromkeys(
                    s.get("sha256_hash", "") for s in samples[:30] if s.get("sha256_hash")
                ))[:20]
                entries = [{
                    "term": f"malware:{kw[:16]}",
                    "category_guess": "malware_hash",
                    "score": 0.80, "sources": 1,
                    "source_samples": "MalwareBazaar abuse.ch",
                } for kw in keywords]
                if entries:
                    saved = database.save_discovered_keywords(entries)
                    results["malwarebazaar"] = saved
                    logging.info(f"💣 MalwareBazaar: {saved} hashes malwares importes")
    except Exception as e:
        logging.warning(f"MalwareBazaar: {e}")

    # 4. Feodo Tracker — IPs C2 -> keywords
    try:
        r = requests.get(IOC_SOURCES["feodotracker"]["url"], timeout=15)
        if r.status_code == 200 and r.text.strip():
            ips = r.json()
            keywords = list(dict.fromkeys(
                f"c2:{entry.get('ip_address','')}"
                for entry in ips[:50] if entry.get("ip_address")
            ))[:20]
            entries = [{
                "term": kw, "category_guess": "botnet_c2",
                "score": 0.80, "sources": 1,
                "source_samples": "FeodoTracker abuse.ch",
            } for kw in keywords]
            if entries:
                saved = database.save_discovered_keywords(entries)
                results["feodo"] = saved
                logging.info(f"🤖 FeodoTracker: {saved} IPs C2 importees")
    except Exception as e:
        logging.warning(f"FeodoTracker: {e}")

    return results
