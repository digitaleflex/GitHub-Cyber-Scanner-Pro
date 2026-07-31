"""OSINT Orchestrator — L'IA determine les outils a utiliser et la methodologie."""
import json
import logging
import os
import time

import requests

GROQ_KEY = os.getenv("GROQ_API_KEY", "")

# Catalogue des outils OSINT disponibles (depuis notre base + ceux qu'on peut lancer)
OSINT_TOOLS = {
    "github_search": {
        "name": "GitHub Profile Search",
        "tool": "src/osint_lab.py → search_github_user()",
        "what": "Trouve des profils GitHub par nom + localisation",
        "requires": "GITHUB_TOKEN",
    },
    "social_check": {
        "name": "Social Media Presence Check",
        "tool": "src/osint_lab.py → check_social_presence()",
        "what": "Verifie la presence sur 10 plateformes (GH, X, Reddit, LinkedIn...)",
        "requires": "rien (requetes HEAD gratuites)",
    },
    "dork_search": {
        "name": "Google Dorks (DuckDuckGo)",
        "tool": "src/osint_lab.py → search_dork()",
        "what": "Recherche web via DuckDuckGo lite",
        "requires": "rien",
    },
    "email_verify": {
        "name": "Email Domain Verification",
        "tool": "src/osint_lab.py → verify_email_domain()",
        "what": "Verifie si un domaine d'email existe (MX check)",
        "requires": "rien",
    },
    "ai_extraction": {
        "name": "AI Parameter Extraction (Groq)",
        "tool": "src/osint_lab.py → ai_extract_person()",
        "what": "Extrait nom, lieu, email, usernames du texte libre",
        "requires": "GROQ_API_KEY",
    },
    "ai_classification": {
        "name": "Target Classification (mDeBERTa)",
        "tool": "src/hf_client.py → classify_ml()",
        "what": "Classifie le type de cible (hacker, chercheur, dev...)",
        "requires": "HF_API_KEY",
    },
    "entity_extraction": {
        "name": "Named Entity Recognition",
        "tool": "src/hf_client.py → extract_entities()",
        "what": "Extrait noms, lieux, orgs du texte",
        "requires": "HF_API_KEY",
    },
    "summarization": {
        "name": "Profile Summarization",
        "tool": "src/hf_client.py → summarize()",
        "what": "Resume les bios et profils trouves",
        "requires": "HF_API_KEY",
    },
    "relevance_filter": {
        "name": "False Positive Filter",
        "tool": "src/hf_client.py → classify_zero_shot()",
        "what": "Elimine les faux positifs des resultats",
        "requires": "HF_API_KEY",
    },
    "semantic_search": {
        "name": "Similar Profile Search",
        "tool": "src/embeddings.py → semantic_search()",
        "what": "Trouve des profils similaires par similarite cosine",
        "requires": "pgvector",
    },
}

_METHODOLOGY_PROMPT = (
    "Tu es un expert OSINT. Analyse la cible et choisis les meilleurs outils parmi ce catalogue.\n\n"
    "CIBLE: {target}\n\n"
    "CATALOGUE D'OUTILS:\n{tools}\n\n"
    "Reponds UNIQUEMENT en JSON:\n"
    '{{"analysis": "1 phrase sur la cible", '
    '"recommended_tools": ["tool_id1", "tool_id2", ...], '
    '"execution_order": "etape par etape en francais (max 5 etapes)", '
    '"estimated_results": "ce quon peut esperer trouver", '
    '"limitations": "ce quon ne pourra PAS trouver avec ces outils", '
    '"alternative_approach": "si les outils echouent, que faire dautre"}}'
)


def analyze_and_recommend(target_text: str) -> dict:
    """L'IA analyse la cible et recommande les meilleurs outils OSINT."""
    if not GROQ_KEY:
        return {"error": "GROQ_API_KEY absent"}

    # Construire le catalogue
    tools_text = "\n".join(
        f"- {tid}: {t['name']} — {t['what']} (requis: {t['requires']})"
        for tid, t in OSINT_TOOLS.items()
    )

    prompt = _METHODOLOGY_PROMPT.format(target=target_text, tools=tools_text)

    try:
        import src.llm_router as llm
        result = llm.llm_complete_json(prompt, max_tokens=600)
        if result:
            # Enrichir avec les details des outils
            enriched = []
            for tid in result.get("recommended_tools", []):
                if tid in OSINT_TOOLS:
                    enriched.append({
                        "id": tid,
                        "name": OSINT_TOOLS[tid]["name"],
                        "what": OSINT_TOOLS[tid]["what"],
                        "ready": True,
                        "requires": OSINT_TOOLS[tid]["requires"],
                    })
            result["tools_ready"] = enriched
            result["total_tools_available"] = len(OSINT_TOOLS)
            logging.info(f"🎯 OSINT Orchestrator: {len(enriched)} outils recommandes pour '{target_text[:50]}'")
            return result
    except Exception as e:
        logging.error(f"Orchestrator: {e}")
    return {"error": "Analyse echouee"}


def run_recommended(target_text: str, tokens: list[str] = None) -> dict:
    """Analyse ET execute les outils recommandes. Retourne le rapport complet."""
    plan = analyze_and_recommend(target_text)
    if "error" in plan:
        return plan

    # Executer le pipeline OSINT complet
    import src.osint_pipeline as pipeline
    results = pipeline.run_full_pipeline(target_text, tokens)

    return {
        "plan": plan,
        "results": results,
        "summary": f"Plan: {len(plan.get('tools_ready',[]))} outils. "
                   f"Pipeline: {results.get('summary','')}",
    }
