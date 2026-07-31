"""Agent IA CVE — resume et priorise chaque CVE via Groq."""
import json
import logging
import os

import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

_CVE_PROMPT = (
    "Tu es un expert en cybersecurite. Analyse cette CVE et donne une fiche pratique en francais.\n\n"
    "CVE: {cve_id}\n"
    "Description: {description}\n"
    "CVSS: {cvss}\n"
    "Severite: {severity}\n"
    "CISA KEV (exploitee activement): {kev}\n"
    "Exploits disponibles: {exploits_count}\n\n"
    "Reponds UNIQUEMENT en JSON strict avec:\n"
    '{{"summary": "1-2 phrases en francais expliquant la vuln", '
    '"impact": "ce que ca permet a un attaquant", '
    '"recommendation": "que faire maintenant (patch/version/solution)", '
    '"patched_in": "version corrigee si mentionnee, sinon null", '
    '"exploitation_likelihood": "FAIBLE/MOYEN/CRITIQUE", '
    '"audience": "qui doit patcher en priorite (tous/admin/dev)"}}\n'
    "Reponds UNIQUEMENT le JSON, rien d'autre."
)

_cve_cache = {}  # {cve_id: dict ou None}


def analyze_cve(cve_id: str, description: str = "", cvss: str = "", severity: str = "", kev: bool = False, exploits_count: int = 0) -> dict:
    """Analyse une CVE avec Groq et retourne un dict d'analyse."""
    if not GROQ_API_KEY:
        return _fallback(cve_id, "GROQ_API_KEY absent")

    if cve_id in _cve_cache:
        return _cve_cache[cve_id]

    prompt = _CVE_PROMPT.format(
        cve_id=cve_id,
        description=description or "(aucune)",
        cvss=cvss or "?",
        severity=severity or "?",
        kev="OUI" if kev else "NON",
        exploits_count=exploits_count,
    )

    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 400, "temperature": 0.2},
            timeout=20,
        )
        if r.status_code != 200:
            return _fallback(cve_id, f"Groq {r.status_code}")

        raw = r.json()["choices"][0]["message"]["content"].strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        data["cve_id"] = cve_id
        _cve_cache[cve_id] = data
        return data
    except Exception as e:
        logging.error(f"Erreur Agent CVE {cve_id}: {e}")
        return _fallback(cve_id, str(e))


def _fallback(cve_id: str, reason: str) -> dict:
    return {
        "cve_id": cve_id,
        "summary": f"Analyse indisponible ({reason})",
        "impact": "Information non disponible",
        "recommendation": "Verifier manuellement la CVE sur NVD",
        "patched_in": None,
        "exploitation_likelihood": "INCONNU",
        "audience": "equipe securite",
    }


def batch_analyze_recent(limit: int = 10) -> int:
    """Analyse les CVE recentes (sans analyse) en batch. Retourne nb analyse."""
    from src.database import get_db_connection
    from psycopg2.extras import RealDictCursor
    import src.correlation as corr

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    # On prend les CVE qui n'ont pas encore d'analyse IA
    cursor.execute("""
        SELECT cve_id, description, severity, cvss_score
        FROM cve_entries
        WHERE (description IS NOT NULL AND description != '')
          AND (weaknesses IS NULL OR weaknesses NOT LIKE '%%AI_ANALYSIS%%')
        ORDER BY
            CASE WHEN weaknesses ILIKE '%%CISA_KEV%%' THEN 0 ELSE 1 END,
            cvss_score DESC NULLS LAST,
            published DESC NULLS LAST
        LIMIT %s
    """, (limit,))
    rows = cursor.fetchall()
    analyzed = 0
    for r in rows:
        cve_id = r["cve_id"]
        exploits = corr.get_exploits_for_cve(cve_id)
        result = analyze_cve(
            cve_id, r.get("description", ""), str(r.get("cvss_score", "")),
            r.get("severity", ""), False, len(exploits),
        )
        if result.get("summary") and "indisponible" not in result["summary"]:
            # Stocker dans la DB (colonne weaknesses en mode cache)
            cursor.execute(
                "UPDATE cve_entries SET weaknesses = COALESCE(weaknesses, '') || ' | AI_ANALYSIS:' || %s WHERE cve_id = %s",
                (json.dumps(result)[:1500], cve_id),
            )
            analyzed += 1
    conn.commit()
    cursor.close()
    conn.close()
    return analyzed


def get_analyzed_cve(cve_id: str) -> dict:
    """Recupere l'analyse IA d'une CVE (depuis la DB ou le cache)."""
    if cve_id in _cve_cache:
        return _cve_cache[cve_id]

    from src.database import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT weaknesses FROM cve_entries WHERE cve_id = %s", (cve_id.upper(),))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row or not row[0] or "AI_ANALYSIS:" not in str(row[0]):
        return {}

    try:
        marker = "AI_ANALYSIS:"
        text = str(row[0])
        idx = text.find(marker)
        if idx >= 0:
            import json as _json
            data = _json.loads(text[idx + len(marker):])
            _cve_cache[cve_id] = data
            return data
    except Exception:
        pass
    return {}
