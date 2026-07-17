import logging
import re

import requests

logger = logging.getLogger(__name__)

CISA_FEED = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
CERT_FR_API = "https://www.cert.ssi.gouv.fr/api/2023-12-01/incident.json"
MITRE_CVE = "https://cveawg.mitre.org/api/cve?limit=50"

TIMEOUT = 15


def fetch_cisa_kev() -> list[str]:
    try:
        resp = requests.get(CISA_FEED, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        vulnerabilities = data.get("vulnerabilities", [])
        keywords: list[str] = []
        for vuln in vulnerabilities:
            desc = (vuln.get("shortDescription") or "")[:200]
            vendor = vuln.get("vendorProject", "")
            product = vuln.get("product", "")
            parts = [vendor, product, desc]
            for part in parts:
                tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", part)
                keywords.extend(t.lower() for t in tokens if len(t) > 3)
        logger.info("ThreatIntel: %d mots-cles depuis CISA KEV", len(keywords))
        return keywords[:200]
    except Exception as e:
        logger.debug("ThreatIntel CISA: %s", e)
        return []


def fetch_cert_fr() -> list[str]:
    try:
        resp = requests.get(CERT_FR_API, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        keywords: list[str] = []
        for incident in data if isinstance(data, list) else data.get("incidents", []):
            title = incident.get("title", "") or incident.get("description", "") or ""
            tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", title)
            keywords.extend(t.lower() for t in tokens if len(t) > 3)
        logger.info("ThreatIntel: %d mots-cles depuis CERT-FR", len(keywords))
        return keywords[:100]
    except Exception as e:
        logger.debug("ThreatIntel CERT-FR: %s", e)
        return []


def fetch_mitre_cve() -> list[str]:
    try:
        resp = requests.get(MITRE_CVE, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        keywords: list[str] = []
        for vuln in data.get("vulnerabilities", []):
            cve_id = (vuln.get("id") or "")
            desc = ""
            containers = vuln.get("containers", {}) or {}
            cna = containers.get("cna", {}) or {}
            if cna:
                desc = (cna.get("descriptions") or [{}])[0].get("value", "") if cna.get("descriptions") else ""
            parts = [cve_id, desc]
            for part in parts:
                tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", str(part))
                keywords.extend(t.lower() for t in tokens if len(t) > 3)
        logger.info("ThreatIntel: %d mots-cles depuis MITRE CVE", len(keywords))
        return keywords[:100]
    except Exception as e:
        logger.debug("ThreatIntel MITRE: %s", e)
        return []


def aggregate_threat_keywords() -> list[str]:
    seen = set()
    all_kw: list[str] = []
    for source_func in [fetch_cisa_kev, fetch_cert_fr, fetch_mitre_cve]:
        try:
            for kw in source_func():
                kw_clean = kw.strip().lower().replace("_", "-").replace(" ", "-")
                if kw_clean not in seen and len(kw_clean) > 3:
                    seen.add(kw_clean)
                    all_kw.append(kw_clean)
        except Exception as e:
            logger.debug("ThreatIntel source error: %s", e)

    logger.info("ThreatIntel: %d mots-cles uniques agreges", len(all_kw))
    return all_kw


THREAT_TEMPLATES = [
    '"{}" exploit github',
    '"{}" cve github',
    '"{}" poc github',
    '"{}" vulnerability github',
]
