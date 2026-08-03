"""FastAPI routes for Cyber Scanner Pro."""
import logging
import json
import os
from datetime import datetime
from fastapi import BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from src.config import app, FRONTEND_DIR, DOMAIN, EXCEL_FILE, JSON_FILE
from src import database
import src.ontology_enricher as ontology_enricher
import src.keyword_sources as keyword_sources
import src.auth
from fastapi import Depends
import src.nlp_processor as nlp_processor
import src.scan_engine as _engine
from src.exports import export_to_excel, export_to_json, export_reports

# --- ROUTAGE FASTAPI ---

@app.get("/", response_class=HTMLResponse)
def read_index():
    """Sert le frontend React SPA."""
    react_index = FRONTEND_DIR / "index.html"
    if react_index.exists():
        return HTMLResponse(react_index.read_text())
    return "<h1>Erreur : Frontend non disponible.</h1>"


@app.get("/api/stats")
def get_stats():
    """Retourne les statistiques (format compatible frontend React)."""
    # scanner_status handled via _engine
    (total_repos, total_stars, languages, lang_dist, last_scan, critique,
     suspect, unscanned, avg_vitality, top_vitality, low_vitality, dead_vitality,
     total_cves, pending_keywords, new_repos_24h) = database.get_frontend_stats()
    last_scan_str = last_scan.isoformat() if last_scan else None
    return {
        "total_repos": total_repos,
        "total_stars": int(total_stars),
        "languages": languages,
        "lang_distribution": lang_dist,
        "last_scan": last_scan_str,
        "status": _engine.scanner_status,
        "security_critique": critique,
        "security_suspect": suspect,
        "security_unscanned": unscanned,
        "avg_vitality": round(float(avg_vitality), 1),
        "top_vitality": top_vitality,
        "low_vitality": low_vitality,
        "dead_vitality": dead_vitality,
        "total_cves": total_cves,
        "pending_keywords": pending_keywords,
        "new_repos_24h": new_repos_24h,
    }


@app.get("/api/search")
def search_api(
    q: str = "",
    page: int = 1,
    per_page: int = 20,
    types: str = "",
    language: str = "",
    severity: str = "",
    security_verdict: str = "",
    category: str = "",
    sort: str = "relevance",
):
    """Recherche unifiee intelligente avec filtres avances, facettes et pagination."""
    type_list = [t.strip() for t in types.split(",") if t.strip()] or None
    return database.unified_search(
        q,
        limit=per_page,
        page=page,
        types=type_list,
        language=language or None,
        severity=severity or None,
        security_verdict=security_verdict or None,
        category=category or None,
        sort=sort,
    )


@app.get("/api/repos")
def get_repos_api(q: str = "", page: int = 1, per_page: int = 50, sort_by: str = "stars", vitality_min: int = 0, security_verdict: str = None):
    """Renvoie les dépôts paginés au format attendu par le frontend React."""
    repos, total = database.search_repos_frontend(q, page, per_page, sort_by, vitality_min, security_verdict)
    pages = max(1, (total + per_page - 1) // per_page)
    return {"total": total, "page": page, "per_page": per_page, "pages": pages, "repos": repos}


@app.get("/api/repositories")
def get_repositories_api():
    """Renvoie la liste des dépôts (format brut)."""
    return database.get_repositories()


@app.get("/api/books")
def get_books_api(q: str = None):
    """
    Renvoie la liste des livres extraits.
    Si le paramètre q est fourni, effectue une recherche sémantique intelligente.
    """
    return database.get_books(q)


@app.get("/api/keywords")
def get_keywords_api(status: str = "pending", limit: int = 100, min_score: float = 0.0):
    """Liste les mots-clés découverts par le miner."""
    return {"keywords": database.get_keywords(status, limit, min_score)}


@app.post("/api/keywords/{term}/approve")
def approve_keyword_api(term: str, category: str = None, _u: str = Depends(src.auth.verify_admin)):
    ok = database.approve_keyword(term, "approved", category)
    if ok:
        from nlp_processor import refresh_cyber_terms
        refresh_cyber_terms()
    return {"success": ok, "term": term}


@app.post("/api/keywords/{term}/reject")
def reject_keyword_api(term: str, _u: str = Depends(src.auth.verify_admin)):
    ok = database.approve_keyword(term, "rejected")
    return {"success": ok, "term": term}


@app.get("/api/search/ai")
def smart_search_api(q: str = "", limit: int = 20):
    """Recherche hybride avec re-rank IA (Groq)."""
    if not q or len(q) < 2:
        return {"query": q, "total": 0, "results": []}
    import src.semantic_ranker as ranker
    return ranker.smart_search(q, limit=limit, use_ai_rank=True)


@app.get("/api/search/semantic")
def semantic_search_api(q: str = "", limit: int = 20):
    """Recherche semantique par similarite cosine (embeddings)."""
    if not q or len(q) < 2:
        return {"results": [], "query": q}
    import src.embeddings as embeddings
    results = embeddings.semantic_search(q, limit=limit)
    return {"query": q, "total": len(results), "results": results}


@app.post("/api/embeddings/build")
def build_embeddings_api(limit: int = 200, _u: str = Depends(src.auth.verify_admin)):
    """Genere les embeddings pour les repos sans."""
    import src.embeddings as embeddings
    n = embeddings.embed_unembedded_repos(limit=limit)
    return {"generated": n, "status": embeddings.embedding_status()}


@app.get("/api/embeddings/status")
def embeddings_status_api():
    """Etat de l'indexation des embeddings semantiques."""
    import src.embeddings as embeddings
    return embeddings.embedding_status()


@app.post("/api/ai-verdict")
def run_ai_verdict(limit: int = 30, _u: str = Depends(src.auth.verify_admin)):
    """Lance l'audit IA sur les repos sans verdict de securite."""
    import src.ai_verdict as ai_verdict
    n = ai_verdict.batch_analyze_unverified(limit=limit)
    return {"audited": n, "message": f"{n} depot(s) audite(s) par l'IA"}


@app.get("/api/trending")
def trending_api(days: int = 7, limit: int = 20):
    """Outils tendance des N derniers jours."""
    import src.database as db
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT full_name, description, stars, language, html_url, security_verdict
           FROM repositories
           WHERE discovered_at >= NOW() - %s::INTERVAL
           ORDER BY stars DESC NULLS LAST LIMIT %s""",
        (f"{days} days", limit),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"days": days, "count": len(rows), "tools": [
        {"name": r[0], "desc": r[1], "stars": r[2], "lang": r[3], "url": r[4], "verdict": r[5]}
        for r in rows
    ]}


@app.get("/api/v1/repos")
def public_api(q: str = "", page: int = 1, per_page: int = 20, sort: str = "stars"):
    """API publique REST pour les outils."""
    import src.database as db
    repos, total = db.search_repos_frontend(q, page, per_page, sort)
    return {"api_version": "v1", "total": total, "page": page, "per_page": per_page, "results": repos}


@app.get("/api/tool/{name:path}")
def tool_detail_api(name: str):
    """Fiche detaillee d'un outil avec score de confiance et similaires."""
    import src.database as db
    from psycopg2.extras import RealDictCursor
    conn = db.get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Fetch tool
    cursor.execute(
        """SELECT full_name, description, stars, language, html_url, security_verdict,
                  security_details, vitality_score, updated_at, discovered_at
           FROM repositories WHERE full_name = %s""",
        (name,),
    )
    tool = cursor.fetchone()
    if not tool:
        cursor.close()
        conn.close()
        return {"error": "Outil introuvable", "name": name}

    tool = dict(tool)

    # Trust score (0-100) — multi-facteurs
    stars_norm = min((tool.get("stars") or 0) / 5000, 1.0)
    vitality = (tool.get("vitality_score") or 0) / 100
    verdict_bonus = {"Sain": 0.3, None: 0, "Suspect": -0.2, "Critique": -0.5}.get(tool.get("security_verdict"), 0)
    trust = round(max(0, min(100, (stars_norm * 40 + vitality * 30 + (verdict_bonus + 0.5) * 30) * 100 / 100)))
    tool["trust_score"] = trust
    tool["trust_breakdown"] = {
        "stars": round(stars_norm * 40, 1),
        "vitality": round(vitality * 30, 1),
        "verdict": round((verdict_bonus + 0.5) * 30, 1),
    }

    # Similar tools (via semantic search on description)
    try:
        import src.embeddings as emb
        similar = emb.semantic_search(tool.get("description") or name, limit=6, min_score=0.1)
        tool["similar"] = [s for s in similar if s.get("name") != name][:5]
    except Exception:
        tool["similar"] = []

    cursor.close()
    conn.close()
    return tool


@app.get("/api/digest")
def get_digest_api():
    """Retourne le dernier digest IA du jour."""
    import src.ai_digest as ai_digest
    return ai_digest.get_latest_digest()


@app.post("/api/digest")
def generate_digest_api(_u: str = Depends(src.auth.verify_admin)):
    """Genere un nouveau digest IA (admin)."""
    import src.ai_digest as ai_digest
    return ai_digest.generate_digest()


@app.get("/api/tools/featured")
def featured_tools_api(limit: int = 12):
    """Outils incontournables: top stars + bon verdict securite."""
    from src.database import get_db_connection
    from psycopg2.extras import RealDictCursor
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT full_name AS name, description AS desc, stars, language AS lang,
               html_url AS url, security_verdict, vitality_score
        FROM repositories WHERE stars > 100 ORDER BY stars DESC LIMIT %s
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"tools": rows, "label": "Incontournables"}


@app.get("/api/tools/readytouse")
def ready_to_use_api(limit: int = 20):
    """Outils prets a l'emploi: bien notes + descriptions riches."""
    from src.database import get_db_connection
    from psycopg2.extras import RealDictCursor
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT full_name AS name, description AS desc, stars, language AS lang,
               html_url AS url, security_verdict, vitality_score
        FROM repositories WHERE stars >= 10 AND description IS NOT NULL AND length(description) > 30
        ORDER BY stars DESC LIMIT %s
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"tools": rows, "label": "Prets a l'emploi"}


@app.get("/api/tools/by-category")
def tools_by_category_api(category: str = "all", limit: int = 30):
    """Outils par categorie."""
    from src.database import get_db_connection
    from psycopg2.extras import RealDictCursor
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    filters = {
        "red-team": "description ILIKE '%red team%' OR description ILIKE '%C2%' OR description ILIKE '%exploit%' OR description ILIKE '%payload%' OR description ILIKE '%backdoor%' OR description ILIKE '%adversary%'",
        "blue-team": "description ILIKE '%defense%' OR description ILIKE '%detect%' OR description ILIKE '%monitor%' OR description ILIKE '%scan%' OR description ILIKE '%forensic%' OR description ILIKE '%incident%'",
        "exploit": "description ILIKE '%exploit%' OR description ILIKE '%PoC%' OR description ILIKE '%CVE%' OR description ILIKE '%vulnerability%'",
        "malware": "description ILIKE '%malware%' OR description ILIKE '%ransomware%' OR description ILIKE '%trojan%' OR description ILIKE '%stealer%' OR description ILIKE '%backdoor%'",
        "osint": "description ILIKE '%osint%' OR description ILIKE '%recon%' OR description ILIKE '%scraper%' OR description ILIKE '%crawler%' OR description ILIKE '%intelligence%'",
        "network": "description ILIKE '%network%' OR description ILIKE '%scanner%' OR description ILIKE '%proxy%' OR description ILIKE '%sniff%' OR description ILIKE '%packet%'",
    }
    where = f"WHERE {filters[category]}" if category in filters else ""
    cursor.execute(f"""
        SELECT full_name AS name, description AS desc, stars, language AS lang,
               html_url AS url, security_verdict, vitality_score
        FROM repositories {where} ORDER BY stars DESC LIMIT %s
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"tools": rows, "category": category}


@app.post("/api/agents/github/categorize")
def github_categorize_api(limit: int = 15, _u: str = Depends(src.auth.verify_admin)):
    """Categorise les repos sans categorie IA (admin)."""
    import src.agents.github_agent as gh
    n = gh.batch_categorize(limit=limit)
    return {"categorized": n}


@app.get("/api/trends")
def trends_api():
    """Tendances emergentes detectees par l'agent IA."""
    import src.agents.trend_agent as trend
    return trend.detect_trends()


@app.post("/api/blog/scan")
def blog_scan_api(_u: str = Depends(src.auth.verify_admin)):
    """Lance le scan des blogs securite (admin). Retourne les articles avec entites extraites."""
    import src.blog_scanner as blog
    n = blog.scan_all()
    posts = blog.get_posts(limit=10)
    # Extraire les entites des derniers articles
    enriched = []
    for p in posts[:5]:
        p["entities"] = blog.extract_entities(p.get("title","") + " " + p.get("summary",""))
        enriched.append(p)
    return {"saved": n, "sample": enriched}


@app.get("/api/blog/posts")
def blog_posts_api(limit: int = 20, source: str = None):
    """Derniers articles de blogs securite."""
    import src.blog_scanner as blog
    return blog.get_posts(limit=limit, source=source)


@app.get("/api/blog/sources")
def blog_sources_api():
    """Sources de blogs disponibles."""
    import src.blog_scanner as blog
    return blog.get_sources()


@app.post("/api/social/reddit")
def reddit_scan_api(limit: int = 10, _u: str = Depends(src.auth.verify_admin)):
    """Scan Reddit pour nouveaux outils (admin)."""
    import src.social.reddit_scanner as reddit
    n = reddit.run(limit_per_sub=limit)
    return {"discovered": n}


@app.post("/api/hf/guard")
def hf_guard_api(limit: int = 20, _u: str = Depends(src.auth.verify_admin)):
    """Content safety scan via Granite Guardian (admin)."""
    import src.hf_client as hf
    n = hf.batch_scan_suspect_repos(limit=limit)
    return {"flagged": n}


@app.post("/api/osint/pro/email")
def osint_email_api(email: str = ""):
    """Email OSINT: breaches + pastebin."""
    import src.osint_pro as pro
    return {
        "breaches": pro.check_email_breaches(email),
        "pastebin": pro.search_pastebin(email),
    }


@app.post("/api/osint/pro/phone")
def osint_phone_api(phone: str = ""):
    """Phone OSINT: analyse numero."""
    import src.osint_pro as pro
    return pro.analyze_phone(phone)


@app.post("/api/osint/pro/domain")
def osint_domain_api(domain: str = ""):
    """Domain OSINT: WHOIS/RDAP."""
    import src.osint_pro as pro
    return pro.lookup_domain(domain)


@app.post("/api/osint/pro/report")
def osint_report_api(free_text: str = "", email: str = "", phone: str = "", domain: str = ""):
    """Rapport OSINT professionnel complet (toutes les sources)."""
    import src.osint_pro as pro
    import src.osint_lab as lab
    import src.github_client as gc

    findings = {}

    # Pipeline standard
    if free_text:
        extracted = lab.ai_extract_person(free_text)
        name = extracted.get("name", "")
        location = extracted.get("location", "")
        username = (extracted.get("probable_usernames") or [""])[0]
        findings["github_profiles"] = lab.search_github_user(name, location, gc.TOKENS) if name else []
        findings["social_presence"] = lab.check_social_presence(username) if username else []
    else:
        extracted = {"name": "", "location": ""}

    # Email OSINT
    if email:
        findings["email_breaches"] = pro.check_email_breaches(email)
        findings["email_pastebin"] = pro.search_pastebin(email)

    # Phone OSINT
    if phone:
        findings["phone_analysis"] = pro.analyze_phone(phone)

    # Domain OSINT
    if domain:
        findings["domain_info"] = pro.lookup_domain(domain)

    return pro.generate_report(
        target={"free_text": free_text, "email": email, "phone": phone, "domain": domain,
                "extracted": extracted},
        findings=findings,
    )


@app.post("/api/osint/investigate-v2")
def osint_investigate_v2(free_text: str = ""):
    """Enquete OSINT 2.0: multi-candidats, scoring, decision engine."""
    import src.osint_engine as engine
    import src.github_client as gc
    result = engine.run_investigation(free_text, tokens=gc.TOKENS if gc.TOKENS else [])
    # Ajouter la comparaison visuelle
    result["comparison"] = engine.compare_candidates(result.get("candidates", []))
    return result


@app.post("/api/slicer/scan")
def slicer_scan_api(queries: int = 10, _u: str = Depends(src.auth.verify_admin)):
    """GitHub Slicer: decouverte massive par tranches (admin)."""
    import src.github_slicer as slicer
    import src.github_client as gc
    return slicer.run_slicing_scan(gc.TOKENS, max_queries=queries)


@app.post("/api/osint/dorks")
def osint_dorks_api(name: str = "", location: str = "", extract: bool = False):
    """Multi-engine dorking OSINT (DuckDuckGo, Bing, SearX)."""
    import src.dorking_engine as dk
    report = dk.run_osint_dorks(name, location)
    if extract and report.get("top_findings"):
        all_urls = []
        for cat in report["top_findings"].values():
            all_urls.extend([u["url"] for u in cat])
        report["extracted_info"] = dk.extract_info_from_urls(all_urls)
    return report


@app.get("/api/osint/tools")
def osint_tools_status():
    """Etat des outils OSINT disponibles."""
    import src.osint_tools as ot
    return ot.tools_status()


@app.post("/api/osint/run-all")
def osint_run_all(username: str = "", email: str = "", name: str = "", location: str = ""):
    """Lance tous les outils OSINT (Sherlock, Maigret, Holehe + internes)."""
    import src.osint_tools as ot
    return ot.run_all(username=username, email=email, name=name, location=location)


@app.post("/api/osint/plan")
def osint_plan_api(free_text: str = ""):
    """L'IA analyse la cible et recommande les meilleurs outils OSINT."""
    import src.osint_orchestrator as orch
    return orch.analyze_and_recommend(free_text)


@app.post("/api/osint/pipeline")
def osint_pipeline_api(free_text: str = ""):
    """Pipeline OSINT complet: 12 modeles IA chaines."""
    import src.osint_pipeline as pipeline
    import src.github_client as gc
    return pipeline.run_full_pipeline(free_text, tokens=gc.TOKENS if gc.TOKENS else [])


@app.post("/api/osint/investigate")
def osint_investigate_api(name: str = "", location: str = "", email: str = "", username: str = "", free_text: str = ""):
    """Enquete OSINT sur une personne. Accepte du texte libre analyse par IA."""
    import src.osint_lab as osint_lab
    import src.github_client as gc
    return osint_lab.investigate_person(
        name=name, location=location, email=email, username=username,
        free_text=free_text, tokens=gc.TOKENS if gc.TOKENS else [],
    )


@app.get("/api/hf/qa")
def hf_qa_api(question: str = "", context: str = ""):
    """Question Answering via HF (roberta-squad2)."""
    import src.hf_client as hf
    answer = hf.answer_question(question, context)
    return {"question": question, "answer": answer}


@app.get("/api/hf/vuln-type")
def hf_vuln_type_api(text: str = ""):
    """Detection de type de vulnerabilite via SecBERT."""
    import src.hf_client as hf
    return {"type": hf.detect_vuln_type(text)}


@app.get("/api/hf/status")
def hf_status():
    """Etat des services HuggingFace."""
    import src.hf_client as hf
    return hf.hf_status()


@app.get("/api/hf/embed")
def hf_embed_api(text: str = ""):
    """Genere un embedding via HF."""
    import src.hf_client as hf
    emb = hf.embed_text(text)
    return {"dims": len(emb), "embedding": emb[:10]}


@app.get("/api/hf/classify")
def hf_classify_api(text: str = ""):
    """Zero-shot classification via HF."""
    import src.hf_client as hf
    return hf.classify_zero_shot(text, ["Red Team", "Blue Team", "Malware", "Exploit", "OSINT", "Cloud", "Forensics"])


@app.get("/api/threats/top")
def top_threats_api(limit: int = 20):
    """Top menaces classees par Threat Priority Score."""
    import src.correlation as corr
    threats = corr.get_top_threats(limit=limit)
    return {"count": len(threats), "threats": threats}


@app.get("/api/cve/{cve_id}/analysis")
def cve_analysis_api(cve_id: str):
    """Analyse IA d'une CVE (Groq)."""
    from src.database import get_db_connection
    import src.correlation as corr
    import src.agents.cve_agent as cve_agent

    cached = cve_agent.get_analyzed_cve(cve_id)
    if cached:
        return cached

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT description, severity, cvss_score, weaknesses FROM cve_entries WHERE cve_id = %s", (cve_id.upper(),))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return {"error": "CVE introuvable"}

    desc, sev, cvss, weaknesses = row
    kev = "CISA_KEV" in (weaknesses or "")
    exploits = corr.get_exploits_for_cve(cve_id)
    return cve_agent.analyze_cve(cve_id, desc, str(cvss or ""), sev, kev, len(exploits))


@app.post("/api/cve/{cve_id}/analyze")
def cve_analyze_api(cve_id: str, _u: str = Depends(src.auth.verify_admin)):
    """Force l'analyse IA d'une CVE (admin)."""
    from src.database import get_db_connection
    import src.correlation as corr
    import src.agents.cve_agent as cve_agent

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT description, severity, cvss_score, weaknesses FROM cve_entries WHERE cve_id = %s", (cve_id.upper(),))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return {"error": "CVE introuvable"}

    desc, sev, cvss, weaknesses = row
    kev = "CISA_KEV" in (weaknesses or "")
    exploits = corr.get_exploits_for_cve(cve_id)
    result = cve_agent.analyze_cve(cve_id, desc, str(cvss or ""), sev, kev, len(exploits))

    # Stocker en DB
    if "indisponible" not in result.get("summary", ""):
        conn = get_db_connection()
        cursor = conn.cursor()
        import json as _json
        cursor.execute(
            "UPDATE cve_entries SET weaknesses = COALESCE(weaknesses, '') || ' | AI_ANALYSIS:' || %s WHERE cve_id = %s",
            (_json.dumps(result)[:1500], cve_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
        cve_agent._cve_cache[cve_id] = result
    return result


@app.get("/api/cve/{cve_id}")
def cve_detail_api(cve_id: str):
    """Detail complet d'une CVE avec exploits et outils associes."""
    import src.correlation as corr
    return corr.get_cve_detail(cve_id)


@app.get("/api/cve/{cve_id}/exploits")
def cve_exploits_api(cve_id: str):
    import src.correlation as corr
    return {"cve_id": cve_id, "exploits": corr.get_exploits_for_cve(cve_id)}


@app.get("/api/cve/{cve_id}/tools")
def cve_tools_api(cve_id: str):
    import src.correlation as corr
    return {"cve_id": cve_id, "tools": corr.get_tools_for_cve(cve_id)}


@app.post("/api/ioc/enrich")
def ioc_enrich_api(_u: str = Depends(src.auth.verify_admin)):
    """Enrichissement IOC via abuse.ch APIs (admin)."""
    import src.ioc_enricher as ioc
    return ioc.run_ioc_enrichment()


@app.post("/api/dorking/scan")
def dorking_scan_api(limit: int = 8, _u: str = Depends(src.auth.verify_admin)):
    """Dorking GitHub Code Search pour nouveaux outils (admin)."""
    import src.dorking as dorking
    import src.github_client as gc
    n = dorking.run_dorking_scan(gc.TOKENS, limit=limit)
    return {"discovered": n}


@app.post("/api/dorking/exploitdb")
def exploitdb_import_api(_u: str = Depends(src.auth.verify_admin)):
    """Importe la base Exploit-DB comme mots-cles (admin)."""
    import src.dorking as dorking
    n = dorking.import_exploitdb()
    return {"keywords_imported": n}


@app.post("/api/osint/enrich")
def osint_enrich_api(_u: str = Depends(src.auth.verify_admin)):
    """Enrichissement OSINT: CISA KEV, GTFOBins, Awesome Lists (admin)."""
    import src.osint_enricher as osint
    return osint.run_osint_enrichment()


@app.get("/api/exploits/stats")
def exploits_stats_api():
    """Statistiques de la base d'exploits (public)."""
    import src.db.exploits as exploits_db
    return exploits_db.get_exploit_stats()


@app.post("/api/exploits/refresh")
def exploits_refresh_api(_u: str = Depends(src.auth.verify_admin)):
    """Telecharge et importe le CSV Exploit-DB dans la table `exploits` (admin)."""
    import src.exploit_loader as loader
    return loader.load_exploitdb()


@app.post("/api/ai-keywords")
def run_ai_keywords(limit: int = 25, _u: str = Depends(src.auth.verify_admin)):
    """Decouvre des mots-cles cyber emergents via l'IA (Groq)."""
    import src.ai_keywords as ai_keywords
    n = ai_keywords.batch_discover(limit=limit)
    return {"discovered": n, "message": f"{n} nouveau(x) mot(s)-cle(s) decouvert(s) par l'IA"}


@app.post("/api/enrich-ontology")
def enrich_ontology_api(background_tasks: BackgroundTasks, _u: str = Depends(src.auth.verify_admin)):
    """Télécharge MITRE ATT&CK / CAPEC / CWE et enrichit l'ontologie."""
    background_tasks.add_task(_run_ontology_enrichment)
    return {"message": "Enrichissement de l'ontologie lancé en arrière-plan"}


def _run_ontology_enrichment():
    count = ontology_enricher.import_ontology_to_db()
    logging.info(f"🧬 Enrichissement ontologique terminé : {count} termes")


@app.post("/api/enrich-keywords")
def enrich_keywords_api(background_tasks: BackgroundTasks, _u: str = Depends(src.auth.verify_admin)):
    """Extrait des mots-clés depuis CVEs, MITRE Mobile/ICS, OWASP, Exploit-DB."""
    background_tasks.add_task(_run_keyword_sources)
    return {"message": "Extraction de mots-clés lancée en arrière-plan"}


def _run_keyword_sources():
    stats = keyword_sources.import_external_sources_to_db()
    logging.info(f"🗄️ Keywords externes: {stats}")


@app.get("/api/download")
def download_excel(_u: str = Depends(src.auth.verify_admin)):
    """Téléchargement de l'export Excel."""
    export_to_excel()
    if os.path.exists(EXCEL_FILE):
        return FileResponse(
            EXCEL_FILE,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="cyber_security_catalogues.xlsx"
        )
    return {"error": "Fichier Excel non disponible."}


@app.get("/api/download/json")
def download_json(_u: str = Depends(src.auth.verify_admin)):
    """Téléchargement de l'export JSON."""
    export_to_json()
    if os.path.exists(JSON_FILE):
        return FileResponse(
            JSON_FILE,
            media_type="application/json",
            filename="cyber_security_catalogues.json"
        )
    return {"error": "Fichier JSON non disponible."}


@app.post("/api/scan")
def start_scan(background_tasks: BackgroundTasks, _u: str = Depends(src.auth.verify_admin)):
    """Déclenche un scan manuel en arrière-plan."""
    # scan_in_progress handled via _engine
    if _engine.scan_in_progress:
        return {"message": "Un scan est déjà en cours."}

    background_tasks.add_task(_engine.run_scan_once_manual)
    return {"message": "Le scan en arrière-plan a été démarré !"}


@app.post("/api/bulk-seed")
def start_bulk_seed(background_tasks: BackgroundTasks, max_pages_per_bucket: int = 10, _u: str = Depends(src.auth.verify_admin)):
    """Scan massif multi-topics pour monter en charge vers 1M de dépôts."""
    # bulk_in_progress via _engine
    if _engine.bulk_in_progress:
        return {"message": "Un bulk-seed est déjà en cours."}

    def _run():
        # bulk_in_progress via _engine, scanner_status
        _engine.bulk_in_progress = True
        _engine.scanner_status = "Bulk-seed en cours..."
        try:
            import src.bulk_seed as bulk_seed
            result = bulk_seed.bulk_seed(max_pages_per_bucket=max_pages_per_bucket)
            logging.info(f"🌱 Bulk-seed terminé: {result}")
        except Exception as e:
            logging.error(f"❌ Erreur bulk-seed: {e}")
        finally:
            _engine.bulk_in_progress = False
            _engine.scanner_status = "Prêt / En sommeil"

    background_tasks.add_task(_run)
    return {"message": "Bulk-seed lancé en arrière-plan.", "max_pages_per_bucket": max_pages_per_bucket}


@app.get("/api/bulk-status")
def bulk_status_api():
    """Retourne l'état d'avancement du dernier bulk-seed."""
    import src.bulk_seed as bulk_seed
    return bulk_seed.get_bulk_status()


@app.post("/api/harvest")
def start_harvest(background_tasks: BackgroundTasks, limit: int = 50, max_issues_pages: int = 3, max_commits_pages: int = 3, _u: str = Depends(src.auth.verify_admin)):
    """Récolte les issues/commits des repos pour exploser le volume de données."""
    # harvest_in_progress via _engine
    if _engine.harvest_in_progress:
        return {"message": "Une récolte d'artifacts est déjà en cours."}

    def _run():
        # harvest_in_progress via _engine, scanner_status
        _engine.harvest_in_progress = True
        _engine.scanner_status = "Récolte issues/commits en cours..."
        try:
            import src.harvest_artifacts as harvest_artifacts
            result = harvest_artifacts.harvest_batch(limit, max_issues_pages, max_commits_pages)
            logging.info(f"🌾 Harvest terminé: {result}")
        except Exception as e:
            logging.error(f"❌ Erreur harvest: {e}")
        finally:
            _engine.harvest_in_progress = False
            _engine.scanner_status = "Prêt / En sommeil"

    background_tasks.add_task(_run)
    return {"message": "Récolte d'artifacts lancée en arrière-plan.", "limit": limit}


@app.get("/api/data-points")
def data_points_api():
    """Retourne le nombre total de points de données (repos + issues + commits + ...)."""
    return database.count_total_data_points()


@app.get("/api/harvest-status")
def harvest_status_api():
    """Retourne l'état d'avancement de la récolte d'artifacts."""
    import src.harvest_artifacts as harvest_artifacts
    return harvest_artifacts.get_harvest_status()


@app.post("/api/import-cve")
def start_cve_import(background_tasks: BackgroundTasks, max_entries_per_year: int = 0):
    """Importe les feeds NVD/CVE (2002-2025) pour ~300k+ vulnérabilités."""
    global cve_in_progress
    if cve_in_progress:
        return {"message": "Un import CVE est déjà en cours."}

    def _run():
        global cve_in_progress, scanner_status
        cve_in_progress = True
        _engine.scanner_status = "Import CVE NVD en cours..."
        try:
            import src.cve_importer as cve_importer
            lim = max_entries_per_year if max_entries_per_year > 0 else None
            result = cve_importer.import_cve_all(max_entries_per_year=lim)
            logging.info(f"🛡️ Import CVE terminé: {result}")
        except Exception as e:
            logging.error(f"❌ Erreur import CVE: {e}")
        finally:
            cve_in_progress = False
            _engine.scanner_status = "Prêt / En sommeil"

    background_tasks.add_task(_run)
    return {"message": "Import CVE NVD lancé en arrière-plan."}


@app.get("/api/cves")
def get_cves_api(q: str = "", severity: str = "", page: int = 1, per_page: int = 20):
    return database.search_cves(q, severity, page, per_page)


@app.get("/api/cve-status")
def cve_status_api():
    """Retourne l'état d'avancement de l'import CVE."""
    import src.cve_importer as cve_importer
    return cve_importer.get_cve_status()


@app.get("/api/token-status")
def token_status_api():
    """Retourne le nombre de tokens configurés (sans exposer les valeurs)."""
    from src import github_client
    return {"token_count": github_client.token_count(), "has_tokens": github_client.token_count() > 0}


# ── STIX 2.1 & IOC Feed ──────────────────────────────────────────────

@app.get("/api/stix/cves")
def stix_cves_api(limit: int = 50, severity: str = ""):
    """Exporte les CVEs au format STIX 2.1."""
    import src.stix_exporter as stix
    data = stix.export_cves(limit=limit, severity=severity)
    return {"stix": data, "format": "STIX 2.1", "type": "vulnerabilities"}


@app.get("/api/stix/tools")
def stix_tools_api():
    """Exporte les outils au format STIX 2.1."""
    import src.stix_exporter as stix
    data = stix.export_tools()
    return {"stix": data, "format": "STIX 2.1", "type": "tools"}


@app.get("/api/stix/ioc-feed")
def stix_ioc_feed_api(limit: int = 100):
    """Génère un flux IOC au format STIX 2.1 (IPs, domaines, hashes)."""
    import src.stix_exporter as stix
    return stix.generate_ioc_feed(limit=limit)


@app.get("/api/stix/download")
def stix_download_api(what: str = "cves", limit: int = 100, severity: str = ""):
    """Téléchargement STIX 2.1 en fichier JSON."""
    import src.stix_exporter as stix
    if what == "cves":
        data = stix.export_cves(limit=limit, severity=severity)
        filename = f"cyberscan_cves_{datetime.utcnow().strftime('%Y%m%d')}.json"
    elif what == "tools":
        data = stix.export_tools()
        filename = f"cyberscan_tools_{datetime.utcnow().strftime('%Y%m%d')}.json"
    else:
        result = stix.generate_ioc_feed(limit=limit)
        data = result["stix"]
        filename = f"cyberscan_ioc_feed_{datetime.utcnow().strftime('%Y%m%d')}.json"
    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    tmp.write(data)
    tmp.close()
    return FileResponse(tmp.name, media_type="application/json", filename=filename)


# ── Massive Ingestion ─────────────────────────────────────────────────

@app.post("/api/ingest/run")
def ingest_run_api(background_tasks: BackgroundTasks, full: bool = False, _u: str = Depends(src.auth.verify_admin)):
    """Lance le pipeline d'ingestion massive (abuse.ch + OTX + EPSS + OpenCVE)."""
    import src.massive_ingestion as mi
    background_tasks.add_task(mi.run_massive_ingestion, full=full)
    return {"message": "Pipeline d'ingestion massive lance", "full": full}


@app.get("/api/ingest/stats")
def ingest_stats_api():
    """Statistiques de volumetrie IOC."""
    import src.massive_ingestion as mi
    return mi.get_ioc_stats()


@app.post("/api/ingest/urlhaus")
def ingest_urlhaus_api(limit: int = 5000, _u: str = Depends(src.auth.verify_admin)):
    import src.massive_ingestion as mi
    n = mi.ingest_urlhaus(limit)
    return {"source": "urlhaus", "saved": n}


@app.post("/api/ingest/malwarebazaar")
def ingest_malwarebazaar_api(limit: int = 2000, _u: str = Depends(src.auth.verify_admin)):
    import src.massive_ingestion as mi
    n = mi.ingest_malwarebazaar(limit)
    return {"source": "malwarebazaar", "saved": n}


@app.post("/api/ingest/threatfox")
def ingest_threatfox_api(limit: int = 5000, _u: str = Depends(src.auth.verify_admin)):
    import src.massive_ingestion as mi
    n = mi.ingest_threatfox(limit)
    return {"source": "threatfox", "saved": n}


@app.post("/api/ingest/feodotracker")
def ingest_feodo_api(_u: str = Depends(src.auth.verify_admin)):
    import src.massive_ingestion as mi
    n = mi.ingest_feodotracker()
    return {"source": "feodotracker", "saved": n}


@app.post("/api/ingest/otx")
def ingest_otx_api(limit: int = 500, _u: str = Depends(src.auth.verify_admin)):
    import src.massive_ingestion as mi
    n = mi.ingest_otx_pulses(limit)
    return {"source": "otx", "saved": n}


@app.post("/api/ingest/opencve")
def ingest_opencve_api(limit: int = 1000, _u: str = Depends(src.auth.verify_admin)):
    import src.massive_ingestion as mi
    n = mi.ingest_opencve(limit)
    return {"source": "opencve", "saved": n}


@app.post("/api/ingest/epss")
def ingest_epss_api(_u: str = Depends(src.auth.verify_admin)):
    import src.massive_ingestion as mi
    n = mi.ingest_epss()
    return {"source": "epss", "saved": n, "message": "Scores EPSS mis a jour sur les CVEs existantes"}


# ── AI Keyword Validator ────────────────────────────────────────────────

@app.post("/api/keywords/ai-validate")
def ai_validate_keywords_api(limit: int = 200, threshold: float = 0.6,
                              _u: str = Depends(src.auth.verify_admin)):
    """Valide automatiquement les mots-cles en attente via HF zero-shot."""
    import src.ai_keyword_validator as kv
    return kv.batch_validate_keywords(limit=limit, auto_approve_threshold=threshold)


@app.get("/api/keywords/stats")
def keyword_stats_api():
    """Statistiques de validation des mots-cles."""
    import src.ai_keyword_validator as kv
    return kv.get_keyword_stats()


# ── Premium Threat Intel (VirusTotal, SecurityTrails, Shodan) ─────────────

@app.get("/api/intel/virustotal")
def intel_vt_api(identifier: str = "", resource_type: str = "auto"):
    """Query VirusTotal API for an IP, domain, URL, or hash."""
    import src.premium_intel as pi
    if not identifier:
        return {"error": "identifier parameter required"}
    return pi.virustotal_lookup(identifier, resource_type)


@app.get("/api/intel/securitytrails")
def intel_st_api(domain: str = "", ip: str = ""):
    """Query SecurityTrails API for a domain (passive DNS, subdomains, WHOIS) or IP."""
    import src.premium_intel as pi
    if domain:
        return pi.securitytrails_domain(domain)
    if ip:
        return pi.securitytrails_ip(ip)
    return {"error": "domain or ip parameter required"}


@app.get("/api/intel/shodan")
def intel_shodan_api(ip: str = "", query: str = ""):
    """Query Shodan API for an IP host or search query."""
    import src.premium_intel as pi
    if ip:
        return pi.shodan_host(ip)
    if query:
        return pi.shodan_search(query)
    return {"error": "ip or query parameter required"}


@app.post("/api/intel/enrich-all")
def intel_enrich_api(limit: int = 20, _u: str = Depends(src.auth.verify_admin)):
    """Enrich existing IOCs via VirusTotal + SecurityTrails + Shodan."""
    import src.premium_intel as pi
    return pi.enrich_all(limit)


@app.get("/api/intel/status")
def intel_status_api():
    """Check which premium APIs are configured."""
    import os
    return {
        "virustotal": bool(os.getenv("VIRUSTOTAL_API_KEY")),
        "securitytrails": bool(os.getenv("SECURITYTRAILS_API_KEY")),
        "shodan": bool(os.getenv("SHODAN_API_KEY")),
    }


# ── Free Sources Pipeline ──────────────────────────────────────────────

@app.post("/api/sources/run")
def free_sources_run_api(_u: str = Depends(src.auth.verify_admin)):
    """Run all free source ingestion (SSLBL, GHSA, OSV, SigmaHQ, YARAify, Ransomware.live, D3FEND, Package Advisories)."""
    import src.free_connectors as fc
    return fc.run_free_sources()


@app.post("/api/sources/sslbl")
def sslbl_ingest_api(_u: str = Depends(src.auth.verify_admin)):
    import src.free_connectors as fc
    return {"source": "sslbl", "saved": fc.ingest_sslbl()}


@app.post("/api/sources/ghsa")
def ghsa_ingest_api(limit: int = 100, _u: str = Depends(src.auth.verify_admin)):
    import src.free_connectors as fc
    return {"source": "ghsa", "saved": fc.ingest_ghsa(limit)}


@app.post("/api/sources/osv")
def osv_ingest_api(limit: int = 200, _u: str = Depends(src.auth.verify_admin)):
    import src.free_connectors as fc
    return {"source": "osv", "saved": fc.ingest_osv(limit)}


@app.post("/api/sources/sigmahq")
def sigmahq_ingest_api(_u: str = Depends(src.auth.verify_admin)):
    import src.free_connectors as fc
    return {"source": "sigmahq", "saved": fc.ingest_sigmahq()}


@app.post("/api/sources/yaraify")
def yaraify_ingest_api(_u: str = Depends(src.auth.verify_admin)):
    import src.free_connectors as fc
    return {"source": "yaraify", "saved": fc.ingest_yaraify()}


@app.post("/api/sources/ransomware")
def ransomware_ingest_api(_u: str = Depends(src.auth.verify_admin)):
    import src.free_connectors as fc
    return {"source": "ransomware_live", "saved": fc.ingest_ransomware_live()}


@app.post("/api/sources/d3fend")
def d3fend_ingest_api(_u: str = Depends(src.auth.verify_admin)):
    import src.free_connectors as fc
    return {"source": "d3fend", "saved": fc.ingest_d3fend()}


@app.post("/api/sources/packages")
def packages_ingest_api(_u: str = Depends(src.auth.verify_admin)):
    import src.free_connectors as fc
    return {"source": "packages", "saved": fc.ingest_package_advisories()}
