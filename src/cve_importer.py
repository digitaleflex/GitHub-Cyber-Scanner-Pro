"""Importeur NVD 2.0 : remplit/rafraichit la table `cve_entries` (description,
sévérité CVSS, références, faiblesses) et backfill des champs manquants.

Pagination robuste : NVD rejette les fenêtres de dates > 120 jours (HTTP 404)
et la pagination profonde par startIndex souffre de drift. On découpe donc le
temps en fenêtres TRIMESTRIELLES puis on pagine à l'intérieur de chaque fenêtre.
"""
import json
import logging
import os
import threading
import time

import requests

from src import database

STATUS_FILE = os.getenv("DATA_DIR", "data") + "/cve_status.json"

# API NVD 2.0 (officielle). Source autoritaire des CVE.
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120 CyberScan"}

RESULTS_PER_PAGE = 2000
START_YEAR = 2002
END_YEAR = 2026

_import_lock = threading.Lock()
_last_request_ts = [0.0]


def _api_key() -> str:
    return os.getenv("NVD_API_KEY", "").strip()


def score_to_severity(score) -> str | None:
    """Convertit un score CVSS en sévérité qualitative (qualitative scoring)."""
    if score is None:
        return None
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    return "LOW"


def _rate_limit():
    """Espace les requêtes selon le quota NVD : 5 req/30s sans clé, 50 req/30s avec."""
    interval = 1.2 if _api_key() else 6.2
    elapsed = time.time() - _last_request_ts[0]
    if elapsed < interval:
        time.sleep(interval - elapsed)
    _last_request_ts[0] = time.time()


def _nvd_get(params: dict, retries: int = 5):
    """Requête NVD avec rate-limit et retry. Retourne le JSON ou None (fenêtre vide/échec)."""
    key = _api_key()
    for attempt in range(retries):
        _rate_limit()
        headers = dict(HEADERS)
        if key:
            headers["apiKey"] = key
        try:
            r = requests.get(NVD_API, headers=headers, params=params, timeout=120)
        except Exception as e:
            logging.error(f"❌ NVD erreur requête: {e}")
            time.sleep(10)
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            # Fenêtre sans résultat — pas une erreur.
            return None
        logging.warning(f"⚠️ NVD HTTP {r.status_code}, retry dans 12s (essai {attempt + 1}/{retries})")
        time.sleep(12)
    return None


def _iter_nvd_pages(start_year: int = START_YEAR, end_year: int = END_YEAR, max_pages: int | None = None, reverse: bool = True):
    """Générateur : fenêtres trimestrielles NVD 2.0.
    Par défaut ordre décroissant (récent → ancien) pour remplir les CVE récentes d'abord."""
    pages = 0
    year_range = range(end_year, start_year - 1, -1) if reverse else range(start_year, end_year + 1)
    for year in year_range:
        for q in range(0, 12, 3):
            m0 = q + 1
            start = f"{year}-{m0:02d}-01T00:00:00.000"
            m1 = q + 3
            end = f"{year + 1}-01-01T00:00:00.000" if m1 >= 12 else f"{year}-{m1 + 1:02d}-01T00:00:00.000"
            label = f"{year}-Q{q // 3 + 1}"
            start_index = 0
            while True:
                if max_pages is not None and pages >= max_pages:
                    return
                data = _nvd_get({
                    "resultsPerPage": RESULTS_PER_PAGE,
                    "startIndex": start_index,
                    "pubStartDate": start,
                    "pubEndDate": end,
                })
                if not data:
                    break
                items = data.get("vulnerabilities", [])
                yield items, f"{label}@{start_index}"
                total = data.get("totalResults", 0)
                start_index += len(items)
                pages += 1
                if not items or start_index >= total:
                    break


def _parse_entry(cve_item):
    """Parse un item du format NVD 2.0 (vulnerabilities[].cve)."""
    cve = cve_item.get("cve", {})
    cve_id = cve.get("id")
    if not cve_id:
        return None

    descriptions = cve.get("descriptions", [])
    description = " ".join(d.get("value", "") for d in descriptions if d.get("lang") == "en")

    published = (cve.get("published") or "")[:10] or None
    last_modified = (cve.get("lastModified") or "")[:10] or None

    severity = None
    cvss_score = None
    metrics = cve.get("metrics", {})
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        mlist = metrics.get(key)
        if mlist:
            m0 = mlist[0]
            # NVD 2.0: V3.x stocke dans "cvss", V2 dans "cvssData".
            cvss = m0.get("cvss") or m0.get("cvssData") or {}
            cvss_score = cvss.get("baseScore")
            severity = cvss.get("baseSeverity") or m0.get("baseSeverity")
            if cvss_score is not None and not severity:
                severity = score_to_severity(cvss_score)
            break

    refs = cve.get("references", [])
    references_urls = ",".join(r.get("url", "") for r in refs[:10])

    weaknesses = cve.get("weaknesses", [])
    weakness_list = []
    for w in weaknesses:
        for d in w.get("description", []):
            val = d.get("value", "")
            if val.startswith("CWE"):
                weakness_list.append(val)
    weaknesses_str = ",".join(weakness_list[:10])

    return {
        "cve_id": cve_id,
        "description": description,
        "published": published,
        "last_modified": last_modified,
        "severity": severity,
        "cvss_score": cvss_score,
        "references_urls": references_urls,
        "weaknesses": weaknesses_str,
    }


def _write_status(status):
    try:
        os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f)
    except Exception:
        pass


def get_cve_status():
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"running": False, "imported": 0, "year": None, "error": None}


def is_running() -> bool:
    return _import_lock.locked()


def get_missing_severity_count() -> int:
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cve_entries WHERE severity IS NULL OR severity = ''")
        row = cursor.fetchone()
        count = row[0] if row else 0
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        logging.error(f"Erreur count missing severity: {e}")
        return -1


def import_cve_all(years=None, max_entries_per_year=None):
    """Importe/rafraichit les CVE depuis NVD 2.0 (fenêtres trimestrielles). ~300k+ CVE."""
    if not _import_lock.acquire(blocking=False):
        logging.info("Import CVE déjà en cours, ignoré.")
        return {"imported": 0, "error": "already_running"}

    total_processed = 0
    error = None
    _write_status({"running": True, "imported": 0, "year": None, "error": None, "mode": "import"})
    try:
        for items, label in _iter_nvd_pages():
            entries = [p for p in (_parse_entry(it) for it in items) if p]
            saved = database.save_cve_entries(entries)
            total_processed += saved
            _write_status({"running": True, "imported": total_processed, "year": label, "error": None, "mode": "import"})
            if total_processed % 40000 < 2000:
                logging.info(f"🛡️ NVD: {total_processed} CVE traitées (page {label})")
    except Exception as e:
        error = str(e)
        logging.error(f"❌ Erreur import CVE: {e}")

    _write_status({"running": False, "imported": total_processed, "year": None, "error": error, "mode": "import"})
    _import_lock.release()
    logging.info(f"✅ Import CVE terminé: {total_processed} CVE traitées")
    return {"imported": total_processed, "error": error}


def backfill_cve_severity(max_pages: int | None = None):
    """Remplit severity/cvss_score manquants en rejouant NVD avec upsert (COALESCE)."""
    before = get_missing_severity_count()
    if before <= 0:
        return {"status": "ok", "processed": 0, "before": before, "after": 0, "message": "Aucune CVE sans sévérité."}

    if not _import_lock.acquire(blocking=False):
        return {"status": "busy", "message": "Un import NVD est déjà en cours."}

    processed = 0
    error = None
    _write_status({"running": True, "imported": 0, "year": None, "error": None, "mode": "backfill", "pending": before})
    try:
        for items, label in _iter_nvd_pages(max_pages=max_pages):
            entries = [p for p in (_parse_entry(it) for it in items) if p]
            processed += database.save_cve_entries(entries)
            _write_status({"running": True, "imported": processed, "year": label, "error": None,
                           "mode": "backfill", "pending": before})
            if processed % 40000 < 2000:
                logging.info(f"🎯 Backfill sévérité: {processed} CVE traitées (page {label})")
    except Exception as e:
        error = str(e)
        logging.error(f"❌ Erreur backfill sévérité: {e}")

    after = get_missing_severity_count()
    _write_status({"running": False, "imported": processed, "year": None, "error": error,
                   "mode": "backfill", "before": before, "after": after})
    _import_lock.release()
    logging.info(f"✅ Backfill sévérité terminé: {processed} CVE, restantes: {after}")
    return {"status": "ok", "processed": processed, "before": before, "after": after, "error": error}
