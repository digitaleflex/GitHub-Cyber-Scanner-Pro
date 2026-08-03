"""EPSS (Exploit Prediction Scoring System) — FIRST.org.

Prediction de la probabilite d'exploitation dans les 30 prochains jours.
Complementaire au CVSS: EPSS dit "ca va etre exploite", CVSS dit "c'est grave".
Gratuit, sans cle API, 300 req/min.
"""
import logging
import time
from datetime import datetime

import requests

from src import database

EPSS_API = "https://api.first.org/data/v1/epss"
_last_fetch_ts = [0.0]

BATCH_LOOKUP = False


def _rate_limit():
    elapsed = time.time() - _last_fetch_ts[0]
    if elapsed < 0.3:
        time.sleep(0.3 - elapsed)
    _last_fetch_ts[0] = time.time()


def fetch_epss_batch(cve_ids: list[str]) -> dict[str, dict]:
    """Recupere les scores EPSS pour une liste de CVEs (API batch, limit 100 par appel)."""
    scores = {}
    batch_size = 100
    for i in range(0, len(cve_ids), batch_size):
        chunk = cve_ids[i:i + batch_size]
        _rate_limit()
        try:
            r = requests.post(
                EPSS_API,
                json={"cve": chunk},
                headers={"Accept": "application/json"},
                timeout=30,
            )
            if r.status_code == 200:
                data = r.json()
                for item in data.get("data", []):
                    cid = item.get("cve", "").upper()
                    if cid:
                        scores[cid] = {
                            "epss": float(item.get("epss", 0)),
                            "percentile": float(item.get("percentile", 0)),
                        }
            elif r.status_code == 400 and not BATCH_LOOKUP:
                pass
        except Exception as e:
            logging.warning(f"EPSS batch fetch: {e}")
    return scores


def fetch_epss_single(cve_id: str) -> dict | None:
    """Recupere EPSS pour une seule CVE."""
    _rate_limit()
    try:
        r = requests.get(
            f"{EPSS_API}?cve={cve_id}",
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            items = data.get("data", [])
            if items:
                item = items[0]
                return {
                    "epss": float(item.get("epss", 0)),
                    "percentile": float(item.get("percentile", 0)),
                }
    except Exception as e:
        logging.warning(f"EPSS fetch {cve_id}: {e}")
    return None


def store_epss(scores: dict[str, dict]):
    if not scores:
        return 0
    conn = database.get_db_connection()
    cursor = conn.cursor()
    stored = 0
    for cve_id, s in scores.items():
        try:
            cursor.execute(
                """INSERT INTO epss_scores (cve_id, epss, percentile, updated_at)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (cve_id) DO UPDATE SET
                     epss = EXCLUDED.epss,
                     percentile = EXCLUDED.percentile,
                     updated_at = EXCLUDED.updated_at""",
                (cve_id, s["epss"], s["percentile"], datetime.utcnow()),
            )
            if cursor.rowcount > 0:
                stored += 1
        except Exception as e:
            logging.warning(f"EPSS save {cve_id}: {e}")
    conn.commit()
    cursor.close()
    conn.close()
    return stored


def get_epss_for_cve(cve_id: str) -> dict | None:
    """Score EPSS depuis le cache DB, ou fetch API si absent."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT epss, percentile FROM epss_scores WHERE cve_id = %s", (cve_id.upper(),))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {"epss": row[0], "percentile": row[1]}

    s = fetch_epss_single(cve_id)
    if s:
        if store_epss({cve_id.upper(): s}):
            return s
    return None


def batch_get_epss(cve_ids: list[str]) -> dict[str, dict]:
    """Scores EPSS pour un lot de CVEs: DB cache d'abord, API pour les manquantes."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT cve_id, epss, percentile FROM epss_scores WHERE cve_id = ANY(%s)",
        (cve_ids,),
    )
    result = {}
    missing = []
    for cve_id, epss, pct in cursor.fetchall():
        result[cve_id] = {"epss": epss, "percentile": pct}
        if epss is None:
            missing.append(cve_id)
    cursor.close()
    conn.close()

    if missing:
        fetched = fetch_epss_batch(missing)
        if fetched:
            store_epss(fetched)
            result.update(fetched)
    return result
