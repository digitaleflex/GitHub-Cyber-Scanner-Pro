"""Ingestion des regles de detection (Sigma, YARA, IDS Snort/Suricata).

Sources:
- Sigma : https://github.com/SigmaHQ/sigma            (regles YAML, rules/)
- YARA  : https://github.com/Neo23x0/signature-base  (regles .yar, yara/)
- IDS   : https://www.snort.org/downloads/community  (community-rules.tar.gz)

Chaque collecteur est isole : un echec reseau ne bloque pas les autres.
Les CVE references dans les regles sont extraites et stockees (lien cve_id).
"""
import io
import logging
import os
import re
import tarfile
import tempfile

import requests
import yaml

from src.database import get_db_connection

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) CyberScannerPro/1.0"
TIMEOUT = 60
_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)

SIGMA_URL = "https://codeload.github.com/SigmaHQ/sigma/tar.gz/refs/heads/master"
YARA_URL = "https://codeload.github.com/Neo23x0/signature-base/tar.gz/refs/heads/master"
IDS_URL = "https://www.snort.org/downloads/community/community-rules.tar.gz"


def _first_cve(*texts) -> str | None:
    for t in texts:
        if not t:
            continue
        m = _CVE_RE.search(str(t))
        if m:
            return m.group(0).upper()
    return None


def _download_tarball(url: str) -> str | None:
    """Telecharge un .tar.gz et retourne le chemin du fichier temporaire."""
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, stream=True)
        if r.status_code != 200:
            logging.warning(f"ingest_rules: HTTP {r.status_code} pour {url}")
            return None
        fd, path = tempfile.mkstemp(suffix=".tar.gz")
        with os.fdopen(fd, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        r.close()
        return path
    except Exception as e:
        logging.warning(f"ingest_rules: telechargement {url} impossible — {e}")
        return None


def _extract(tarball_path: str, want_subdir: str, suffix: str):
    """Extrait les fichiers `suffix` du sous-dossier `want_subdir`. Generateur (name, bytes)."""
    try:
        with tarfile.open(tarball_path, "r:gz") as tf:
            for member in tf.getmembers():
                if not member.isfile():
                    continue
                if want_subdir not in member.name:
                    continue
                if not member.name.endswith(suffix):
                    continue
                f = tf.extractfile(member)
                if f is None:
                    continue
                data = f.read()
                f.close()
                yield member.name, data
    except Exception as e:
        logging.error(f"ingest_rules: extraction impossible — {e}")
    finally:
        try:
            os.unlink(tarball_path)
        except OSError:
            pass


# ── Sigma ────────────────────────────────────────────────────────────────

def ingest_sigma() -> dict:
    """Importe les regles SigmaHQ (rules/**.yml) dans sigma_rules."""
    path = _download_tarball(SIGMA_URL)
    if not path:
        return {"sigma": {"fetched": 0, "error": "source indisponible"}}

    conn = get_db_connection()
    cursor = conn.cursor()
    parsed = inserted = linked = 0
    for name, data in _extract(path, "/rules/", ".yml"):
        try:
            rule = yaml.safe_load(data)
        except Exception:
            continue
        if not isinstance(rule, dict) or not rule.get("title"):
            continue
        parsed += 1
        rule_id = str(rule.get("id") or "").strip() or None
        title = str(rule.get("title") or "")[:2000]
        references = rule.get("references") or []
        cve_id = _first_cve(*references)
        if cve_id:
            linked += 1
        try:
            detection_txt = yaml.safe_dump(rule.get("detection") or {}, sort_keys=False) or ""
        except Exception:
            detection_txt = ""
        logsource = rule.get("logsource") or {}
        logsource_txt = yaml.safe_dump(logsource, sort_keys=False) if isinstance(logsource, dict) else str(logsource)
        cursor.execute(
            """INSERT INTO sigma_rules (rule_id, title, description, level, status, tags,
                                        logsource, detection, source, file_url, cve_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (rule_id) DO UPDATE SET
                 title = EXCLUDED.title, description = EXCLUDED.description,
                 level = EXCLUDED.level, status = EXCLUDED.status,
                 tags = EXCLUDED.tags, logsource = EXCLUDED.logsource,
                 detection = EXCLUDED.detection, file_url = EXCLUDED.file_url,
                 cve_id = COALESCE(EXCLUDED.cve_id, sigma_rules.cve_id)""",
            (rule_id, title,
             str(rule.get("description") or "")[:4000],
             str(rule.get("level") or "")[:20],
             str(rule.get("status") or "")[:30],
             ", ".join(rule.get("tags") or [])[:1000] or None,
             logsource_txt[:2000] or None,
             detection_txt[:20000],
             "SigmaHQ/sigma",
             f"https://github.com/SigmaHQ/sigma/blob/master/{name.split('/', 1)[-1]}",
             cve_id),
        )
        inserted += cursor.rowcount if rule_id else 0
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Sigma: %d fichiers YAML, %d regles, %d liees a des CVE", parsed, inserted, linked)
    return {"sigma": {"fetched": parsed, "inserted": inserted, "cve_linked": linked}}


# ── YARA ─────────────────────────────────────────────────────────────────

_YARA_RULE_SPLIT = re.compile(r"^\s*rule\s+\w+\s*[:{]", re.MULTILINE)


def ingest_yara() -> dict:
    """Importe les regles YARA (signature-base/yara/**yar) dans yara_rules."""
    path = _download_tarball(YARA_URL)
    if not path:
        return {"yara": {"fetched": 0, "error": "source indisponible"}}

    conn = get_db_connection()
    cursor = conn.cursor()
    files = inserted = linked = 0
    for name, data in _extract(path, "/yara/", ".yar"):
        files += 1
        text = data.decode("utf-8", errors="replace")
        starts = [m.start() for m in _YARA_RULE_SPLIT.finditer(text)]
        boundaries = starts + [len(text)]
        for i in range(len(starts)):
            block = text[starts[i]:boundaries[i + 1]].strip()
            m = re.match(r"rule\s+(\w+)", block)
            if not m:
                continue
            rule_name = m.group(1)[:200]
            meta = " ".join(re.findall(r'"(CVE-\d{4}-\d{4,7})"', block, re.IGNORECASE))
            cve_id = _first_cve(meta, block[:400])
            if cve_id:
                linked += 1
            cursor.execute(
                """INSERT INTO yara_rules (rule_name, title, author, description, tags,
                                           rule_text, source, file_url, cve_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (rule_name) DO UPDATE SET
                     title = EXCLUDED.title, author = EXCLUDED.author,
                     description = EXCLUDED.description, tags = EXCLUDED.tags,
                     rule_text = EXCLUDED.rule_text, file_url = EXCLUDED.file_url,
                     cve_id = COALESCE(EXCLUDED.cve_id, yara_rules.cve_id)""",
                (rule_name, f"YARA {rule_name}", None,
                 "Regle YARA extraite de signature-base", None,
                 block[:20000],
                 "Neo23x0/signature-base",
                 f"https://github.com/Neo23x0/signature-base/blob/master/{name.split('/', 1)[-1]}",
                 cve_id),
            )
            inserted += 1
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("YARA: %d fichiers, %d regles, %d liees a des CVE", files, inserted, linked)
    return {"yara": {"fetched": files, "inserted": inserted, "cve_linked": linked}}


# ── IDS (Snort / Suricata) ───────────────────────────────────────────────

_IDS_RULE = re.compile(
    r'^(?P<action>\w+)\s+(?P<proto>\S+)\s+(?P<src>\S+)\s+(?P<srcport>\S+)\s+->\s+'
    r'(?P<dst>\S+)\s+(?P<dstport>\S+)\s*\((?P<opts>.*)\)\s*$',
    re.DOTALL,
)


def _parse_ids_line(line: str) -> dict | None:
    """Parse une ligne de regle Snort/Suricata et extrait msg/sid/rev/severity/references."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    m = _IDS_RULE.match(line)
    if not m:
        return None
    opts = m.group("opts")
    msg = re.search(r'msg\s*:\s*"((?:[^"\\]|\\.)*)"', opts)
    sid = re.search(r"\bsid\s*:\s*(\d+)", opts)
    rev = re.search(r"\brev\s*:\s*(\d+)", opts)
    classtype = re.search(r"\bclasstype\s*:\s*(\w+)", opts)
    refs = re.findall(r"reference\s*:\s*([^,;]+)", opts)
    cve = None
    for r in refs:
        cve = _first_cve(r)
        if cve:
            break
    severity = 3
    if classtype and classtype.group(1) in ("attempted-admin", "successful-admin", "attempted-user",
                                            "successful-user", "trojan-activity", "web-application-attack",
                                            "shellcode-detect", "misc-attack"):
        severity = 1
    elif classtype and classtype.group(1) in ("policy-violation", "misc-activity", "string-detect"):
        severity = 3
    return {
        "sid": int(sid.group(1)) if sid else None,
        "rev": int(rev.group(1)) if rev else None,
        "message": (msg.group(1) if msg else "")[:2000],
        "classtype": classtype.group(1) if classtype else None,
        "severity": severity,
        "reference": "; ".join(refs)[:2000] or None,
        "rule_text": line,
        "cve_id": cve,
    }


def ingest_ids() -> dict:
    """Importe les regles Snort community (community-rules/*.rules) dans ids_rules."""
    path = _download_tarball(IDS_URL)
    if not path:
        return {"ids": {"fetched": 0, "error": "source indisponible"}}

    conn = get_db_connection()
    cursor = conn.cursor()
    files = inserted = linked = 0
    for name, data in _extract(path, "rules/", ".rules"):
        files += 1
        for line in data.decode("utf-8", errors="replace").splitlines():
            rule = _parse_ids_line(line)
            if not rule:
                continue
            if rule["cve_id"]:
                linked += 1
            cursor.execute(
                """INSERT INTO ids_rules (engine, sid, gid, rev, message, severity, priority,
                                          reference, rule_text, source, file_url, cve_id)
                   VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT DO NOTHING""",
                ("snort", rule["sid"], rule["rev"],
                 rule["message"], rule["severity"], rule["severity"],
                 rule["reference"], rule["rule_text"], "Snort Community",
                 f"https://www.snort.org/downloads/community/{name.split('/')[-1]}",
                 rule["cve_id"]),
            )
            inserted += cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("IDS: %d fichiers, %d regles, %d liees a des CVE", files, inserted, linked)
    return {"ids": {"fetched": files, "inserted": inserted, "cve_linked": linked}}


# ── Orchestrateur + stats ────────────────────────────────────────────────

def run_rules_ingest() -> dict:
    """Lance l'ingestion des trois familles de regles de detection."""
    return {
        "sigma": ingest_sigma()["sigma"],
        "yara": ingest_yara()["yara"],
        "ids": ingest_ids()["ids"],
    }


def get_rules_stats() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()

    def _count(sql: str) -> int:
        cursor.execute(sql)
        row = cursor.fetchone()
        return row[0] if row else 0

    sigma = _count("SELECT COUNT(*) FROM sigma_rules")
    sigma_cve = _count("SELECT COUNT(*) FROM sigma_rules WHERE cve_id IS NOT NULL")
    yara = _count("SELECT COUNT(*) FROM yara_rules")
    yara_cve = _count("SELECT COUNT(*) FROM yara_rules WHERE cve_id IS NOT NULL")
    ids = _count("SELECT COUNT(*) FROM ids_rules")
    ids_cve = _count("SELECT COUNT(*) FROM ids_rules WHERE cve_id IS NOT NULL")
    cursor.close()
    conn.close()
    return {
        "sigma": {"total": sigma, "cve_linked": sigma_cve},
        "yara": {"total": yara, "cve_linked": yara_cve},
        "ids": {"total": ids, "cve_linked": ids_cve},
    }
