import json
import logging
import os
import time

import requests

from src import database

STATUS_FILE = os.getenv("DATA_DIR", "data") + "/cve_status.json"

# Feeds NVD par année (format 1.1, JSON zippé). On couvre 2002 -> 2025.
NVD_BASE = "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-{year}.json.gz"

YEARS = list(range(2002, 2026))


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


def _parse_entry(cve_item):
    cve = cve_item.get("cve", {})
    cve_id = cve.get("CVE_data_meta", {}).get("ID")
    if not cve_id:
        return None

    descriptions = cve.get("description", {}).get("description_data", [])
    description = " ".join(d.get("value", "") for d in descriptions if d.get("lang") == "en")

    published = cve_item.get("publishedDate", "")[:10] or None
    last_modified = cve_item.get("lastModifiedDate", "")[:10] or None

    severity = None
    cvss_score = None
    impacts = cve_item.get("impact", {})
    base_metric = impacts.get("baseMetricV3") or impacts.get("baseMetricV2")
    if base_metric:
        cvss = base_metric.get("cvssV3") or base_metric.get("cvssV2")
        if cvss:
            cvss_score = cvss.get("baseScore")
            severity = cvss.get("baseSeverity")

    refs = cve.get("references", {}).get("reference_data", [])
    references_urls = ",".join(r.get("url", "") for r in refs[:10])

    weaknesses = cve.get("problemtype", {}).get("problemtype_data", [])
    weakness_list = []
    for w in weaknesses:
        for d in w.get("description", []):
            if d.get("value", "").startswith("CWE"):
                weakness_list.append(d["value"])
    weaknesses_str = ",".join(weakness_list)

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


def import_cve_all(years=None, max_entries_per_year=None):
    """Télécharge et importe les feeds NVD par année. ~300k+ CVE au total."""
    years = years or YEARS
    total_imported = 0
    error = None
    _write_status({"running": True, "imported": 0, "year": None, "error": None})

    try:
        for year in years:
            _write_status({"running": True, "imported": total_imported, "year": year, "error": None})
            url = NVD_BASE.format(year=year)
            logging.info(f"🛡️ Téléchargement NVD {year}...")
            try:
                r = requests.get(url, timeout=120)
                if r.status_code != 200:
                    logging.warning(f"⚠️ NVD {year} status {r.status_code}")
                    continue
            except Exception as e:
                logging.error(f"❌ Erreur téléchargement NVD {year}: {e}")
                continue

            try:
                data = r.json()
            except Exception:
                # parfois le gzip n'est pas auto-décompressé
                import gzip
                import io
                try:
                    data = json.loads(gzip.decompress(r.content))
                except Exception as e2:
                    logging.error(f"❌ Erreur parse NVD {year}: {e2}")
                    continue

            items = data.get("CVE_Items", [])
            entries = []
            for it in items:
                parsed = _parse_entry(it)
                if parsed:
                    entries.append(parsed)
                if max_entries_per_year and len(entries) >= max_entries_per_year:
                    break

            saved = database.save_cve_entries(entries)
            total_imported += saved
            logging.info(f"🛡️ NVD {year}: {saved} nouvelles CVE (cumul {total_imported})")
            _write_status({"running": True, "imported": total_imported, "year": year, "error": None})
            time.sleep(1)
    except Exception as e:
        error = str(e)
        logging.error(f"❌ Erreur import CVE: {e}")

    _write_status({"running": False, "imported": total_imported, "year": None, "error": error})
    logging.info(f"✅ Import CVE terminé: {total_imported} CVE importées")
    return {"imported": total_imported, "error": error}
