"""Agent IA Tendances — detecte les sujets emergents de la semaine via Groq."""
import json
import logging
import os

import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

_TREND_PROMPT = (
    "Tu es un expert en cybersecurite. Analyse ces donnees et detecte les 5 tendances emergentes.\n\n"
    "Nouveaux outils cette semaine:\n{repos}\n\n"
    "Nouvelles CVE critiques:\n{cves}\n\n"
    "Reponds UNIQUEMENT en JSON: {{\"trends\": [{{\"topic\": \"sujet\", \"description\": \"1 phrase\", \"momentum\": \"HAUSSE/STABLE/BAISSE\", \"evidence\": [\"outil1\", \"outil2\"]}}], \"summary\": \"1 phrase globale\"}}"
)


def detect_trends() -> dict:
    """Detecte les tendances emergentes de la semaine. Retourne le JSON."""
    if not GROQ_API_KEY:
        return {"trends": [], "summary": "GROQ_API_KEY absent"}

    from src.database import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor()

    # Top 15 nouveaux repos de la semaine
    cursor.execute("""
        SELECT full_name, description FROM repositories
        WHERE discovered_at >= NOW() - INTERVAL '7 days'
        ORDER BY stars DESC NULLS LAST LIMIT 15
    """)
    repos = cursor.fetchall()
    repo_text = "\n".join(f"- {r[0]}: {r[1] or ''}" for r in repos) or "(aucun)"

    # Top 10 nouvelles CVE critiques
    cursor.execute("""
        SELECT cve_id, description FROM cve_entries
        WHERE discovered_at >= NOW() - INTERVAL '7 days'
          AND severity IN ('CRITICAL', 'HIGH')
        ORDER BY discovered_at DESC LIMIT 10
    """)
    cves = cursor.fetchall()
    cve_text = "\n".join(f"- {c[0]}: {c[1] or ''}" for c in cves) or "(aucune)"
    cursor.close()
    conn.close()

    prompt = _TREND_PROMPT.format(repos=repo_text, cves=cve_text)
    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 500, "temperature": 0.3},
            timeout=30,
        )
        if r.status_code != 200:
            return {"trends": [], "summary": f"Groq {r.status_code}"}
        raw = r.json()["choices"][0]["message"]["content"].strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        logging.info(f"📈 Trend Agent: {len(data.get('trends', []))} tendances detectees")
        return data
    except Exception as e:
        return {"trends": [], "summary": str(e)}
