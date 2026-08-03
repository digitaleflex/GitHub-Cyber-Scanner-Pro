"""Decision Engine v1 : transforme les CVE brutes en decisions priorisees et justifiees.

Chaque decision repond a la question : "Que dois-je faire aujourd'hui ?" en combinant
severite (CVSS), exploitabilite (Exploit-DB), exploitation active (CISA KEV),
pertinence pour la stack de l'utilisateur et recence. La sortie est justifiee :
score, raison lisible, "si vous ignorez", niveau de confiance et sources.
"""
import csv
import logging
import os
import re
from datetime import date, datetime, timedelta, timezone

from src import database
from src import correlation

_KEV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cisa_kev.csv")
_kev_cache = None

SEVERITY_BASE = {"CRITICAL": 10.0, "HIGH": 7.5, "MEDIUM": 5.0, "LOW": 2.5}

_STOP_WORDS = {
    "github", "gitlab", "the", "and", "for", "with", "from", "tool", "tools",
    "security", "cli", "test", "testing", "lib", "library", "scripts", "pro",
    "scanner", "scanners", "a", "an", "of", "in", "on", "to", "cyber", "hack",
    "repository", "src", "new", "com", "org", "net", "not", "all", "any", "can",
    "could", "may", "use", "file", "files", "data", "code", "arbitrary", "remote",
    "local", "attack", "cause", "allow", "via", "execute", "version", "versions",
    "this", "is", "be", "has", "have", "other", "information", "system", "user",
    "users", "web", "server", "service", "services", "http", "https",
}


def _load_kev() -> dict:
    """Charge le catalogue CISA KEV (cache) : {cveID: {product, vendor, dueDate, ...}}."""
    global _kev_cache
    if _kev_cache is not None:
        return _kev_cache
    _kev_cache = {}
    try:
        with open(_KEV_PATH, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                cid = (row.get("cveID") or "").strip().upper()
                if not cid:
                    continue
                _kev_cache[cid] = {
                    "product": (row.get("product") or "").strip(),
                    "vendor": (row.get("vendorProject") or "").strip(),
                    "vulnerabilityName": (row.get("vulnerabilityName") or "").strip(),
                    "dateAdded": (row.get("dateAdded") or "").strip(),
                    "dueDate": (row.get("dueDate") or "").strip(),
                    "ransomware": (row.get("knownRansomwareCampaignUse") or "").strip(),
                    "requiredAction": (row.get("requiredAction") or "").strip()[:300],
                }
    except Exception as e:
        logging.error(f"DecisionEngine: chargement KEV impossible: {e}")
    return _kev_cache


def _iter_tokens(value: str):
    for tok in re.split(r"[/\-_.\s]+", value or ""):
        tok = tok.strip().lower()
        if tok and tok not in _STOP_WORDS:
            yield tok


def build_stack_keywords(limit_repos: int | None = None, max_freq: int = 200) -> set:
    """Termes representatifs de la stack utilisateur, filtres par rarete."""
    kws: dict[str, int] = {}
    conn = database.get_db_connection()
    cursor = conn.cursor()
    sql = (
        "SELECT full_name, language, ai_category, semantic_category "
        "FROM repositories WHERE full_name IS NOT NULL"
    )
    if limit_repos:
        sql += " LIMIT %s"
        cursor.execute(sql, (limit_repos,))
    else:
        cursor.execute(sql)
    for full_name, lang, ai, sem in cursor.fetchall():
        for tok in _iter_tokens(full_name):
            kws[tok] = kws.get(tok, 0) + 1
        if lang and lang != "Non specifiee":
            kws[lang.lower()] = kws.get(lang.lower(), 0) + 1
        if ai:
            for tok in _iter_tokens(ai):
                kws[tok] = kws.get(tok, 0) + 1
        if sem:
            for tok in _iter_tokens(sem):
                kws[tok] = kws.get(tok, 0) + 1
    cursor.close()
    conn.close()
    return {k for k, v in kws.items() if v <= max_freq}


def _risk_if_ignored(cvss, exploits, kev_row, level):
    if kev_row:
        due = kev_row.get("dueDate") or ""
        base = "Exploitation active documentee (CISA KEV)"
        if due:
            return f"{base} → compromission probable; patcher avant l'echeance CISA {due}."
        return f"{base} → compromission probable; patcher en priorite absolue."
    if exploits:
        return "Exploit public disponible → risque d'utilisation dans des campagnes; patcher rapidement."
    if cvss and cvss >= 9:
        return "Score critique sans exploit public connu — surveiller de pres et prevoir un correctif."
    if level in ("CRITIQUE", "ELEVE"):
        return "Vulnerabilite a haute priorite; a integrer dans le cycle de patching."
    return "Priorite a surveiller."


def _confidence(factors: dict) -> str:
    n = len(factors)
    if n >= 3:
        return "Elevee"
    if n == 2:
        return "Moyenne"
    return "Basse"


def score_cve(cve: dict, stack_keywords: set, exploits: list, kev_row: dict | None) -> dict:
    """Calcule le score de decision (0-100) pour une CVE avec justification."""
    cvss = cve.get("cvss_score") or 0
    severity = (cve.get("severity") or "").upper()
    published = cve.get("published")
    desc = (cve.get("description") or "").lower()
    desc_tokens = cve.get("_tokens", set())

    score = 0.0
    factors = {}
    reasons = []
    sources = []

    if cvss:
        pts = min(cvss * 4, 40)
        score += pts
        factors["cvss"] = round(pts, 1)
        sources.append("NVD")
        if cvss >= 9:
            reasons.append(f"Score CVSS {cvss} (severite maximale)")
    elif severity in SEVERITY_BASE:
        pts = SEVERITY_BASE[severity] * 4
        score += pts
        factors["severity"] = round(pts, 1)
        sources.append("NVD")

    if exploits:
        pts = min(len(exploits) * 6, 25)
        score += pts
        factors["exploit"] = round(pts, 1)
        sources.append("Exploit-DB")
        dates = [e.get("date") for e in exploits if e.get("date")]
        hint = f" (le plus recent: {max(dates)})" if dates else ""
        reasons.append(f"{len(exploits)} exploit(s) public(s) disponible(s){hint}")

    if kev_row:
        score += 20
        factors["kev"] = 20
        sources.append("CISA KEV")
        rw = " — liee a des campagnes ransomware" if kev_row.get("ransomware") == "Known" else ""
        reasons.append(f"Exploitee activement dans la nature (CISA KEV){rw}")

    if stack_keywords and desc_tokens:
        kev_text = " ".join(kev_row.get(k, "") for k in ("product", "vendor") if kev_row and kev_row.get(k)).lower()
        kev_tokens = set(re.findall(r"[a-z0-9]{3,}", kev_text)) if kev_text else set()
        hits = sorted(desc_tokens & stack_keywords | kev_tokens & stack_keywords)
        if hits:
            pts = min(len(hits) * 2.5, 10)
            score += pts
            factors["stack"] = round(pts, 1)
            reasons.append(f"Pertinent pour votre stack: {', '.join(hits[:4])}")

    if published:
        try:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if isinstance(published, datetime):
                age = (now - published.replace(tzinfo=None)).days
            elif isinstance(published, date):
                age = (now - datetime(published.year, published.month, published.day)).days
            else:
                age = (now - datetime.fromisoformat(str(published))).days
        except Exception:
            age = 999
        if age <= 30:
            score += 5
            factors["recency"] = 5
            reasons.append("Publiee il y a moins de 30 jours")
        elif age <= 90:
            score += 3
            factors["recency"] = 3

    score = round(min(score, 100))
    level = "CRITIQUE" if score >= 75 else "ELEVE" if score >= 50 else "MOYEN" if score >= 25 else "BAS"

    return {
        "cve_id": cve.get("cve_id"),
        "score": score,
        "level": level,
        "severity": severity or "",
        "cvss_score": cvss,
        "published": str(published) if published else None,
        "description": (cve.get("description") or "")[:400],
        "is_kev": bool(kev_row),
        "exploits_count": len(exploits),
        "factors": factors,
        "reasons": reasons,
        "risk_if_ignored": _risk_if_ignored(cvss, exploits, kev_row, level),
        "confidence": _confidence(factors),
        "sources": sorted(set(sources)),
    }


def _candidate_rows(days: int):
    """CVE recentes (fenetre, CRITICAL+HIGH uniquement) + toutes les CVE CISA KEV."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    since = datetime.now() - timedelta(days=days)
    cursor.execute(
        """
        SELECT cve_id, description, severity, cvss_score, published, weaknesses
        FROM cve_entries
        WHERE (published >= %s AND severity IN ('CRITICAL', 'HIGH'))
           OR weaknesses ILIKE '%%CISA_KEV%%'
        ORDER BY cvss_score DESC NULLS LAST, published DESC NULLS LAST
        LIMIT 3000
        """,
        (since,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [
        {
            "cve_id": r[0],
            "description": r[1],
            "severity": r[2],
            "cvss_score": r[3],
            "published": r[4],
            "weaknesses": r[5],
            "_tokens": set(re.findall(r"[a-z0-9]{3,}", (r[1] or "").lower())),
        }
        for r in rows
    ]


def get_priority_decisions(days: int = 90, limit: int = 20) -> list[dict]:
    """Retourne les decisions priorisees : top N CVE justifiees."""
    kev = _load_kev()
    stack = build_stack_keywords()
    decisions = []
    for cve in _candidate_rows(days):
        cve_id = cve["cve_id"]
        exploits = correlation.get_exploits_for_cve(cve_id)
        kev_row = kev.get(cve_id.upper())
        if not kev_row and cve.get("weaknesses") and "CISA_KEV" in str(cve.get("weaknesses", "")):
            kev_row = {"product": "", "vendor": "", "dueDate": "", "ransomware": ""}
        decisions.append(score_cve(cve, stack, exploits, kev_row))
    decisions.sort(key=lambda d: d["score"], reverse=True)
    return decisions[:limit]


def get_decision_summary(days: int = 90) -> dict:
    """Compteurs utiles pour l'ecran 'Aujourd'hui'."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    since = datetime.now() - timedelta(days=days)
    cursor.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE severity IN ('CRITICAL','HIGH')),
            COUNT(*) FILTER (WHERE weaknesses ILIKE '%%CISA_KEV%%')
        FROM cve_entries
        WHERE (published >= %s AND severity IN ('CRITICAL','HIGH'))
           OR weaknesses ILIKE '%%CISA_KEV%%'
        """,
        (since,),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    critical = row[0] if row else 0
    kev = row[1] if row else 0
    return {
        "window_days": days,
        "critiques": critical,
        "kev_actives": kev,
    }
