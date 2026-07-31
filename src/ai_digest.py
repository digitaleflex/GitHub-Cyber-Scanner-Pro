"""Digest IA quotidien — analyse les nouveaux depots et CVEs avec Groq."""
import json
import logging
import os
import re
from datetime import datetime, timezone

import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

_DIGEST_PROMPT = (
    "Tu es un analyste cybersecurite senior. Voici les nouveaux outils/outils decouverts "
    "sur GitHub dans les dernieres 24h et les CVE recentes. Genere un digest en francais.\n\n"
    "NOUVEAUX OUTILS (top 30):\n{repos}\n\n"
    "NOUVELLES CVE (top 15):\n{cves}\n\n"
    "Format JSON strict:\n"
    '{{"title": "titre accrocheur", "date": "date", "summary": "resume 2-3 phrases", '
    '"top_threats": [{{"name": "...", "severity": "CRITIQUE/ELEVE/MOYEN", "description": "..."}}], '
    '"trending_tools": [{{"name": "...", "category": "pentest/defense/malware/osint...", "why": "..."}}], '
    '"key_insight": "1 insight cle en francais", '
    '"stats": {{"new_repos": N, "new_cves": N}}}}\n'
    "top_threats: max 5, trending_tools: max 5. Reponds UNIQUEMENT en JSON."
)


def generate_digest() -> dict:
    """Genere le digest IA du jour et le sauvegarde. Retourne le digest."""
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY absent"}

    repos = _get_new_repos(limit=30)
    cves = _get_new_cves(limit=15)

    repo_text = "\n".join(
        f"- [{r[3] or '?'}] {r[0][:80]} | {r[1][:120] if r[1] else ''}"
        for r in repos
    ) or "(aucun nouveau depot)"
    cve_text = "\n".join(
        f"- {c[0]} [{c[1] or '?'}] {c[2][:120] if c[2] else ''}"
        for c in cves
    ) or "(aucune nouvelle CVE)"

    prompt = _DIGEST_PROMPT.format(repos=repo_text, cves=cve_text)

    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 800, "temperature": 0.4},
            timeout=45,
        )
        if r.status_code != 200:
            return {"error": f"Groq {r.status_code}: {r.text[:120]}"}

        raw = r.json()["choices"][0]["message"]["content"].strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        digest = json.loads(raw)
        digest["generated_at"] = datetime.now(timezone.utc).isoformat()

        # Cache in data/
        cache_path = os.path.join(os.path.dirname(__file__), "..", "data", "digest_latest.json")
        with open(cache_path, "w") as f:
            json.dump(digest, f, ensure_ascii=False, indent=2)

        logging.info(f"📰 Digest IA genere: {digest.get('title', '?')}")
        return digest
    except Exception as e:
        logging.error(f"Erreur digest IA: {e}")
        return {"error": str(e)}


def get_latest_digest() -> dict:
    """Retourne le dernier digest (depuis le cache ou le genere)."""
    cache_path = os.path.join(os.path.dirname(__file__), "..", "data", "digest_latest.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path) as f:
                return json.load(f)
        except Exception:
            pass
    return generate_digest()


def _get_new_repos(limit: int = 30) -> list:
    from src.database import get_db_connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT full_name, description, stars, security_verdict
               FROM repositories
               WHERE discovered_at >= NOW() - INTERVAL '24 hours'
               ORDER BY stars DESC NULLS LAST LIMIT %s""",
            (limit,),
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        logging.error(f"Erreur _get_new_repos: {e}")
        return []


def _get_new_cves(limit: int = 15) -> list:
    from src.database import get_db_connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT cve_id, severity, description
               FROM cve_entries
               WHERE discovered_at >= NOW() - INTERVAL '24 hours'
               ORDER BY 
                 CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,
                 discovered_at DESC
               LIMIT %s""",
            (limit,),
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        logging.error(f"Erreur _get_new_cves: {e}")
        return []
