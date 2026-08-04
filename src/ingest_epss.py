"""Ingestion massive EPSS (First.org) — 355k scores dans epss_scores.

L'API EPSS v1 retourne tous les scores paginés (epss, percentile, date).
Bulk-insert via execute_values, ~42s pour les 355k CVE (35 pages × 1.2s).
"""
import json
import logging
import os
import threading
import time

import requests
from psycopg2.extras import execute_values

from src import database

EPSS_API = "https://api.first.org/data/v1/epss"
PAGE_SIZE = 10000

_lock = threading.Lock()
_last_ts = [0.0]


def _rate_limit():
    elapsed = time.time() - _last_ts[0]
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    _last_ts[0] = time.time()


def import_epss_all():
    """Charge l'intégralité des scores EPSS dans la table epss_scores."""
    if not _lock.acquire(blocking=False):
        return {"error": "already_running"}

    total = 0
    offset = 0
    total_expected = 0
    error = None
    try:
        # première page pour connaître le total
        _rate_limit()
        r = requests.get(EPSS_API, params={"limit": 1, "offset": 0},
                         headers={"User-Agent": "Mozilla/5.0 CyberScan EPSS"}, timeout=30)
        if r.status_code == 200:
            total_expected = r.json().get("total", 0)
        logging.info("EPSS: %d scores attendus", total_expected)

        while True:
            _rate_limit()
            r = requests.get(EPSS_API, params={"limit": PAGE_SIZE, "offset": offset},
                             headers={"User-Agent": "Mozilla/5.0 CyberScan EPSS"}, timeout=60)
            if r.status_code != 200:
                error = f"HTTP {r.status_code}"
                break
            data = r.json().get("data", [])
            if not data:
                break

            rows = [(
                d["cve"],
                float(d["epss"]),
                float(d["percentile"]),
                d.get("date") or None,
            ) for d in data if d.get("cve")]

            conn = database.get_db_connection()
            cursor = conn.cursor()
            execute_values(
                cursor,
                """INSERT INTO epss_scores (cve_id, epss, percentile, updated_at)
                   VALUES %s
                   ON CONFLICT (cve_id) DO UPDATE SET
                     epss = EXCLUDED.epss,
                     percentile = EXCLUDED.percentile,
                     updated_at = EXCLUDED.updated_at""",
                rows,
                page_size=2000,
            )
            conn.commit()
            cursor.close()
            conn.close()

            total += len(rows)
            offset += PAGE_SIZE
            if total % 100000 < PAGE_SIZE:
                logging.info("📊 EPSS: %d/%d scores injectés", total, total_expected)
    except Exception as e:
        error = str(e)
        logging.error("❌ Erreur EPSS: %s", e)
    finally:
        _lock.release()

    logging.info("✅ EPSS terminé: %d scores", total)
    return {"imported": total, "total_expected": total_expected, "error": error}
