"""FastAPI routes for Cyber Scanner Pro."""
import logging
import json
import os
from datetime import datetime
from fastapi import BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from src.config import app, FRONTEND_DIR, DOMAIN, EXCEL_FILE, JSON_FILE
from src import database
import src.auth
from fastapi import Depends
import src.nlp_processor as nlp_processor
import src.scan_engine as _engine

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


@app.get("/api/tools/featured")
def featured_tools_api(limit: int = 12):
    """Outils incontournables: score de qualite eleve (top vitalite)."""
    from src.database import get_db_connection
    from psycopg2.extras import RealDictCursor
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT full_name AS name, description AS desc, stars, language AS lang,
               html_url AS url, security_verdict, vitality_score, semantic_category AS category
        FROM repositories WHERE stars > 100 AND COALESCE(security_verdict, 'Sain') <> 'Critique'
        ORDER BY vitality_score DESC, stars DESC LIMIT %s
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"tools": rows, "label": "Incontournables"}


@app.get("/api/tools/best")
def tools_best_api(category: str = "all", limit: int = 24):
    """Curateur 'outils pro': top score qualite, filtre par categorie semantique."""
    from src.database import get_best_tools
    tools = get_best_tools(category=category, limit=limit)
    return {"tools": tools, "label": "Outils pro", "category": category}


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


@app.post("/api/hf/guard")
def hf_guard_api(limit: int = 20, _u: str = Depends(src.auth.verify_admin)):
    """Content safety scan via Granite Guardian (admin)."""
    import src.hf_client as hf
    n = hf.batch_scan_suspect_repos(limit=limit)
    return {"flagged": n}


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


@app.get("/api/priority/cves")
def priority_cves_api(days: int = 90, limit: int = 20, profile_id: int | None = None):
    """Decision Engine : 'Que dois-je faire aujourd'hui ?' — CVE priorisees et justifiees.
    
    Si profile_id fourni, contexte personnel (organisation, assets, role).
    Sinon, contexte global (tous les repos)."""
    import src.priority_engine as pe
    decisions = pe.get_priority_decisions(days=days, limit=limit, profile_id=profile_id)
    summary = pe.get_decision_summary(days=days)
    import src.context_engine as ctx
    role = ctx.get_user_role(profile_id)
    summary["role"] = role
    return {"count": len(decisions), "decisions": decisions, "summary": summary}


@app.get("/api/profile")
def get_profile_api(profile_id: int = 0):
    """Profil utilisateur courant."""
    import src.context_engine as ctx
    profile = ctx.ensure_profile(profile_id=profile_id)
    return profile


@app.post("/api/profile/onboard")
def onboard_profile_api(profile_id: int, role: str, assets: str = "[]", org_name: str = "", sector: str = "", compliance: str = ""):
    """Onboarding: configure le role, les assets et l'organisation."""
    import json as _j
    import src.context_engine as ctx
    asset_list = _j.loads(assets) if assets else []
    result = ctx.init_profile(profile_id, role, asset_list, org_name, sector, compliance)
    return result


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


@app.post("/api/tools/backfill-readmes")
def backfill_readmes_api(background_tasks: BackgroundTasks, limit: int = 100, _u: str = Depends(src.auth.verify_admin)):
    """Recupere les README manquants (tri stars DESC) et les stocke en chunks RAG (admin)."""
    background_tasks.add_task(_run_readme_backfill, limit)
    return {"message": f"Backfill README lancé en arrière-plan ({limit} dépôts)"}


def _run_readme_backfill(limit: int):
    import src.collectors as collectors
    n = collectors.backfill_readmes(limit=limit)
    logging.info(f"📖 Backfill README terminé : {n} dépôt(s)")


@app.post("/api/tools/recompute-vitality")
def recompute_vitality_api(background_tasks: BackgroundTasks, _u: str = Depends(src.auth.verify_admin)):
    """Recalcule le score de qualite (vitality_score) de tous les depots (admin)."""
    background_tasks.add_task(_run_vitality_recompute)
    return {"message": "Recalcul des scores de qualité lancé en arrière-plan"}


def _run_vitality_recompute():
    n = database.recalculate_vitality_scores()
    logging.info(f"⚡ Recalcul qualite : {n} dépôts mis à jour")


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


@app.get("/api/data-points")
def data_points_api():
    """Retourne le nombre total de points de données (repos + issues + commits + ...)."""
    return database.count_total_data_points()


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


@app.post("/api/cves/backfill-severity")
def backfill_cve_severity_api(background_tasks: BackgroundTasks):
    """Backfill NVD des champs severity/cvss_score manquants (en arrière-plan)."""
    import src.cve_importer as cve_importer

    pending = cve_importer.get_missing_severity_count()
    if pending == 0:
        return {"message": "Aucune CVE sans sévérité.", "pending": 0}
    if pending < 0:
        return {"message": "Erreur lors du comptage des CVE.", "pending": -1}
    if cve_importer.is_running():
        return {"message": "Un import NVD est déjà en cours.", "pending": pending}

    background_tasks.add_task(cve_importer.backfill_cve_severity)
    return {"message": f"Backfill sévérité lancé ({pending} CVE en attente).", "pending": pending}


@app.get("/api/token-status")
def token_status_api():
    """Retourne le nombre de tokens configurés (sans exposer les valeurs)."""
    from src import github_client
    return {"token_count": github_client.token_count(), "has_tokens": github_client.token_count() > 0}


# ── STIX 2.1 & IOC Feed ──────────────────────────────────────────────

@app.post("/api/ingest/run")
def ingest_run_api(background_tasks: BackgroundTasks, full: bool = False, _u: str = Depends(src.auth.verify_admin)):
    """Lance le pipeline d'ingestion massive (abuse.ch + OTX + EPSS + OpenCVE)."""
@app.get("/api/ingest/stats")
def ingest_stats_api():
    """Statistiques de volumetrie IOC."""
@app.post("/api/keywords/ai-validate")
def ai_validate_keywords_api(limit: int = 200, threshold: float = 0.6,
                              _u: str = Depends(src.auth.verify_admin)):
    """Valide automatiquement les mots-cles en attente via HF zero-shot."""
@app.get("/api/keywords/stats")
def keyword_stats_api():
    """Statistiques de validation des mots-cles."""
@app.get("/api/intel/virustotal")
def intel_vt_api(identifier: str = "", resource_type: str = "auto"):
    """Query VirusTotal API for an IP, domain, URL, or hash."""
@app.get("/api/intel/securitytrails")
def intel_st_api(domain: str = "", ip: str = ""):
    """Query SecurityTrails API for a domain (passive DNS, subdomains, WHOIS) or IP."""
@app.get("/api/intel/shodan")
def intel_shodan_api(ip: str = "", query: str = ""):
    """Query Shodan API for an IP host or search query."""
@app.post("/api/intel/enrich-all")
def intel_enrich_api(limit: int = 20, _u: str = Depends(src.auth.verify_admin)):
    """Enrich existing IOCs via VirusTotal + SecurityTrails + Shodan."""
@app.get("/api/intel/status")
def intel_status_api():
    """Check which premium APIs are configured."""
    import os
    return {
        "virustotal": bool(os.getenv("VIRUSTOTAL_API_KEY")),
        "securitytrails": bool(os.getenv("SECURITYTRAILS_API_KEY")),
        "shodan": bool(os.getenv("SHODAN_API_KEY")),
    }
