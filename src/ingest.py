"""Pipeline d'ingestion du cycle de vie des menaces (KEV + IOCs + ATT&CK).

Sources:
- CISA KEV  : https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
- URLhaus   : https://urlhaus.abuse.ch/downloads/csv_recent/  (URLs + payloads)
- ThreatFox : https://threatfox.abuse.ch/export/json/recent/  (IOCs malveillants)

Chaque collecteur est isole : un echec reseau ne bloque pas les autres.
"""
import json
import logging
from datetime import datetime

import requests

from src.database import get_db_connection

USER_AGENT = "CyberScannerPro/1.0"
TIMEOUT = 30


def _get(url: str) -> requests.Response | None:
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        if r.status_code == 200:
            return r
        logging.warning(f"ingest: HTTP {r.status_code} pour {url}")
    except Exception as e:
        logging.warning(f"ingest: erreur {url} — {e}")
    return None


# ── CISA KEV ─────────────────────────────────────────────────────────────

def ingest_cisa_kev() -> dict:
    """Upsert cve_kev (champs officiels) + marque CISA_KEV sur cve_entries."""
    r = _get("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")
    if not r:
        return {"kev": {"fetched": 0, "error": "source indisponible"}}

    try:
        data = r.json()
    except Exception as e:
        return {"kev": {"fetched": 0, "error": f"JSON invalide: {e}"}}

    vulns = data.get("vulnerabilities", [])
    conn = get_db_connection()
    cursor = conn.cursor()
    inserted = updated = 0
    for v in vulns:
        cve_id = (v.get("cveID") or "").strip().upper()
        if not cve_id:
            continue
        try:
            cursor.execute(
                """INSERT INTO cve_kev (cve_id, vulnerability_name, cisa_kev_date, due_date,
                                        required_action, ransomware_campaign, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (cve_id) DO UPDATE SET
                     vulnerability_name = EXCLUDED.vulnerability_name,
                     cisa_kev_date = EXCLUDED.cisa_kev_date,
                     due_date = EXCLUDED.due_date,
                     required_action = EXCLUDED.required_action,
                     ransomware_campaign = EXCLUDED.ransomware_campaign,
                     notes = EXCLUDED.notes""",
                (
                    cve_id,
                    v.get("vulnerabilityName") or "",
                    v.get("dateAdded") or None,
                    v.get("dueDate") or None,
                    v.get("requiredAction") or "",
                    v.get("ransomwareUse") or "",
                    v.get("notes") or "",
                ),
            )
            updated += 1
            cursor.execute(
                """UPDATE cve_entries
                   SET weaknesses = CASE
                        WHEN weaknesses ILIKE '%%CISA_KEV%%' THEN weaknesses
                        ELSE COALESCE(weaknesses, '') || ' | CISA_KEV' END
                   WHERE cve_id = %s AND weaknesses NOT ILIKE '%%CISA_KEV%%'""",
                (cve_id,),
            )
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            logging.warning(f"ingest KEV {cve_id}: {e}")
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("KEV: %d CVE upsert, %d marquees", updated, inserted)
    return {"kev": {"fetched": len(vulns), "upserted": updated, "newly_marked": inserted}}


# ── IOCs abuse.ch ────────────────────────────────────────────────────────

def _upsert_ioc(cursor, source: str, value: str, ioc_type: str, threat_type: str | None,
                tags: str | None, raw: dict) -> bool:
    """Insere un IOC unique. Retourne True si nouvellement insere."""
    try:
        cursor.execute(
            """INSERT INTO ioc_feed (source, value, ioc_type, threat_type, tags, first_seen, status, raw_json)
               VALUES (%s, %s, %s, %s, %s, %s, 'active', %s)
               ON CONFLICT (value) DO NOTHING""",
            (source, value, ioc_type, threat_type, tags, datetime.utcnow(), json.dumps(raw)[:2000]),
        )
        return cursor.rowcount > 0
    except Exception as e:
        logging.warning(f"ingest IOC {value}: {e}")
        return False


def _classify_ioc(value: str, ioc_type: str) -> str:
    """Normalise le type d'IOC en categorie canonique."""
    t = (ioc_type or "").lower()
    if "ip" in t:
        return "ipv4" if ":" not in value else "ipv6"
    if "domain" in t or "host" in t:
        return "domain"
    if "url" in t or value.startswith(("http://", "https://")):
        return "url"
    if t in ("md5", "sha1", "sha256", "sha384", "sha512"):
        return t
    if "sha" in t:
        return "sha256"
    if "md" in t:
        return "md5"
    if "email" in t:
        return "email"
    if "." in value and " " not in value and not value.startswith("http"):
        return "domain"
    return t or "unknown"


def ingest_urlhaus() -> dict:
    """IOCs URLs malveillantes + hashes de payloads (CSV recent, vraie colonne URL)."""
    r = _get("https://urlhaus.abuse.ch/downloads/csv_recent/")
    if not r:
        return {"urlhaus": {"fetched": 0, "error": "source indisponible"}}

    import csv as _csv
    from io import StringIO

    conn = get_db_connection()
    cursor = conn.cursor()
    inserted = total = 0
    reader = _csv.reader(StringIO(r.text))
    for parts in reader:
        if not parts or parts[0].startswith("#") or len(parts) < 3:
            continue
        url = (parts[2] or "").strip()
        if not url.startswith(("http://", "https://")):
            continue
        total += 1
        threat = (parts[4] or "malware").strip() if len(parts) > 4 else "malware"
        if _upsert_ioc(cursor, "urlhaus", url, "url", threat, None, {"row": parts[:8]}):
            inserted += 1
        if len(parts) > 5 and parts[5].strip():
            # colonne tags : contient parfois des hashes de payloads
            for tag in parts[5].split(","):
                tag = tag.strip()
                if len(tag) in (32, 40, 64):
                    if _upsert_ioc(cursor, "urlhaus", tag, _classify_ioc(tag, tag), threat, None, {"url": url}):
                        inserted += 1
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("URLhaus: %d lignes, %d IOC nouveaux", total, inserted)
    return {"urlhaus": {"fetched": total, "inserted": inserted}}


def ingest_threatfox() -> dict:
    """IOCs malveillants (IP, domaines, hashes) du feed ThreatFox recent."""
    r = _get("https://threatfox.abuse.ch/export/json/recent/")
    if not r:
        return {"threatfox": {"fetched": 0, "error": "source indisponible"}}

    try:
        payload = r.json()
    except Exception as e:
        return {"threatfox": {"fetched": 0, "error": f"JSON invalide: {e}"}}
    items = payload if isinstance(payload, list) else \
        [item for group in payload.values() if isinstance(group, list) for item in group]
    if not isinstance(items, list):
        return {"threatfox": {"fetched": 0, "error": "format inattendu"}}

    conn = get_db_connection()
    cursor = conn.cursor()
    inserted = 0
    for item in items:
        value = (item.get("ioc_value") or item.get("ioc") or "").strip()
        if not value:
            continue
        ioc_type = _classify_ioc(value, item.get("ioc_type") or "")
        threat = item.get("threat_type") or item.get("malware_printable") or "malware"
        tags = item.get("malware_printable") or None
        if _upsert_ioc(cursor, "threatfox", value, ioc_type, threat, tags, item):
            inserted += 1
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("ThreatFox: %d IOC nouveaux", inserted)
    return {"threatfox": {"fetched": len(items), "inserted": inserted}}


# ── MITRE ATT&CK (donnees locales) ───────────────────────────────────────

_ATTACK_FILES = [
    "mitre_attack_enterprise.json",
    "mitre_attack_ics.json",
    "mitre_attack_mobile.json",
]


def _attack_ext_id(o: dict) -> str | None:
    for ref in o.get("external_references", []) or []:
        if ref.get("source_name") == "mitre-attack" and ref.get("external_id"):
            return ref["external_id"]
    return None


def _attack_url(o: dict) -> str | None:
    for ref in o.get("external_references", []) or []:
        if ref.get("source_name") == "mitre-attack" and ref.get("url"):
            return ref["url"]
    return None


def _safe_date(value) -> str | None:
    """Convertit une date MITRE (parfois '2014-??-??') en DATE SQL safe."""
    if not value:
        return None
    s = str(value).strip().replace("??", "01").replace("--", "-01-")
    if len(s) == 4:
        s = f"{s}-01-01"
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return s
    except Exception:
        return None


def ingest_mitre_attack() -> dict:
    """Importe techniques, acteurs (intrusion-set) et campagnes depuis les bundles locaux."""
    import os
    from src.config import DATA_DIR

    techniques = actors = campaigns = 0
    conn = get_db_connection()
    cursor = conn.cursor()
    for fname in _ATTACK_FILES:
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                bundle = json.load(f)
        except Exception as e:
            logging.warning(f"ATT&CK {fname}: {e}")
            continue

        for o in bundle.get("objects", []):
            otype = o.get("type")
            try:
                if otype == "attack-pattern":
                    t_id = _attack_ext_id(o)
                    if not t_id:
                        continue
                    phases = o.get("kill_chain_phases", []) or []
                    tactic = phases[0].get("phase_name") if phases else None
                    cursor.execute(
                        """INSERT INTO attack_techniques (technique_id, name, tactic, platform, description, url)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           ON CONFLICT (technique_id) DO UPDATE SET
                             name = EXCLUDED.name, tactic = EXCLUDED.tactic,
                             platform = EXCLUDED.platform, description = EXCLUDED.description,
                             url = EXCLUDED.url""",
                        (t_id, (o.get("name") or "")[:300], tactic, (o.get("x_mitre_platforms") or [None])[0],
                         (o.get("description") or "")[:4000], _attack_url(o)),
                    )
                    techniques += 1
                elif otype == "intrusion-set":
                    name = o.get("name") or ""
                    if not name:
                        continue
                    aliases = o.get("aliases") or []
                    cursor.execute(
                        """INSERT INTO apt_groups (name, aliases, description, motivations, countries, first_seen, tools, url)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (name) DO UPDATE SET
                             aliases = EXCLUDED.aliases, description = EXCLUDED.description,
                             motivations = EXCLUDED.motivations, countries = EXCLUDED.countries,
                             first_seen = EXCLUDED.first_seen, tools = EXCLUDED.tools, url = EXCLUDED.url""",
                        (name[:300], ", ".join(aliases)[:500] or None,
                         (o.get("description") or "")[:4000],
                         ", ".join(o.get("x_mitre_motivations", []) or [])[:300] or None,
                         ", ".join(o.get("x_mitre_countries", []) or [])[:300] or None,
                         _safe_date(o.get("first_seen")), (o.get("x_mitre_used_refs") or []),
                         _attack_url(o)),
                    )
                    actors += 1
                elif otype == "campaign":
                    name = o.get("name") or ""
                    if not name:
                        continue
                    cursor.execute(
                        """INSERT INTO campaigns (name, description, status, start_date, end_date)
                           VALUES (%s, %s, 'active', %s, %s)
                           ON CONFLICT DO NOTHING""",
                        (name[:300], (o.get("description") or "")[:4000],
                         _safe_date(o.get("first_seen")), _safe_date(o.get("last_seen"))),
                    )
                    campaigns += 1
            except Exception as e:
                logging.warning(f"ATT&CK import {otype}: {e}")
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("ATT&CK: %d techniques, %d acteurs, %d campagnes", techniques, actors, campaigns)
    return {"mitre": {"techniques": techniques, "actors": actors, "campaigns": campaigns}}


# ── Orchestrateur ────────────────────────────────────────────────────────

def run_ingest(full: bool = False) -> dict:
    """Lance le pipeline complet. `full=True` force les gros volumes."""
    results = {
        "started_at": datetime.utcnow().isoformat(),
        "full": full,
        "steps": {},
    }
    results["steps"]["kev"] = ingest_cisa_kev()["kev"]
    results["steps"]["urlhaus"] = ingest_urlhaus()["urlhaus"]
    results["steps"]["threatfox"] = ingest_threatfox()["threatfox"]
    results["steps"]["mitre"] = ingest_mitre_attack()["mitre"]
    if full:
        try:
            import src.ingest_rules as rules_mod
            results["steps"]["rules"] = rules_mod.run_rules_ingest()
        except Exception as e:
            logging.error(f"ingest rules: {e}")
            results["steps"]["rules"] = {"error": str(e)}
    results["finished_at"] = datetime.utcnow().isoformat()
    return results


def get_ingest_stats() -> dict:
    """Statistiques de volumetrie IOC et sources."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ioc_feed")
    row = cursor.fetchone()
    total = row[0] if row else 0
    cursor.execute(
        """SELECT ioc_type, COUNT(*) AS cnt FROM ioc_feed
           GROUP BY ioc_type ORDER BY cnt DESC"""
    )
    by_type = [{"ioc_type": r[0], "count": r[1]} for r in cursor.fetchall()]
    cursor.execute(
        """SELECT source, COUNT(*) AS cnt FROM ioc_feed
           GROUP BY source ORDER BY cnt DESC"""
    )
    by_source = [{"source": r[0], "count": r[1]} for r in cursor.fetchall()]
    cursor.execute("SELECT MAX(first_seen) FROM ioc_feed")
    row = cursor.fetchone()
    last_seen = row[0] if row else None
    cursor.execute("SELECT COUNT(*) FROM cve_kev")
    row = cursor.fetchone()
    kev_count = row[0] if row else 0
    cursor.close()
    conn.close()
    rules = {}
    try:
        import src.ingest_rules as rules_mod
        rules = rules_mod.get_rules_stats()
    except Exception as e:
        logging.error(f"stats regles: {e}")
    return {
        "total_iocs": total,
        "by_type": by_type,
        "by_source": by_source,
        "last_ingest": str(last_seen) if last_seen else None,
        "kev_count": kev_count,
        "rules": rules,
    }
