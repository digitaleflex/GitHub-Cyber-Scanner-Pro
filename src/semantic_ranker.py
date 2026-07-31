"""Classement semantique via Groq — traduit les requetes en langage naturel + re-ranke les resultats."""
import json
import logging
import os

import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

_RANK_PROMPT = (
    "Tu es un moteur de recherche semantique pour outils cybersecurite. "
    "Classe les depots suivants par PERTINENCE par rapport a la requete.\n"
    "Requete: {query}\n\n"
    "Depots:\n{repos}\n\n"
    "Retourne UNIQUEMENT un JSON: {{\"ranked\": [id1, id2, ...], \"explanation\": \"1 phrase en francais\"}}\n"
    "Garde les plus pertinents. Max 10 resultats."
)


def rank_results(query: str, repos: list[dict], top_k: int = 10) -> list[dict]:
    """Re-classe des resultats de recherche par pertinence semantique via Groq."""
    if not GROQ_API_KEY or not repos:
        return repos[:top_k]

    repo_list = "\n".join(
        f"  id={r.get('name','?')[:60]} | desc={r.get('desc','')[:120]}"
        for r in repos[:20]
    )
    prompt = _RANK_PROMPT.format(query=query, repos=repo_list)

    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 300, "temperature": 0.1},
            timeout=20,
        )
        if r.status_code != 200:
            logging.warning(f"Groq ranker {r.status_code}")
            return repos[:top_k]

        raw = r.json()["choices"][0]["message"]["content"].strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        ranked_ids = data.get("ranked", [])
        explanation = data.get("explanation", "")

        # Reorder
        id_map = {r.get("name", ""): r for r in repos}
        ranked = []
        seen = set()
        for rid in ranked_ids:
            if rid in id_map and rid not in seen:
                ranked.append({**id_map[rid], "ai_explanation": explanation})
                seen.add(rid)
        # Add remaining
        for r in repos:
            if r.get("name") not in seen:
                ranked.append(r)
        logging.info(f"🤖 Groq ranker: {len(ranked_ids)} classes, '{explanation[:80]}'")
        return ranked[:top_k]
    except Exception as e:
        logging.error(f"Erreur Groq ranker: {e}")
        return repos[:top_k]


def smart_search(query: str, limit: int = 20, use_ai_rank: bool = True) -> dict:
    """Recherche hybride: trigram + TF-IDF + re-rank IA."""
    from src import database
    import src.embeddings as embeddings

    # Trigram full-text search (primary)
    trigram = database.unified_search(query, limit=limit, types=["repo"], sort="relevance")
    # TF-IDF semantic search (secondary)
    semantic = embeddings.semantic_search(query, limit=limit)

    # Merge and deduplicate
    seen = set()
    merged = []
    for r in trigram.get("results", []) + semantic:
        key = r.get("name", "")
        if key and key not in seen:
            seen.add(key)
            merged.append(r)

    if use_ai_rank and merged and GROQ_API_KEY:
        merged = rank_results(query, merged, top_k=limit)

    return {"query": query, "total": len(merged), "results": merged,
            "facets": trigram.get("facets", {})}
