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
def approve_keyword_api(term: str, category: str = None):
    ok = database.approve_keyword(term, "approved", category)
    if ok:
        from nlp_processor import refresh_cyber_terms
        refresh_cyber_terms()
    return {"success": ok, "term": term}


@app.post("/api/keywords/{term}/reject")
def reject_keyword_api(term: str):
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
def build_embeddings_api(limit: int = 200):
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
def run_ai_verdict(limit: int = 30):
    """Lance l'audit IA sur les repos sans verdict de securite."""
    import src.ai_verdict as ai_verdict
    n = ai_verdict.batch_analyze_unverified(limit=limit)
    return {"audited": n, "message": f"{n} depot(s) audite(s) par l'IA"}


@app.post("/api/ai-keywords")
def run_ai_keywords(limit: int = 25):
    """Decouvre des mots-cles cyber emergents via l'IA (Groq)."""
    import src.ai_keywords as ai_keywords
    n = ai_keywords.batch_discover(limit=limit)
    return {"discovered": n, "message": f"{n} nouveau(x) mot(s)-cle(s) decouvert(s) par l'IA"}


@app.post("/api/enrich-ontology")
def enrich_ontology_api(background_tasks: BackgroundTasks):
    """Télécharge MITRE ATT&CK / CAPEC / CWE et enrichit l'ontologie."""
    background_tasks.add_task(_run_ontology_enrichment)
    return {"message": "Enrichissement de l'ontologie lancé en arrière-plan"}


def _run_ontology_enrichment():
    import ontology_enricher
    count = ontology_enricher.import_ontology_to_db()
    logging.info(f"🧬 Enrichissement ontologique terminé : {count} termes")


@app.post("/api/enrich-keywords")
def enrich_keywords_api(background_tasks: BackgroundTasks):
    """Extrait des mots-clés depuis CVEs, MITRE Mobile/ICS, OWASP, Exploit-DB."""
    background_tasks.add_task(_run_keyword_sources)
    return {"message": "Extraction de mots-clés lancée en arrière-plan"}


def _run_keyword_sources():
    import keyword_sources
    stats = keyword_sources.import_external_sources_to_db()
    logging.info(f"🗄️ Keywords externes: {stats}")


@app.get("/api/download")
def download_excel():
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
def download_json():
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
def start_scan(background_tasks: BackgroundTasks):
    """Déclenche un scan manuel en arrière-plan."""
    # scan_in_progress handled via _engine
    if _engine.scan_in_progress:
        return {"message": "Un scan est déjà en cours."}

    background_tasks.add_task(_engine.run_scan_once_manual)
    return {"message": "Le scan en arrière-plan a été démarré !"}


@app.post("/api/bulk-seed")
def start_bulk_seed(background_tasks: BackgroundTasks, max_pages_per_bucket: int = 10):
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
def start_harvest(background_tasks: BackgroundTasks, limit: int = 50, max_issues_pages: int = 3, max_commits_pages: int = 3):
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
