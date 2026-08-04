"""Moteur de correlation: CVE ↔ Exploit ↔ Outils ↔ IOCs."""
import csv
import logging
import os
import re
from io import StringIO

import requests

EXPLOITDB_URL = "https://gitlab.com/exploit-database/exploitdb/-/raw/main/files_exploits.csv"

# ── Cache des references Exploit-DB ──────────────────────────────────────

_exploitdb_cache: dict | None = None  # {cve_id: [exploit_row, ...]}


def _load_exploitdb_cache():
    """Charge le CSV Exploit-DB en memoire (cache paresseux)."""
    global _exploitdb_cache
    if _exploitdb_cache is not None:
        return

    _exploitdb_cache = {}
    cache_path = os.path.join(os.path.dirname(__file__), "..", "data", "exploitdb.csv")
    try:
        if os.path.exists(cache_path):
            with open(cache_path, encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    desc = (row.get("description") or "") + " " + (row.get("codes") or "")
                    cve_ids = re.findall(r"CVE-\d{4}-\d{4,7}", desc, re.IGNORECASE)
                    for cve in set(cve_ids):
                        cve = cve.upper()
                        _exploitdb_cache.setdefault(cve, []).append({
                            "id": row.get("id", ""),
                            "file": row.get("file", ""),
                            "description": row.get("description", "")[:200],
                            "platform": row.get("platform", ""),
                            "author": row.get("author", ""),
                            "date": row.get("date", ""),
                            "type": row.get("type", ""),
                            "port": row.get("port", ""),
                        })
        logging.info(f"Exploit-DB cache: {len(_exploitdb_cache)} CVEs liees a des exploits")
    except Exception as e:
        logging.error(f"Erreur chargement Exploit-DB cache: {e}")


def get_exploits_for_cve(cve_id: str) -> list[dict]:
    """Retourne les exploits connus pour une CVE (cache CSV + liens en DB)."""
    cve_id = cve_id.upper()
    _load_exploitdb_cache()
    cache = _exploitdb_cache or {}
    exploits = list(cache.get(cve_id, []))
    try:
        import src.db.connection as _conn
        conn = _conn.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT exploit_id, description, platform, exploit_type, author, date, file_url "
            "FROM exploits WHERE cve_id = %s",
            (cve_id,),
        )
        seen = {e["id"] for e in exploits}
        for r in cursor.fetchall():
            eid = str(r[0])
            if eid in seen:
                continue
            exploits.append({
                "id": eid,
                "file": "",
                "description": (r[1] or "")[:200],
                "platform": r[2] or "",
                "author": r[4] or "",
                "date": r[5] or "",
                "type": r[3] or "",
                "port": "",
            })
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"Erreur get_exploits_for_cve (DB): {e}")
    return exploits


def get_tools_for_cve(cve_id: str, limit: int = 10) -> list[dict]:
    """Retourne les outils de la base lies a une CVE (description + semantique)."""
    import src.embeddings as emb
    from src.database import get_db_connection
    from psycopg2.extras import RealDictCursor

    tools = []
    cve_id_upper = cve_id.upper()

    # 1. Recherche textuelle: description contient le CVE-ID
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT full_name AS name, description AS desc, stars, language AS lang,
                  html_url AS url, security_verdict, vitality_score
           FROM repositories
           WHERE description ILIKE %s
           ORDER BY stars DESC LIMIT %s""",
        (f"%{cve_id_upper}%", limit),
    )
    for r in cursor.fetchall():
        tools.append({**dict(r), "match_type": "mention_explicite"})

    # 2. Recherche semantique via la description CVE
    cursor.execute("SELECT description FROM cve_entries WHERE cve_id = %s", (cve_id_upper,))
    cve_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if cve_row and cve_row["description"]:
        try:
            semantic = emb.semantic_search(cve_row["description"], limit=limit, min_score=0.1)
            for s in semantic:
                if s.get("name") not in {t["name"] for t in tools}:
                    tools.append({**s, "match_type": "semantique"})
        except Exception:
            pass

    return tools[:limit]


def _get_cve_lifecycle(conn, cve_id: str) -> dict:
    """Donnees du cycle de vie (IOCs, regles, ATT&CK, CAPEC, campagnes, produits, patches, KEV)."""
    from psycopg2.extras import RealDictCursor
    cve_id = cve_id.upper()
    out = {
        "epss": None,
        "kev": None,
        "iocs": [],
        "sigma_rules": [],
        "yara_rules": [],
        "ids_rules": [],
        "attack_techniques": [],
        "capec": [],
        "campaigns": [],
        "apt_groups": [],
        "affected_products": [],
        "patches": [],
        "advisories": [],
        "analysis": None,
    }
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT epss, percentile, updated_at FROM epss_scores WHERE cve_id = %s", (cve_id,))
        row = cursor.fetchone()
        if row:
            out["epss"] = {"epss": row["epss"], "percentile": row["percentile"], "updated_at": str(row["updated_at"]) if row["updated_at"] else None}

        cursor.execute(
            """SELECT vulnerability_name, cisa_kev_date, due_date, required_action,
                      ransomware_campaign, notes
               FROM cve_kev WHERE cve_id = %s""",
            (cve_id,),
        )
        row = cursor.fetchone()
        if row:
            out["kev"] = {
                "vulnerability_name": row["vulnerability_name"],
                "cisa_kev_date": str(row["cisa_kev_date"]) if row["cisa_kev_date"] else None,
                "due_date": str(row["due_date"]) if row["due_date"] else None,
                "required_action": row["required_action"],
                "ransomware_campaign": row["ransomware_campaign"],
                "notes": row["notes"],
            }

        cursor.execute(
            """SELECT i.id, i.value, i.ioc_type, i.threat_type, i.source, i.first_seen,
                      ci.confidence
               FROM ioc_feed i
               JOIN cve_iocs ci ON ci.ioc_id = i.id
               WHERE ci.cve_id = %s ORDER BY i.id DESC LIMIT 50""",
            (cve_id,),
        )
        for r in cursor.fetchall():
            out["iocs"].append({
                "id": r["id"], "value": r["value"], "ioc_type": r["ioc_type"],
                "threat_type": r["threat_type"], "source": r["source"],
                "first_seen": str(r["first_seen"]) if r["first_seen"] else None,
                "confidence": r["confidence"],
            })

        for table in ("sigma_rules", "yara_rules", "ids_rules"):
            cols = "id, title, description, source, cve_id, created_at" if table == "sigma_rules" else \
                   ("id, rule_name, title, description, source, file_url, created_at" if table == "yara_rules" else
                    "id, engine, sid, message, severity, reference, source, created_at")
            cursor.execute(f"SELECT {cols} FROM {table} WHERE cve_id = %s ORDER BY id DESC LIMIT 20", (cve_id,))
            for r in cursor.fetchall():
                out[table].append(dict(r))

        cursor.execute(
            """SELECT at.technique_id, at.name, at.tactic, at.platform, at.description, at.url,
                      cam.confidence
               FROM attack_techniques at
               JOIN cve_attack_mapping cam ON cam.technique_id = at.technique_id
               WHERE cam.cve_id = %s ORDER BY at.technique_id""",
            (cve_id,),
        )
        for r in cursor.fetchall():
            out["attack_techniques"].append(dict(r))

        cursor.execute(
            """SELECT cp.capec_id, cp.name, cp.description, cp.likelihood, cp.severity
               FROM capec_patterns cp
               JOIN cve_capec_mapping ccm ON ccm.capec_id = cp.capec_id
               WHERE ccm.cve_id = %s ORDER BY cp.capec_id""",
            (cve_id,),
        )
        for r in cursor.fetchall():
            out["capec"].append(dict(r))

        cursor.execute(
            """SELECT c.id, c.name, c.status, c.target_sectors, c.start_date, c.end_date,
                      a.id AS actor_id, a.name AS actor_name
               FROM campaigns c
               JOIN cve_campaign_mapping ccm ON ccm.campaign_id = c.id
               LEFT JOIN apt_groups a ON a.id = c.threat_actor_id
               WHERE ccm.cve_id = %s ORDER BY c.id DESC""",
            (cve_id,),
        )
        campaigns = cursor.fetchall()
        out["campaigns"] = [dict(r) for r in campaigns]
        out["apt_groups"] = []
        seen_actors = set()
        for r in campaigns:
            if r["actor_id"] and r["actor_id"] not in seen_actors:
                seen_actors.add(r["actor_id"])
                out["apt_groups"].append({"id": r["actor_id"], "name": r["actor_name"]})

        cursor.execute(
            """SELECT id, product, vendor, version, platform, cpe_uri, status
               FROM cve_affected_products WHERE cve_id = %s ORDER BY vendor, product""",
            (cve_id,),
        )
        for r in cursor.fetchall():
            out["affected_products"].append(dict(r))

        cursor.execute(
            """SELECT id, patch_name, vendor, url, version_fixed, released, available, verified, notes
               FROM cve_patches WHERE cve_id = %s ORDER BY id DESC""",
            (cve_id,),
        )
        for r in cursor.fetchall():
            out["patches"].append(dict(r))

        cursor.execute(
            """SELECT id, vendor, advisory_id, title, url, severity, published
               FROM vendor_advisories WHERE cve_id = %s ORDER BY published DESC NULLS LAST""",
            (cve_id,),
        )
        for r in cursor.fetchall():
            out["advisories"].append(dict(r))

        # Analyse IA (daemon) - table dediee cve_analysis
        cursor.execute(
            """SELECT summary, impact, recommendation, patched_in,
                      exploitation_likelihood, audience, model, created_at
               FROM cve_analysis WHERE cve_id = %s""",
            (cve_id,),
        )
        ar = cursor.fetchone()
        if ar:
            out["analysis"] = {
                "summary": ar["summary"],
                "impact": ar["impact"],
                "recommendation": ar["recommendation"],
                "patched_in": ar["patched_in"],
                "exploitation_likelihood": ar["exploitation_likelihood"],
                "audience": ar["audience"],
                "model": ar["model"],
                "created_at": str(ar["created_at"]) if ar["created_at"] else None,
            }

        cursor.close()
    except Exception as e:
        logging.error(f"Erreur lifecycle CVE {cve_id}: {e}")
    return out


def get_cve_detail(cve_id: str) -> dict:
    """Retourne le detail complet d'une CVE avec correlations."""
    from src.database import get_db_connection
    from psycopg2.extras import RealDictCursor

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT cve_id, description, severity, cvss_score, published, last_modified,
                  weaknesses
           FROM cve_entries WHERE cve_id = %s""",
        (cve_id.upper(),),
    )
    cve = cursor.fetchone()
    cursor.close()

    if not cve:
        conn.close()
        return {"error": "CVE introuvable", "cve_id": cve_id}

    cve = dict(cve)
    lifecycle = _get_cve_lifecycle(conn, cve_id)
    conn.close()

    cve.update(lifecycle)
    cve["exploits"] = get_exploits_for_cve(cve_id)
    cve["tools"] = get_tools_for_cve(cve_id)
    cve["is_kev"] = bool(cve.get("weaknesses") and "CISA_KEV" in str(cve.get("weaknesses", "")))
    cve["threat_priority"] = compute_threat_priority(cve)

    return cve


def compute_threat_priority(cve: dict) -> dict:
    """Calcule un Threat Priority Score (0-100) multi-facteurs."""
    cvss = cve.get("cvss_score") or 0
    is_kev = cve.get("is_kev", False)
    exploits = cve.get("exploits", [])
    published = cve.get("published")

    score = 0
    factors = {}

    # CVSS (0-40 points)
    cvss_points = min(cvss * 4, 40)
    score += cvss_points
    factors["cvss"] = round(cvss_points, 1)

    # CISA KEV: activement exploite (+30)
    if is_kev:
        score += 30
        factors["kev"] = 30

    # Exploit disponible (+25)
    if exploits:
        exploit_points = min(len(exploits) * 5, 25)
        score += exploit_points
        factors["exploit"] = exploit_points

    # Age: si > 2 ans, penalite (-10); si > 5 ans, pas d'alerte
    if published:
        from datetime import datetime, timezone
        try:
            age_days = (datetime.now(timezone.utc) - published).days if hasattr(published, 'days') else \
                       (datetime.now(timezone.utc) - datetime.fromisoformat(str(published).replace("Z", "+00:00"))).days
            if age_days > 365 * 5:
                factors["age_penalty"] = -20
                score += factors["age_penalty"]
            elif age_days > 365 * 2:
                factors["age_penalty"] = -10
                score += factors["age_penalty"]
        except Exception:
            pass

    score = max(0, min(100, round(score)))
    return {"score": score, "factors": factors, "label": "CRITIQUE" if score >= 75 else "ELEVE" if score >= 50 else "MOYEN" if score >= 25 else "BAS"}


def get_top_threats(limit: int = 20) -> list[dict]:
    """Retourne les CVE les plus menacees selon le Threat Priority Score."""
    from src.database import get_db_connection
    from psycopg2.extras import RealDictCursor

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT cve_id, description, severity, cvss_score, published, weaknesses
        FROM cve_entries
        WHERE (weaknesses ILIKE '%%CISA_KEV%%' OR severity = 'CRITICAL' OR cvss_score >= 9)
        ORDER BY
            CASE WHEN weaknesses ILIKE '%%CISA_KEV%%' THEN 0 ELSE 1 END,
            cvss_score DESC NULLS LAST,
            published DESC NULLS LAST
        LIMIT %s
    """, (limit,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    threats = []
    for r in rows:
        cve = dict(r)
        cve["is_kev"] = bool(cve.get("weaknesses") and "CISA_KEV" in str(cve.get("weaknesses", "")))
        cve["exploits"] = get_exploits_for_cve(cve["cve_id"])
        cve["priority"] = compute_threat_priority(cve)
        threats.append(cve)

    threats.sort(key=lambda t: t["priority"]["score"], reverse=True)
    return threats[:limit]
