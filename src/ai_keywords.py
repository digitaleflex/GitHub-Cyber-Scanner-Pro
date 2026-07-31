"""Decouverte de mots-cles cyber emergents via l'IA (Groq)."""
import json
import logging
import os
import re
import time

import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

_PROMPT = (
    "Tu es un expert en cybersecurite et analyse de code source. "
    "Voici des descriptions de depots GitHub. Extrais UNIQUEMENT les termes cyber pertinents "
    "(outils, techniques, frameworks, vulnerabilites, concepts de securite, protocoles) "
    "qui ne sont pas des mots generiques.\n\n"
    "REGLES:\n"
    "- Ignore les mots communs (security, tool, scanner, pentest, hacking, exploit)\n"
    "- Ignore les acronymes generiques (API, CLI, GUI, HTTP, TLS)\n"
    "- Ignore les technologies standard (Python, Docker, Linux, Windows, AWS, React)\n"
    "- Cherche des termes SPECIFIQUES et EMERGENTS (ex: kerberoasting, dll-sideloading, prompt-injection, mcp-hijack)\n"
    "- Max 1 terme par ligne, en minuscules\n"
    "- Format JSON strict: {\"keywords\": [\"terme1\", \"terme2\", ...], \"category\": \"<categorie>\"}\n"
    "- Categories: pentest, defense, malware, osint, exploit, ctf, cloud, iot, llm, mobile, forensics, crypto, network, web, social\n"
    "- Max 15 termes au total, seulement les plus pertinents\n\n"
    "Descriptions:\n{descriptions}\n\n"
    "Reponds UNIQUEMENT avec le JSON, pas de texte supplementaire."
)


def discover_from_descriptions(descriptions: list[str], existing_terms: set[str] | None = None) -> list[dict]:
    """Envoie un batch de descriptions a Groq et retourne les mots-cles decouverts."""
    if not GROQ_API_KEY:
        logging.warning("GROQ_API_KEY absent, decouverte IA desactivee")
        return []

    existing = existing_terms or set()
    text = "\n".join(f"- {d[:200]}" for d in descriptions[:20] if d)
    prompt = _PROMPT.replace("{descriptions}", text)

    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.3,
            },
            timeout=30,
        )
        if r.status_code != 200:
            logging.warning(f"Groq keywords API {r.status_code}: {r.text[:120]}")
            return []

        raw = r.json()["choices"][0]["message"]["content"].strip()
        # Nettoyage markdown fences
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        terms = data.get("keywords", [])
        category = data.get("category", "pentest")

        results = []
        seen = set()
        for term in terms:
            t = re.sub(r"[^a-z0-9\-_ ]", "", str(term).lower().strip())
            if len(t) < 3 or len(t) > 60 or t in existing or t in seen:
                continue
            if t in _BLACKLIST:
                continue
            seen.add(t)
            results.append({"term": t, "category_guess": category, "score": 0.70, "sources": 1,
                            "source_samples": f"AI discovery from repo batch"})
        return results

    except Exception as e:
        logging.error(f"Erreur decouverte IA keywords: {e}")
        return []


def batch_discover(limit: int = 30) -> int:
    """Decouvre des mots-cles dans les repos non traites. Retourne le nb sauvegarde."""
    import time
    from src import database

    descs, known = _get_descriptions(limit)
    if not descs:
        return 0

    candidates = discover_from_descriptions(descs, known)
    if not candidates:
        return 0

    try:
        saved = database.save_discovered_keywords(candidates)
        logging.info(f"🧠 AI keywords: {saved} nouveau(x) mot(s)-cle(s) decouvert(s)")
        return saved
    except Exception as e:
        logging.error(f"Erreur sauvegarde AI keywords: {e}")
        return 0


def _get_descriptions(limit: int = 30) -> tuple[list[str], set[str]]:
    from src.database import get_db_connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT description FROM repositories
               WHERE description IS NOT NULL AND description != ''
               ORDER BY RANDOM() LIMIT %s""",
            (limit,),
        )
        descs = [r[0] for r in cursor.fetchall()]

        cursor.execute("SELECT term FROM discovered_keywords")
        known = {r[0].lower() for r in cursor.fetchall()}
        cursor.close()
        conn.close()
        return descs, known
    except Exception as e:
        logging.error(f"Erreur _get_descriptions: {e}")
        return [], set()


_BLACKLIST = {
    "security", "tool", "tools", "scanner", "pentest", "hacking", "exploit",
    "framework", "library", "script", "payload", "bypass", "attack", "defense",
    "python", "docker", "linux", "windows", "aws", "github", "api", "cli",
    "gui", "http", "https", "tls", "ssl", "dns", "ssh", "ftp", "vpn",
    "react", "node", "typescript", "javascript", "rust", "golang", "java",
    "c", "c++", "ruby", "php", "perl", "bash", "powershell", "sql",
    "test", "testing", "setup", "config", "configuration", "example",
    "demo", "sample", "template", "tutorial", "documentation", "readme",
}
