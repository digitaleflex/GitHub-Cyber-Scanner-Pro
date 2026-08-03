"""STIX 2.1 export for CVEs, IOCs, Threat Actors, and Tools."""
from datetime import datetime
import stix2
from stix2 import Bundle, Indicator, Vulnerability, Relationship, Identity, Malware, Tool, ThreatActor, Report
from src import database
import logging

CYBERSCAN_ID = "identity--cyberscan-pro"
CYBERSCAN_NAME = "CyberScan Pro"
TLP_CLEAR = stix2.TLP_WHITE  # Will use marking-definition for TLP:CLEAR


def _now():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_id(prefix: str, value: str) -> str:
    import hashlib
    h = hashlib.sha256(f"{prefix}:{value}".encode()).hexdigest()[:32]
    return f"{prefix}--{h}"


def export_cves(limit: int = 50, severity: str = "") -> str:
    """Export CVEs as STIX 2.1 Vulnerability objects with Indicators."""
    cves_data = database.search_cves(severity=severity, page=1, per_page=limit)
    cves = cves_data.get("cves", [])

    objects = [
        stix2.Identity(
            id=CYBERSCAN_ID,
            name=CYBERSCAN_NAME,
            identity_class="organization",
            created=_now(),
            modified=_now(),
        )
    ]

    for cve in cves:
        cve_id = cve["cve_id"]
        sev = cve.get("severity", "UNKNOWN")
        cvss = cve.get("cvss_score") or 0
        desc = cve.get("description", "")[:500]
        published = cve.get("published")

        vuln = stix2.Vulnerability(
            id=_make_id("vulnerability", cve_id),
            name=cve_id,
            description=desc,
            created=published or _now(),
            modified=cve.get("last_modified") or _now(),
            external_references=[
                {"source_name": "NVD", "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}"}
            ],
            custom_properties={
                "x_cvss_score": float(cvss) if cvss else None,
                "x_severity": sev,
                "x_weaknesses": cve.get("weaknesses", []),
            },
        )
        objects.append(vuln)

        if float(cvss) >= 7.0:
            indicator = stix2.Indicator(
                id=_make_id("indicator", f"cve-{cve_id}"),
                name=f"CVE-{cve_id} exploitation",
                description=f"Indicator for {cve_id}",
                pattern=f"[vulnerability:name = '{cve_id}']",
                pattern_type="stix",
                valid_from=published or _now(),
                indicator_types=["malicious-activity"],
                created_by_ref=CYBERSCAN_ID,
            )
            rel = stix2.Relationship(
                id=_make_id("relationship", f"indicates-{cve_id}"),
                relationship_type="indicates",
                source_ref=indicator.id,
                target_ref=vuln.id,
                created_by_ref=CYBERSCAN_ID,
            )
            objects.append(indicator)
            objects.append(rel)

    bundle = stix2.Bundle(
        id=_make_id("bundle", f"cves-{datetime.utcnow().isoformat()}"),
        objects=objects,
        created=_now(),
    )
    return bundle.serialize()


def export_tools() -> str:
    """Export tools as STIX 2.1 Tool objects."""
    tools = database.get_repos_frontend(sort_by="stars")

    objects = [
        stix2.Identity(
            id=CYBERSCAN_ID,
            name=CYBERSCAN_NAME,
            identity_class="organization",
            created=_now(),
            modified=_now(),
        )
    ]

    for tool in tools:
        tid = _make_id("tool", tool["name"])
        tool_obj = stix2.Tool(
            id=tid,
            name=tool["name"],
            description=tool.get("desc", "")[:500] if tool.get("desc") else None,
            tool_version="latest",
            created_by_ref=CYBERSCAN_ID,
            external_references=[
                {"source_name": "GitHub", "url": tool.get("url", f"https://github.com/{tool['name']}")}
            ],
            custom_properties={
                "x_stars": tool.get("stars", 0),
                "x_language": tool.get("lang"),
                "x_security_verdict": tool.get("security_verdict"),
                "x_vitality_score": tool.get("vitality_score"),
            },
        )
        objects.append(tool_obj)

    bundle = stix2.Bundle(
        id=_make_id("bundle", f"tools-{datetime.utcnow().isoformat()}"),
        objects=objects,
        created=_now(),
    )
    return bundle.serialize()


def extract_iocs(text: str) -> list[dict]:
    """Extract IOCs (IPs, domains, hashes, URLs) from text using regex."""
    import re
    iocs = []

    ip_pattern = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
    domain_pattern = re.compile(r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b')
    hash_patterns = {
        'md5': re.compile(r'\b[a-fA-F0-9]{32}\b'),
        'sha1': re.compile(r'\b[a-fA-F0-9]{40}\b'),
        'sha256': re.compile(r'\b[a-fA-F0-9]{64}\b'),
    }
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    for ip in set(ip_pattern.findall(text)):
        if not ip.startswith(('0.', '127.', '255.')):
            iocs.append({'type': 'ipv4-addr', 'value': ip})

    for domain in set(domain_pattern.findall(text)):
        if '.' in domain and not domain.endswith(('.py', '.js', '.exe', '.dll', '.com')):
            iocs.append({'type': 'domain-name', 'value': domain.lower()})

    for algo, pattern in hash_patterns.items():
        for h in set(pattern.findall(text)):
            iocs.append({'type': 'file', 'hashes': {algo.upper(): h}, 'value': h})

    for email in set(email_pattern.findall(text)):
        iocs.append({'type': 'email-addr', 'value': email.lower()})

    return iocs


def generate_ioc_feed(limit: int = 100) -> dict:
    """Generate IOC feed from repos + CVEs as STIX 2.1 Bundle."""
    cves_data = database.search_cves(page=1, per_page=limit)
    cves = cves_data.get("cves", [])
    repos = database.get_repos_frontend(sort_by="stars")

    objects = [
        stix2.Identity(
            id=CYBERSCAN_ID,
            name=CYBERSCAN_NAME,
            identity_class="organization",
            created=_now(),
            modified=_now(),
        )
    ]

    all_iocs = []
    for cve in cves:
        text = cve.get("description", "") + " " + str(cve.get("weaknesses", ""))
        iocs = extract_iocs(text)
        for ioc in iocs:
            ioc["source"] = cve["cve_id"]
            ioc["severity"] = cve.get("severity", "UNKNOWN")
            all_iocs.append(ioc)

    for repo in repos:
        text = repo.get("desc", "") or ""
        iocs = extract_iocs(text)
        for ioc in iocs:
            ioc["source"] = repo["name"]
            ioc["severity"] = repo.get("security_verdict", "unknown")
            all_iocs.append(ioc)

    seen = set()
    for ioc in all_iocs[:500]:
        key = f"{ioc['type']}:{ioc['value']}"
        if key in seen:
            continue
        seen.add(key)

        pattern_map = {
            'ipv4-addr': f"[ipv4-addr:value = '{ioc['value']}']",
            'domain-name': f"[domain-name:value = '{ioc['value']}']",
            'file': f"[file:hashes.'{list(ioc.get('hashes', {}).keys())[0] if ioc.get('hashes') else 'SHA-256'}' = '{ioc['value']}']",
            'email-addr': f"[email-addr:value = '{ioc['value']}']",
        }
        pattern = pattern_map.get(ioc['type'], f"[artifact:value = '{ioc['value']}']")

        indicator = stix2.Indicator(
            id=_make_id("indicator", key),
            name=f"{ioc['type']}: {ioc['value']}",
            description=f"Extracted from {ioc['source']}",
            pattern=pattern,
            pattern_type="stix",
            valid_from=_now(),
            indicator_types=["malicious-activity"] if ioc.get("severity") in ("CRITICAL", "HIGH", "Critique") else ["anomalous-activity"],
            created_by_ref=CYBERSCAN_ID,
            custom_properties={
                "x_source": ioc["source"],
                "x_severity": ioc["severity"],
            },
        )
        objects.append(indicator)

    count = len(objects) - 1
    logging.info(f"🎯 IOC Feed: {count} indicators generated")

    bundle = stix2.Bundle(
        id=_make_id("bundle", f"ioc-feed-{datetime.utcnow().date().isoformat()}"),
        objects=objects,
        created=_now(),
    )
    return {"indicators": count, "stix": bundle.serialize()}
