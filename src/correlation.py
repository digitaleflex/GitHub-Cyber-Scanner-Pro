"""Moteur de correlation: CVE ↔ Exploit ↔ Outils ↔ IOCs."""
import csv
import logging
import os
import re
from io import StringIO

import requests

EXPLOITDB_URL = "https://gitlab.com/exploit-database/exploitdb/-/raw/main/files_exploits.csv"

# ── Cache des references Exploit-DB ──────────────────────────────────────

_exploitdb_cache = None  # {cve_id: [exploit_row, ...]}


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
    """Retourne les exploits connus pour une CVE (Exploit-DB)."""
    _load_exploitdb_cache()
    return _exploitdb_cache.get(cve_id.upper(), [])


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
    conn.close()

    if not cve:
        return {"error": "CVE introuvable", "cve_id": cve_id}

    cve = dict(cve)
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
