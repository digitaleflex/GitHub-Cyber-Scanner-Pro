import json
import logging
import os
import time

import requests

from src import database

STATUS_FILE = os.getenv("DATA_DIR", "data") + "/cve_status.json"

# API NVD 2.0 (officielle, pagination par startIndex). Source autoritaire des CVE.
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"

HEADERS = {"User-Agent": "CyberScan/1.0 (github-cyber-scanner)"}

RESULTS_PER_PAGE = 2000
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
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        mlist = metrics.get(key)
        if mlist:
            cvss = mlist[0].get("cvss", {})
            cvss_score = cvss.get("baseScore")
            severity = cvss.get("baseSeverity")
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


def import_cve_all(years=None, max_entries_per_year=None):
    """Télécharge et importe les feeds CVE (mirror CIRCL) par année. ~300k+ CVE au total."""
    years = years or YEARS
    total_imported = 0
    error = None
    _write_status({"running": True, "imported": 0, "year": None, "error": None})

    try:
        # Récupérer le total estimé via une 1ère requête
        r0 = requests.get(NVD_API, headers=HEADERS, params={"resultsPerPage": 1}, timeout=60)
        if r0.status_code != 200:
            error = f"NVD 2.0 status {r0.status_code}"
            logging.error(f"❌ {error}")
        else:
            total_nvd = r0.json().get("totalResults", 0)
            logging.info(f"🛡️ NVD 2.0: {total_nvd} CVE au total")
            per_page = RESULTS_PER_PAGE
            limit = max_entries_per_year if max_entries_per_year and max_entries_per_year > 0 else total_nvd
            start_index = 0
            while start_index < limit:
                _write_status({"running": True, "imported": total_imported,
                               "year": f"{start_index}/{limit}", "error": None})
                try:
                    r = requests.get(NVD_API, headers=HEADERS,
                                     params={"resultsPerPage": per_page, "startIndex": start_index},
                                     timeout=120)
                    if r.status_code != 200:
                        logging.warning(f"⚠️ NVD status {r.status_code}, pause 10s")
                        time.sleep(10)
                        continue
                except Exception as e:
                    logging.error(f"❌ Erreur NVD req: {e}")
                    time.sleep(10)
                    continue

                try:
                    data = r.json()
                except Exception as e:
                    logging.error(f"❌ Erreur parse NVD: {e}")
                    time.sleep(5)
                    continue

                items = data.get("vulnerabilities", [])
                if not items:
                    break
                entries = []
                for it in items:
                    parsed = _parse_entry(it)
                    if parsed:
                        entries.append(parsed)
                saved = database.save_cve_entries(entries)
                total_imported += saved
                logging.info(f"🛡️ NVD: +{saved} (cumul {total_imported}, idx {start_index})")
                start_index += per_page
                time.sleep(0.3)
    except Exception as e:
        error = str(e)
        logging.error(f"❌ Erreur import CVE: {e}")

    _write_status({"running": False, "imported": total_imported, "year": None, "error": error})
    logging.info(f"✅ Import CVE terminé: {total_imported} CVE importées")
    return {"imported": total_imported, "error": error}
