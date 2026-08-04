"""Ingestion des produits affectés (CPE) depuis NVD 2.0.

Remplit la table `cve_affected_products` (vendor/product/version/cpe_uri) en
rejouant les pages NVD 2.0 déjà couvertes par `cve_importer`. Deux sources par
CVE : le bloc `affected[].affectedData[]` (le plus structuré, récent) et le
bloc `configurations[].nodes[].cpeMatch[]` (historique). La première fait
autorité ; on complète avec la seconde quand elle n'existe pas.

Résultat : le matching assets↔CVE du Risk Engine (mode "product") et la fiche
CVE 360 (correlation) disposent enfin des produits concrets.
"""
import json
import logging
import os
import threading
import time

from src import cve_importer
from src import database
from src.db import products as db_products

STATUS_FILE = os.getenv("DATA_DIR", "data") + "/products_status.json"

_import_lock = threading.Lock()


def _write_status(status):
    try:
        os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f)
    except Exception:
        pass


def get_products_status():
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"running": False, "processed": 0, "page": None, "error": None}


def is_running() -> bool:
    return _import_lock.locked()


def _parse_cpe_uri(criteria: str):
    """Décompose une URI CPE 2.3 → (vendor, product, version, platform).

    cpe:2.3:<part>:<vendor>:<product>:<version>:<update>:<edition>:<language>:<sw>:<hw>:<other>
    """
    parts = (criteria or "").split(":")
    if len(parts) < 5:
        return None, None, None, None
    vendor = parts[3].replace("\\:", ":").replace("_", " ").strip() if len(parts) > 3 else None
    product = parts[4].replace("\\:", ":").replace("_", " ").strip() if len(parts) > 4 else None
    version = None
    update = None
    if len(parts) > 5 and parts[5] not in ("", "*", "-"):
        version = parts[5].replace("_", " ")
    if len(parts) > 6 and parts[6] not in ("", "*", "-"):
        update = parts[6].replace("_", " ")
    if not version and update:
        version = update
    hw = parts[10].replace("_", " ") if len(parts) > 10 and parts[10] not in ("", "*") else None
    sw = parts[9].replace("_", " ") if len(parts) > 9 and parts[9] not in ("", "*") else None
    platform = None
    if hw and sw:
        platform = f"{sw}/{hw}"
    elif hw:
        platform = hw
    elif sw:
        platform = sw
    return vendor or None, product or None, version, platform


def _products_from_item(cve_item):
    """Extrait la liste des produits affectés d'un item NVD 2.0."""
    cve = cve_item.get("cve", {})
    cve_id = cve.get("id")
    if not cve_id:
        return []

    out = []

    # Source 1 (prioritaire) : affected[].affectedData[] — vendor/product structurés
    for aff in cve.get("affected", []) or []:
        for ad in aff.get("affectedData", []) or []:
            vendor = (ad.get("vendor") or "").strip() or None
            product = (ad.get("product") or "").strip() or None
            platforms = ad.get("platforms", []) or []
            platform = ", ".join(p for p in platforms if p) if platforms else None
            versions = ad.get("versions", []) or []
            version = None
            for v in versions:
                status = (v.get("status") or "affected")
                if status in ("affected", "affected; vulnerable"):
                    vv = v.get("version")
                    if vv:
                        version = vv if vv not in ("-", "*") else None
                        break
            if not version and (versions or ad.get("cpes")):
                for v in versions:
                    vv = v.get("version")
                    if vv and vv not in ("-", "*"):
                        version = vv
                        break
            for cpe in ad.get("cpes", []) or []:
                out.append({
                    "cve_id": cve_id,
                    "product": product or _parse_cpe_uri(cpe)[1] or "unknown",
                    "vendor": vendor or _parse_cpe_uri(cpe)[0],
                    "version": version or _parse_cpe_uri(cpe)[2],
                    "platform": platform or _parse_cpe_uri(cpe)[3],
                    "cpe_uri": cpe,
                    "status": "affected",
                })

    # Source 2 (complémentaire) : configurations[].nodes[].cpeMatch[] — historique
    if not out:
        for cfg in cve.get("configurations", []) or []:
            def walk(nodes):
                for node in nodes or []:
                    for m in node.get("cpeMatch", []) or []:
                        if not m.get("vulnerable", True):
                            continue
                        criteria = m.get("criteria", "")
                        vendor, product, version, platform = _parse_cpe_uri(criteria)
                        status = "unknown"
                        if m.get("versionEndExcluding"):
                            status = "affected"
                        out.append({
                            "cve_id": cve_id,
                            "product": product or "unknown",
                            "vendor": vendor,
                            "version": version,
                            "platform": platform,
                            "cpe_uri": criteria or None,
                            "status": status,
                        })
                    walk(node.get("children", []) or [])
            walk(cfg.get("nodes", []) or [])

    return out


def import_products_all(max_pages: int | None = None, start_year: int | None = None,
                        end_year: int | None = None, reverse: bool = True, resume: bool = True):
    """Rejoue les pages NVD et remplit cve_affected_products."""
    if not _import_lock.acquire(blocking=False):
        logging.info("Import produits déjà en cours, ignoré.")
        return {"imported": 0, "error": "already_running"}

    total = 0
    error = None
    page = None
    _write_status({"running": True, "processed": 0, "page": None, "error": None, "mode": "products"})
    try:
        start = start_year if start_year is not None else cve_importer.START_YEAR
        end = end_year if end_year is not None else cve_importer.END_YEAR
        for items, label in cve_importer._iter_nvd_pages(start_year=start, end_year=end,
                                                         max_pages=max_pages, reverse=reverse):
            rows = []
            for it in items:
                rows.extend(_products_from_item(it))
            saved = db_products.save_affected_products(rows)
            total += saved
            page = label
            _write_status({"running": True, "processed": total, "page": label, "error": None, "mode": "products"})
            if total % 20000 < 2000:
                logging.info(f"🧩 Produits CPE: {total} enregistrés (page {label})")
    except Exception as e:
        error = str(e)
        logging.error(f"❌ Erreur import produits: {e}")

    _write_status({"running": False, "processed": total, "page": page, "error": error, "mode": "products"})
    _import_lock.release()
    logging.info(f"✅ Import produits terminé: {total} produits enregistrés")
    return {"imported": total, "error": error}
