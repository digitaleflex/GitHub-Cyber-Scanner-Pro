"""Agent IA GitHub — categorise automatiquement les repos via Groq."""
import json
import logging
import os

import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

_CATEGORIES = [
    "Red Team / Offensif", "Blue Team / Defensif", "Exploit / PoC",
    "Malware / Ransomware", "OSINT / Recon", "Forensics / DFIR",
    "Cloud Security", "Network / Scan", "Web Security",
    "Mobile Security", "Reverse Engineering", "Cryptography",
    "Threat Intelligence / CTI", "Vulnerability Scanner",
    "Documentation / Formation", "Honeypot / Deception",
    "Supply Chain / SBOM", "LLM / AI Security",
]

_RANK_PROMPT = (
    "Tu es un expert en cybersecurite. Categorise ce depot GitHub selon sa description et son README.\n\n"
    "Depot: {name}\nDescription: {description}\nREADME: {readme}\n\n"
    "Categories disponibles: {categories}\n\n"
    "Reponds UNIQUEMENT en JSON: {{\"category\": \"<categorie la plus proche>\", \"subcategory\": \"sous-categorie\", \"level\": \"debutant/intermediaire/expert\", \"confidence\": 0.0-1.0, \"keywords\": [\"tag1\", \"tag2\", \"tag3\"]}}\n"
    "La categorie doit etre la plus pertinente parmi la liste."
)


def categorize_repo(name: str, description: str = "", readme: str = "") -> dict:
    """Categorise un repo via Groq. Retourne category, subcategory, level, keywords."""
    if not GROQ_API_KEY:
        return _fallback()

    readme_short = (readme or "")[:1000]
    prompt = _RANK_PROMPT.format(
        name=name or "?", description=description or "(aucune)",
        readme=readme_short or "(non disponible)",
        categories=", ".join(_CATEGORIES),
    )
    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 300, "temperature": 0.2},
            timeout=15,
        )
        if r.status_code != 200:
            return _fallback()
        raw = r.json()["choices"][0]["message"]["content"].strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        data.setdefault("category", "Non classe")
        data.setdefault("confidence", 0.5)
        return data
    except Exception as e:
        logging.warning(f"Agent GitHub {name}: {e}")
        return _fallback()


def _fallback() -> dict:
    return {"category": "Non classe", "subcategory": "", "level": "intermediaire", "confidence": 0.0, "keywords": []}


def batch_categorize(limit: int = 15) -> int:
    """Categorise les repos sans categorie IA. Retourne nb traites."""
    from src.database import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor()
    # On prend les repos avec description mais sans ai_category
    try:
        cursor.execute(
            "ALTER TABLE repositories ADD COLUMN IF NOT EXISTS ai_category VARCHAR(50)"
        )
        conn.commit()
    except Exception:
        conn.rollback()

    cursor.execute("""
        SELECT full_name, description, id FROM repositories
        WHERE description IS NOT NULL AND description != ''
          AND (ai_category IS NULL OR ai_category = '')
        ORDER BY stars DESC NULLS LAST LIMIT %s
    """, (limit,))
    rows = cursor.fetchall()
    updated = 0
    for row in rows:
        name, desc, repo_id = row
        result = categorize_repo(name, desc)
        if result["category"] and result["category"] != "Non classe":
            cursor.execute(
                "UPDATE repositories SET ai_category = %s WHERE id = %s",
                (result["category"], repo_id),
            )
            updated += 1
            logging.info(f"🏷️ {result['category']} ← {name[:60]}")
    conn.commit()
    cursor.close()
    conn.close()
    return updated
