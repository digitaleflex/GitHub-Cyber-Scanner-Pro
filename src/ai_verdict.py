import logging
import os

import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

_PROMPT = (
    "Tu es un analyste en cybersecurite. Analyse ce depot GitHub et donne un verdict "
    "EXACTEMENT dans ce format sur une seule ligne:\n"
    "VERDICT: <Sain|Suspect|Critique> | JUSTIFICATION: <une phrase en francais, max 120 chars>\n\n"
    "Critique = malware, ransomware, phishing kit, C2, backdoor, stealer, keylogger, botnet, "
    "exploit sans usage legitime, outil d'attaque pur, credential harvester.\n"
    "Suspect = outil a double usage (pentest/attack), OSINT agressif, bruteforce, "
    "doxing, code obfusque sans raison legitime, usage limite aux red teams.\n"
    "Sain = outil defensif, educatif, recherche legitime, outil dev, "
    "CTF, scanner de vulnerabilite legitime, durcissement, monitoring.\n\n"
    "Description: {description}\n"
    "README (extrait): {readme}\n"
)


def analyze_repo(description: str, readme: str = "", timeout: int = 15) -> dict:
    if not GROQ_API_KEY:
        return {"verdict": None, "justification": "GROQ_API_KEY absent"}

    readme = (readme or "")[:1500]
    description = (description or "")[:500]
    prompt = _PROMPT.format(description=description or "(aucune)", readme=readme or "(aucun)")

    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 80,
                "temperature": 0.1,
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            logging.warning(f"Groq API {r.status_code}: {r.text[:120]}")
            return {"verdict": None, "justification": f"API {r.status_code}"}

        content = r.json()["choices"][0]["message"]["content"].strip()

        import re
        v = re.search(r"VERDICT:\s*(Sain|Suspect|Critique)", content, re.IGNORECASE)
        j = re.search(r"JUSTIFICATION:\s*(.+)", content, re.IGNORECASE)
        verdict = v.group(1).capitalize() if v else "Suspect"
        justification = j.group(1).strip()[:200] if j else content[:200]

        return {"verdict": verdict, "justification": justification, "raw": content}
    except Exception as e:
        logging.error(f"Erreur analyse IA: {e}")
        return {"verdict": None, "justification": str(e)[:120]}


def batch_analyze_unverified(limit: int = 10) -> int:
    """Analyse les repos sans verdict de securite. Retourne le nombre traite."""
    import time
    from src import database

    repos = _get_unverified_repos(limit)
    if not repos:
        logging.info("Aucun depot non audite a analyser via IA.")
        return 0

    updated = 0
    for repo in repos:
        verdict = analyze_repo(repo.get("description", ""), repo.get("readme", ""))
        if verdict["verdict"]:
            database.update_repo_security_verdict(
                repo["id"],
                verdict["verdict"],
                verdict.get("justification", ""),
            )
            updated += 1
            logging.info(
                f"🤖 IA verdict: {verdict['verdict']} → {repo.get('full_name', '?')[:80]}"
            )
        time.sleep(0.3)  # rate-limit amical pour Groq free tier (30 req/min)
    return updated


def _get_unverified_repos(limit: int = 10) -> list[dict]:
    from src.database import get_db_connection
    from psycopg2.extras import RealDictCursor

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """SELECT id, full_name, description
               FROM repositories
               WHERE security_verdict IS NULL
               ORDER BY stars DESC NULLS LAST
               LIMIT %s""",
            (limit,),
        )
        rows = cursor.fetchall()
        # Fetch readme for each (best-effort)
        for row in rows:
            try:
                c2 = conn.cursor()
                c2.execute(
                    "SELECT content FROM resource_chunks WHERE repo_id = %s AND chunk_type = 'readme' LIMIT 1",
                    (row["id"],),
                )
                chunk = c2.fetchone()
                row["readme"] = chunk["content"][:1500] if chunk else ""
                c2.close()
            except Exception:
                row["readme"] = ""
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"Erreur _get_unverified_repos: {e}")
        return []
