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

    return cve
