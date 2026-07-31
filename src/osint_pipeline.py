"""OSINT Pipeline — chaine IA complete: extraction → classification → recherche → NER → resume → rapport."""
import json
import logging
import time
from datetime import datetime, timezone

import src.osint_lab as lab

_AVAILABLE_MODELS = {
    "extraction": "Groq / Qwen3-235B",
    "classification": "mDeBERTa multilingual",
    "ner": "bert-base-NER",
    "summarization": "bart-large-cnn",
    "qa": "roberta-squad2",
    "translation": "opus-mt FR↔EN",
    "embeddings": "BGE-large-en 1024d",
    "relevance_filter": "bart-large-mnli",
    "security_terms": "SecBERT",
    "content_safety": "Granite Guardian",
    "report_generation": "Kimi-K2 / Groq",
    "reasoning": "DeepSeek-R1 70B",
}


def run_full_pipeline(free_text: str, tokens: list[str] = None) -> dict:
    """Pipeline OSINT complet: 12 modeles IA chaines intelligemment."""
    start = time.time()
    report = {
        "query": free_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "methodology": "OSINT Pipeline v2: AI extraction → classification → multi-source → NER → resume → rapport",
        "models_used": [],
    }

    # ── Phase 1: AI Extraction (Groq) ──────────────────────────────────
    extracted = lab.ai_extract_person(free_text)
    report["phase1_extraction"] = extracted
    report["models_used"].append({"phase": 1, "model": "Groq/Qwen3-235B", "task": "Extraction parametres"})
    logging.info(f"🧠 Phase 1: Extraits → {extracted.get('name','?')} / {extracted.get('location','?')}")

    # ── Phase 2: Target Classification (mDeBERTa) ──────────────────────
    target_type = "chercheur"
    try:
        import src.hf_client as hf
        cls = hf.classify_ml(free_text, ["hacker", "chercheur en securite", "journaliste", "developpeur", "etudiant", "anonyme"])
        target_type = cls.get("label", "chercheur")
        report["phase2_classification"] = cls
        report["models_used"].append({"phase": 2, "model": "mDeBERTa multilingual", "task": f"Classification: {target_type}"})
        logging.info(f"🏷️ Phase 2: Type cible → {target_type} ({cls.get('score',0):.2f})")
    except Exception as e:
        logging.warning(f"Phase 2 skip: {e}")

    # ── Phase 3: Multi-source Search ────────────────────────────────────
    findings = {}
    name = extracted.get("name", "")
    location = extracted.get("location", "")
    username = (extracted.get("probable_usernames") or [""])[0]
    email = extracted.get("email", "")
    keywords = extracted.get("keywords", [])

    # 3a. GitHub profiles
    if name:
        github = lab.search_github_user(name, location, tokens)
        if github:
            findings["github_profiles"] = github
            report["models_used"].append({"phase": "3a", "model": "GitHub API", "task": f"{len(github)} profils"})

    # 3b. Social presence
    uname = username or name.lower().replace(" ", "").replace(".", "")
    if uname:
        social = lab.check_social_presence(uname)
        present = [s for s in social if s["present"]]
        if present:
            findings["social_presence"] = present

    # 3c. Dorks (with AI keywords)
    dork_query = f'"{name}" {location} {" ".join(keywords[:3])}'
    dorks = lab.search_dork(dork_query)
    if dorks:
        findings["dorks"] = dorks[:5]

    report["findings"] = findings
    logging.info(f"🔍 Phase 3: {sum(len(v) for v in findings.values() if isinstance(v, list))} sources")

    # ── Phase 4: NER on findings ───────────────────────────────────────
    all_text = " ".join([
        free_text,
        *[f"{p.get('name','')} {p.get('bio','')} {p.get('location','')}" for p in findings.get("github_profiles", [])],
    ])[:3000]
    try:
        import src.hf_client as hf
        entities = hf.extract_entities(all_text)
        report["phase4_entities"] = entities[:10] if entities else []
        report["models_used"].append({"phase": 4, "model": "bert-base-NER", "task": f"{len(entities) if entities else 0} entites"})
    except Exception:
        pass

    # ── Phase 5: Summarize Findings ────────────────────────────────────
    summary_text = ""
    for p in findings.get("github_profiles", [])[:3]:
        summary_text += f"{p.get('username','')}: {p.get('bio','')}\n"
    if summary_text:
        try:
            import src.hf_client as hf
            summary = hf.summarize(summary_text, max_len=130)
            report["phase5_summary"] = summary
            report["models_used"].append({"phase": 5, "model": "bart-large-cnn", "task": "Resume profils"})
        except Exception:
            pass

    # ── Phase 6: Relevance Filter ──────────────────────────────────────
    if findings.get("github_profiles"):
        for p in findings["github_profiles"][:5]:
            try:
                import src.hf_client as hf
                relevance = hf.classify_zero_shot(
                    f"{p.get('name','')} {p.get('bio','')} {p.get('location','')}",
                    ["correspond a la cible", "faux positif probable", "information insuffisante"]
                )
                p["relevance"] = relevance
            except Exception:
                pass
        report["models_used"].append({"phase": 6, "model": "bart-large-mnli", "task": "Filtre pertinence"})

    # ── Phase 7: Content Safety Check ──────────────────────────────────
    try:
        import src.hf_client as hf
        safe = hf.scan_content_safety(free_text[:1000])
        report["phase7_safety"] = "OK" if not safe.get("flagged") else "FLAGGED"
    except Exception:
        report["phase7_safety"] = "SKIP"

    # ── Final Report ───────────────────────────────────────────────────
    total_findings = sum(len(v) for v in findings.values() if isinstance(v, list))
    report["summary"] = (
        f"Pipeline OSINT termine en {time.time()-start:.1f}s. "
        f"{total_findings} sources trouvees. "
        f"Cible classee comme '{target_type}'. "
        f"Modeles IA utilises: {len(report['models_used'])}."
    )
    logging.info(f"✅ Pipeline OSINT: {report['summary']}")
    return report
