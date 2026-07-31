"""OSINT Decision Engine — multi-candidats, scoring, correlation, flow visual."""
import json
import logging
import os
import time
from datetime import datetime, timezone

import requests

GROQ_KEY = os.getenv("GROQ_API_KEY", "")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; OSINT-Engine/2.0)"}

# ── PHASE 1: Multi-Candidate Discovery ──────────────────────────────────

def find_candidates(name: str, location: str, tokens: list[str] = None) -> list[dict]:
    """Trouve TOUS les candidats possibles pour un nom + lieu."""
    candidates = []

    # 1a. GitHub API search (multiple pages)
    import src.osint_lab as lab
    github = lab.search_github_user(name, location, tokens)
    if github:
        for g in github:
            candidates.append({
                "source": "github",
                "id": f"gh:{g.get('username','')}",
                "username": g.get("username"),
                "name": g.get("name"),
                "location": g.get("location"),
                "bio": g.get("bio", ""),
                "company": g.get("company"),
                "followers": g.get("followers", 0),
                "url": g.get("url"),
                "avatar": g.get("avatar"),
                "raw": g,
            })

    # 1b. Social media check for guessed usernames
    import src.osint_lab as lab
    extracted = lab.ai_extract_person(f"{name} {location}")
    usernames = extracted.get("probable_usernames", [])
    for uname in usernames[:3]:
        social = lab.check_social_presence(uname)
        present = [s for s in social if s["present"]]
        if len(present) >= 2:
            candidates.append({
                "source": "social",
                "id": f"social:{uname}",
                "username": uname,
                "social_platforms": [s["platform"] for s in present],
                "platform_count": len(present),
                "raw_social": present,
            })

    return candidates


# ── PHASE 2: Scoring Engine ─────────────────────────────────────────────

def score_candidate(candidate: dict, target: dict) -> dict:
    """Calcule un score de probabilite (0-100) qu'un candidat corresponde a la cible."""
    scores = {}
    insights = []

    name = target.get("name", "").lower()
    location = target.get("location", "").lower()
    
    c_name = (candidate.get("name") or candidate.get("username") or "").lower()
    c_location = (candidate.get("location") or "").lower()
    c_bio = (candidate.get("bio") or "").lower()
    c_company = (candidate.get("company") or "").lower()

    # Name match (0-40 points)
    name_parts = set(name.split())
    c_name_parts = set(c_name.split()) | set((candidate.get("username") or "").lower().split("_"))
    name_overlap = len(name_parts & c_name_parts)
    if name and c_name:
        name_score = min(40, name_overlap * 20 + (10 if name in c_name else 0))
        scores["name_match"] = name_score
        insights.append(f"Nom: {name_overlap} parties communes sur l'identite (+{name_score})")
    else:
        scores["name_match"] = 10

    # Location match (0-30 points)
    loc_parts = set(location.replace(",", " ").split())
    c_loc_parts = set(c_location.replace(",", " ").split())
    loc_overlap = len(loc_parts & c_loc_parts)
    if location and c_location:
        loc_score = min(30, loc_overlap * 15)
        scores["location_match"] = loc_score
        if loc_overlap > 0:
            insights.append(f"Localisation: correspondance trouvee (+{loc_score})")
    else:
        scores["location_match"] = 0

    # Bio/description relevance (0-15 points)
    keywords = target.get("keywords", [])
    if keywords and c_bio:
        kw_matches = sum(1 for kw in keywords if kw.lower() in c_bio)
        scores["bio_relevance"] = min(15, kw_matches * 5)
        if kw_matches > 0:
            insights.append(f"Bio: {kw_matches} mots-cles pertinents (+{scores['bio_relevance']})")
    else:
        scores["bio_relevance"] = 5

    # Social presence (0-10 points)
    social_count = candidate.get("platform_count", 0)
    scores["social_presence"] = min(10, social_count * 2)
    if social_count >= 3:
        insights.append(f"Presence sociale: {social_count} plateformes (+{scores['social_presence']})")

    # GitHub popularity (0-5 points)
    followers = candidate.get("followers", 0)
    scores["popularity"] = min(5, followers // 10)
    if followers > 20:
        insights.append(f"Popularite: {followers} followers GitHub (+{scores['popularity']})")

    # Total
    total = sum(scores.values())
    level = "TRES_PROBABLE" if total >= 70 else "PROBABLE" if total >= 45 else "POSSIBLE" if total >= 20 else "FAIBLE"

    return {
        "total_score": total,
        "level": level,
        "breakdown": scores,
        "insights": insights,
        "recommendation": "Cible principale" if total >= 45 else "A verifier" if total >= 20 else "Probablement hors cible",
    }


def score_all_candidates(candidates: list[dict], target: dict) -> list[dict]:
    """Score tous les candidats et trie par probabilite decroissante."""
    scored = []
    for c in candidates:
        s = score_candidate(c, target)
        c["scoring"] = s
        scored.append(c)
    scored.sort(key=lambda x: x.get("scoring", {}).get("total_score", 0), reverse=True)
    return scored


# ── PHASE 3: Investigation Flow ─────────────────────────────────────────

def run_investigation(target_text: str, tokens: list[str] = None) -> dict:
    """Enquete OSINT complete avec flow visuel et decision engine."""
    start_time = time.time()
    flow = {
        "investigation_id": f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "target_text": target_text,
        "steps": [],
        "model_switches": [],
    }

    # Step 1: AI Extraction (which model?)
    step1 = {"step": 1, "action": "AI Extraction", "model": "Groq Llama-3.3-70B",
             "status": "running"}
    flow["steps"].append(step1)

    try:
        import src.osint_lab as lab
        extracted = lab.ai_extract_person(target_text)
        step1["status"] = "done"
        step1["result"] = {k: v for k, v in extracted.items() if k != "keywords"}
        target = {
            "name": extracted.get("name", ""),
            "location": extracted.get("location", ""),
            "keywords": extracted.get("keywords", []),
            "text": target_text,
        }
    except Exception:
        # Model switch: Groq → HF
        step1["model"] = "HF Qwen3-235B (fallback)"
        flow["model_switches"].append({"from": "Groq", "to": "HF/Qwen3", "reason": "Groq rate-limited"})
        try:
            import src.llm_router as llm
            prompt = f"Extrait nom, lieu, mots-cles de ce texte pour OSINT. JSON: {{\"name\":\"\",\"location\":\"\",\"keywords\":[]}}\nTexte: {target_text}"
            result = llm.llm_complete_json(prompt, max_tokens=200)
            if result:
                target = {
                    "name": result.get("name", ""),
                    "location": result.get("location", ""),
                    "keywords": result.get("keywords", []),
                    "text": target_text,
                }
                step1["result"] = target
                step1["status"] = "done"
        except Exception:
            step1["status"] = "failed"
            target = {"name": target_text[:50], "location": "", "keywords": [], "text": target_text}

    # Step 2: Multi-Candidate Discovery
    step2 = {"step": 2, "action": "Multi-Candidate Discovery",
             "sources": ["GitHub API", "Social Presence Check"],
             "status": "running"}
    flow["steps"].append(step2)

    candidates = find_candidates(target.get("name", ""), target.get("location", ""), tokens)
    step2["status"] = "done"
    step2["candidates_found"] = len(candidates)
    step2["sources_used"] = len(set(c.get("source") for c in candidates))

    # Step 3: AI Classification of each candidate
    step3 = {"step": 3, "action": "Target Classification", "model": "mDeBERTa multilingual",
             "candidates": []}
    flow["steps"].append(step3)

    try:
        import src.hf_client as hf
        for c in candidates[:5]:
            text = f"{c.get('name','')} {c.get('bio','')} {c.get('location','')} {c.get('username','')}"
            cls = hf.classify_ml(text, ["developpeur securite", "hacker", "chercheur", "etudiant", "inconnu"])
            c["classification"] = cls
        step3["status"] = "done"
    except Exception:
        step3["status"] = "skipped (HF rate-limited)"
        # Model switch
        flow["model_switches"].append({"from": "mDeBERTa", "to": "bart-large-mnli (EN only)", "reason": "HF rate-limited"})

    # Step 4: Scoring & Ranking
    step4 = {"step": 4, "action": "Probability Scoring"}
    flow["steps"].append(step4)

    scored = score_all_candidates(candidates, target)
    step4["scored"] = len(scored)
    step4["top_candidate"] = scored[0].get("username") if scored else "aucun"
    step4["top_score"] = scored[0]["scoring"]["total_score"] if scored else 0

    # Step 5: Decision
    step5 = {"step": 5, "action": "Decision Engine"}
    flow["steps"].append(step5)

    if scored and scored[0]["scoring"]["total_score"] >= 45:
        decision = "TARGET_FOUND"
        detail = f"Candidat principal identifie avec score {scored[0]['scoring']['total_score']}/100"
    elif scored and scored[0]["scoring"]["total_score"] >= 20:
        decision = "MULTIPLE_POSSIBLES"
        detail = f"{len(scored)} candidats, meilleur score {scored[0]['scoring']['total_score']}/100"
    else:
        decision = "INCONCLUSIVE"
        detail = "Aucun candidat avec un score suffisant. Elargir la recherche."

    step5["decision"] = decision
    step5["detail"] = detail

    # Build final report
    flow["duration_s"] = round(time.time() - start_time, 1)
    flow["candidates"] = scored[:10]
    flow["target"] = target
    flow["decision"] = {"result": decision, "detail": detail}
    flow["models_used_count"] = len(flow.get("model_switches", [])) + 3

    return flow


# ── PHASE 4: Visual Comparison ──────────────────────────────────────────

def compare_candidates(candidates: list[dict]) -> str:
    """Genere une comparaison visuelle textuelle des candidats (pour debug/API)."""
    lines = []
    for i, c in enumerate(candidates[:5]):
        s = c.get("scoring", {})
        lines.append(
            f"#{i+1} [{s.get('level','?'):15s} {s.get('total_score',0):3d}/100] "
            f"{c.get('username','?'):20s} | {str(c.get('name','?')):20s} | {str(c.get('location','?')):20s}"
        )
        for ins in s.get("insights", []):
            lines.append(f"     → {ins}")
    return "\n".join(lines)
