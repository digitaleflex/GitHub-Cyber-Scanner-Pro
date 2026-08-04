"""Export STIX 2.1 — generation de bundles interoperables (OC TAXII).

Convertit les donnees du cycle de vie (CVE, IOCs, ATT&CK, campagnes, regles)
en objets STIX 2.1 pour l'echange avec des plateformes tierces (MISP, OpenCTI, SOC).
"""
import json
import logging
import uuid
from datetime import datetime, timezone

from src.database import get_db_connection
from psycopg2.extras import RealDictCursor

STIX_NS = uuid.UUID("97f9b6a8-3c4e-4b1a-9d6e-8f0a2c4e6b8d")

IDENTITY = {
    "type": "identity",
    "id": "identity--" + str(uuid.uuid5(STIX_NS, "cyber-scanner-pro")),
    "name": "Cyber Scanner Pro",
    "identity_class": "organization",
    "created": "2024-01-01T00:00:00.000Z",
    "modified": "2024-01-01T00:00:00.000Z",
}


def _ts(day) -> str | None:
    if not day:
        return None
    s = str(day)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).isoformat() + "Z"
    except Exception:
        return s + "T00:00:00.000Z"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stix_id(stype: str, key: str) -> str:
    return f"{stype}--{uuid.uuid5(STIX_NS, key)}"


def build_bundle(objects: list[dict]) -> dict:
    """Enveloppe une liste d'objets STIX dans un bundle 2.1."""
    return {
        "type": "bundle",
        "id": _stix_id("bundle", f"bundle-{datetime.now(timezone.utc).timestamp()}"),
        "spec_version": "2.1",
        "objects": [IDENTITY] + objects,
    }


def _cve_to_vulnerability(row: dict) -> dict:
    cve_id = row["cve_id"]
    description = row.get("description") or "Vulnerabilite de securite."
    external = {
        "source_name": "cve",
        "external_id": cve_id,
    }
    if row.get("cvss_score") is not None:
        external["description"] = f"CVSS: {row['cvss_score']} ({row.get('severity') or 'N/A'})"
    return {
        "type": "vulnerability",
        "id": _stix_id("vulnerability", cve_id),
        "created": _ts(row.get("published")) or _now(),
        "modified": _ts(row.get("last_modified")) or _now(),
        "name": cve_id,
        "description": description[:2000],
        "external_references": [external],
    }


def _cve_to_attack_pattern(cve_id: str, technique: dict) -> dict:
    return {
        "type": "attack-pattern",
        "id": _stix_id("attack-pattern", f"{cve_id}:{technique['technique_id']}"),
        "created": _now(),
        "modified": _now(),
        "name": f"{technique.get('name', technique['technique_id'])} ({technique['technique_id']})",
        "description": technique.get("description") or "",
        "kill_chain_phases": [{"kill_chain_name": "mitre-attack", "phase_name": (technique.get("tactic") or "unknown").lower()}],
        "external_references": [{"source_name": "mitre-attack", "external_id": technique["technique_id"]}],
    }


def _cve_to_indicator(cve_id: str, ioc: dict) -> dict | None:
    pattern_map = {
        "ipv4": "ipv4-addr",
        "ipv6": "ipv6-addr",
        "domain": "domain-name",
        "url": "url",
        "md5": "file:hashes.'MD5'",
        "sha1": "file:hashes.'SHA-1'",
        "sha256": "file:hashes.'SHA-256'",
    }
    stix_type = pattern_map.get((ioc.get("ioc_type") or "").lower())
    if not stix_type:
        return None
    value = ioc.get("value", "")
    if "file:hashes" in stix_type:
        pattern = f"[{stix_type} = '{value}']"
    else:
        pattern = f"[{stix_type} = '{value}']"
    return {
        "type": "indicator",
        "id": _stix_id("indicator", f"{cve_id}:{value}"),
        "created": _ts(ioc.get("first_seen")) or _now(),
        "modified": _now(),
        "name": f"IOC {ioc.get('ioc_type')} lie a {cve_id}",
        "pattern": pattern,
        "valid_from": _ts(ioc.get("first_seen")) or _now(),
        "labels": [ioc.get("threat_type") or "unknown"],
        "source": ioc.get("source") or "ingest",
    }


def get_cve_bundle(cve_id: str) -> dict | None:
    """Bundle STIX 2.1 complet pour une CVE (vuln + IOCs + ATT&CK + campagne)."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT cve_id, description, severity, cvss_score, published, last_modified
           FROM cve_entries WHERE cve_id = %s""",
        (cve_id.upper(),),
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return None

    objects = [_cve_to_vulnerability(dict(row))]

    cursor.execute(
        """SELECT i.id, i.value, i.ioc_type, i.threat_type, i.source, i.first_seen
           FROM ioc_feed i
           JOIN cve_iocs ci ON ci.ioc_id = i.id
           WHERE ci.cve_id = %s""",
        (cve_id.upper(),),
    )
    for ioc in cursor.fetchall():
        ind = _cve_to_indicator(cve_id, dict(ioc))
        if ind:
            objects.append(ind)

    cursor.execute(
        """SELECT at.technique_id, at.name, at.tactic, at.description
           FROM attack_techniques at
           JOIN cve_attack_mapping cam ON cam.technique_id = at.technique_id
           WHERE cam.cve_id = %s""",
        (cve_id.upper(),),
    )
    for tech in cursor.fetchall():
        objects.append(_cve_to_attack_pattern(cve_id, dict(tech)))

    cursor.execute(
        """SELECT c.id, c.name, c.status, a.name AS actor
           FROM campaigns c
           JOIN cve_campaign_mapping ccm ON ccm.campaign_id = c.id
           LEFT JOIN apt_groups a ON a.id = c.threat_actor_id
           WHERE ccm.cve_id = %s""",
        (cve_id.upper(),),
    )
    for camp in cursor.fetchall():
        objects.append({
            "type": "campaign",
            "id": _stix_id("campaign", f"campaign-{camp['id']}"),
            "created": _now(),
            "modified": _now(),
            "name": camp.get("name") or f"Campagne {camp['id']}",
            "description": f"Actor: {camp.get('actor') or 'inconnu'} — statut {camp.get('status') or 'active'}",
            "aliases": [camp.get("name") or ""] if camp.get("name") else [],
        })

    bundle = build_bundle(objects)
    cursor.close()
    conn.close()

    _log_export(cve_id.upper(), bundle)
    return bundle


def get_cves_bundle(limit: int = 50, what: str = "cves") -> dict:
    """Bundle STIX 2.1 des CVEs les plus critiques/recents (KEV d'abord)."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    order = "weaknesses ILIKE '%CISA_KEV%'" if what == "kev" else "severity IN ('CRITICAL','HIGH')"
    cursor.execute(
        f"""SELECT cve_id, description, severity, cvss_score, published, last_modified
            FROM cve_entries
            WHERE {order}
            ORDER BY published DESC NULLS LAST
            LIMIT %s""",
        (limit,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    objects = [_cve_to_vulnerability(dict(r)) for r in rows]
    bundle = build_bundle(objects)
    _log_export("batch:" + what, bundle, batch_size=len(objects))
    return bundle


def _log_export(ref: str, bundle: dict, batch_size: int = 1):
    """Historise l'export dans stix_export_logs (idempotent par objet)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for obj in bundle.get("objects", []):
            if obj.get("type") == "identity":
                continue
            cursor.execute(
                """INSERT INTO stix_export_logs (stix_id, stix_type, object_ref, export_format, raw_json)
                   VALUES (%s, %s, %s, 'json', %s)
                   ON CONFLICT (stix_id) DO NOTHING""",
                (obj["id"], obj["type"], ref, json.dumps(obj)[:4000]),
            )
        conn.commit()
        cursor.close()
        conn.close()
        logging.info("STIX: %d objet(s) exporte(s) pour %s", batch_size, ref)
    except Exception as e:
        logging.error(f"STIX log export: {e}")
