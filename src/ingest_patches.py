"""Ingestion des correctifs et advisories depuis les references taggees NVD.

Parcourt les pages NVD 2.0 (reutilise la pagination trimestrielle) et extrait :
  - cve_patches : references taggees "Patch" ou "Mitigation"
  - vendor_advisories : references taggees "Vendor Advisory"

Bulk-insert via execute_values comme pour l'EPSS et les produits.
"""
import json
import logging
import os
import re
import threading
import time
from urllib.parse import urlparse

from psycopg2.extras import execute_values

from src import cve_importer
from src import database

STATUS_FILE = os.getenv("DATA_DIR", "data") + "/patches_status.json"

_lock = threading.Lock()


def _write_status(status):
    try:
        os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f)
    except Exception:
        pass


def _extract_patches_advisories(cve_item):
    """Extrait patches et advisories depuis les refs taggees d'une CVE."""
    cve = cve_item.get("cve", {})
    cve_id = cve.get("id")
    if not cve_id:
        return [], []

    source_id = cve.get("sourceIdentifier", "")
    references = cve.get("references", []) or []

    patches = []
    advisories = []

    for ref in references:
        tags = [t.lower() for t in (ref.get("tags", []) or [])]
        url = (ref.get("url") or "").strip()
        if not url:
            continue
        source_name = ref.get("source", source_id) or ""
        domain = urlparse(url).netloc or source_name

        # Patch / Mitigation
        if any(t in tags for t in ("patch", "mitigation", "release notes", "remediation")):
            patch_name = _patch_name_from_url(url, domain)
            vendor = _vendor_from_domain(domain) or _vendor_from_source(source_id)
            patches.append({
                "cve_id": cve_id,
                "patch_name": patch_name[:300],
                "vendor": vendor[:200] if vendor else None,
                "url": url[:500],
                "available": True,
            })

        # Vendor Advisory
        if "vendor advisory" in tags:
            advisory_id = _advisory_id_from_url(url)
            title = _advisory_title(ref, cve_id)
            advisories.append({
                "cve_id": cve_id,
                "vendor": _vendor_from_domain(domain) or _vendor_from_source(source_id) or "unknown",
                "advisory_id": advisory_id[:200] if advisory_id else None,
                "title": title[:300],
                "url": url[:500],
            })

    return patches, advisories


def _patch_name_from_url(url, domain):
    """Extrait un nom lisible depuis l'URL du correctif."""
    path = urlparse(url).path.strip("/")
    segments = [s for s in path.split("/") if s and len(s) > 2 and not s.isdigit()]
    if segments:
        name = segments[-1].replace("-", " ").replace("_", " ")
        if len(name) > 3:
            return name[:300]
    return f"Sécurité {domain}"[:300]


def _advisory_id_from_url(url):
    """Tente d'extraire un ID d'advisory (ex: CVE-2021-34527, MS16-xxx)."""
    path = urlparse(url).path.strip("/")
    m = re.search(r"(CVE-\d{4}-\d{4,})|(MS\d{2}-\d{3})|(ADV\d+)", path, re.I)
    if m:
        return m.group(0).upper()
    return path.split("/")[-1][:200] if path else None


def _advisory_title(ref, cve_id):
    """Titre pour l'advisory (depuis tags ou URL)."""
    tags = ref.get("tags", []) or []
    if "Vendor Advisory" in tags:
        return f"Advisory {cve_id}"
    return f"Ref {cve_id}"


def _vendor_from_domain(domain):
    """Extrait le nom du vendor depuis le domaine (ex: microsoft.com → Microsoft)."""
    if not domain:
        return None
    domain = domain.lower().replace("www.", "")
    name = domain.split(".")[0]
    if len(name) < 3:
        return domain
    return name.capitalize()


def _vendor_from_source(source_id):
    """Extrait le vendor depuis le sourceIdentifier (ex: cve@mitre.org → Mitre)."""
    if not source_id:
        return None
    parts = source_id.split("@")
    if len(parts) >= 2:
        name = parts[1].split(".")[0]
        return name.capitalize() if len(name) > 2 else None
    return None


def import_patches_all(max_pages: int | None = None):
    """Rejoue NVD et remplit cve_patches + vendor_advisories."""
    if not _lock.acquire(blocking=False):
        return {"error": "already_running"}

    total_p = total_a = 0
    error = None
    _write_status({"running": True, "patches": 0, "advisories": 0, "page": None, "error": None})
    try:
        for items, label in cve_importer._iter_nvd_pages(max_pages=max_pages):
            batch_p, batch_a = [], []
            for it in items:
                p, a = _extract_patches_advisories(it)
                batch_p.extend(p)
                batch_a.extend(a)

            saved_p = _bulk_save_patches(batch_p) if batch_p else 0
            saved_a = _bulk_save_advisories(batch_a) if batch_a else 0
            total_p += saved_p
            total_a += saved_a

            _write_status({"running": True, "patches": total_p, "advisories": total_a,
                           "page": label, "error": None})
            if (total_p + total_a) % 10000 < 2000:
                logging.info("🔧 Patches/Advisories: %d patches, %d advisories (page %s)",
                             total_p, total_a, label)
    except Exception as e:
        error = str(e)
        logging.error("❌ Erreur import patches: %s", e)
    finally:
        _lock.release()

    _write_status({"running": False, "patches": total_p, "advisories": total_a,
                   "page": None, "error": error})
    logging.info("✅ Patches/Advisories terminé: %d patches, %d advisories", total_p, total_a)
    return {"patches": total_p, "advisories": total_a, "error": error}


def _bulk_save_patches(patches):
    if not patches:
        return 0
    seen = set()
    rows = []
    for p in patches:
        key = (p["cve_id"], (p.get("url") or ""))
        if key in seen:
            continue
        seen.add(key)
        rows.append((
            p["cve_id"],
            p.get("patch_name"),
            p.get("vendor"),
            p.get("url"),
            p.get("available", True),
        ))
    conn = database.get_db_connection()
    cur = conn.cursor()
    n = 0
    try:
        execute_values(
            cur,
            """INSERT INTO cve_patches (cve_id, patch_name, vendor, url, available)
               VALUES %s ON CONFLICT DO NOTHING""",
            rows, page_size=2000,
        )
        n = len(rows)
    except Exception as e:
        logging.error("Erreur batch save patches: %s", e)
    conn.commit()
    cur.close()
    conn.close()
    return n


def _bulk_save_advisories(advisories):
    if not advisories:
        return 0
    seen = set()
    rows = []
    for a in advisories:
        key = (a["cve_id"], (a.get("url") or ""))
        if key in seen:
            continue
        seen.add(key)
        rows.append((
            a["cve_id"],
            a.get("vendor"),
            a.get("advisory_id"),
            a.get("title"),
            a.get("url"),
        ))
    conn = database.get_db_connection()
    cur = conn.cursor()
    n = 0
    try:
        execute_values(
            cur,
            """INSERT INTO vendor_advisories (cve_id, vendor, advisory_id, title, url)
               VALUES %s ON CONFLICT DO NOTHING""",
            rows, page_size=2000,
        )
        n = len(rows)
    except Exception as e:
        logging.error("Erreur batch save advisories: %s", e)
    conn.commit()
    cur.close()
    conn.close()
    return n
