"""FastAPI routes for Cyber Scanner Pro."""
import logging
import json
import os
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
        cursor.close(); conn.close()
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

    cursor.close(); conn.close()
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
    cursor.close(); conn.close()
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
    cursor.close(); conn.close()
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
    cursor.close(); conn.close()
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
    import ontology_enricher
    count = ontology_enricher.import_ontology_to_db()
    logging.info(f"🧬 Enrichissement ontologique terminé : {count} termes")


@app.post("/api/enrich-keywords")
def enrich_keywords_api(background_tasks: BackgroundTasks, _u: str = Depends(src.auth.verify_admin)):
    """Extrait des mots-clés depuis CVEs, MITRE Mobile/ICS, OWASP, Exploit-DB."""
    background_tasks.add_task(_run_keyword_sources)
    return {"message": "Extraction de mots-clés lancée en arrière-plan"}


def _run_keyword_sources():
    import keyword_sources
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
