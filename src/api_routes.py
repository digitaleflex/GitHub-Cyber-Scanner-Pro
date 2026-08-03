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


@app.get("/api/organization")
def get_organization_api(profile_id: int = 0):
    """Retourne l'organisation, ses assets et le profil."""
    import src.context_engine as ctx
    conn = database.get_db_connection()
    cursor = conn.cursor()
    profile = ctx.ensure_profile(profile_id=profile_id)
    org_id = profile.get("org_id")
    org = None
    assets = []
    if org_id:
        cursor.execute("SELECT id, name, sector, compliance_frameworks FROM organizations WHERE id = %s", (org_id,))
        row = cursor.fetchone()
        if row:
            org = {"id": row[0], "name": row[1], "sector": row[2] or "", "compliance": row[3] or ""}
        cursor.execute(
            """SELECT id, asset_type, name, vendor, version, exposed, criticality
               FROM asset_inventory WHERE org_id = %s ORDER BY criticality DESC, name""",
            (org_id,),
        )
        assets = [{"id": r[0], "type": r[1], "name": r[2], "vendor": r[3] or "", "version": r[4] or "", "exposed": r[5], "criticality": r[6]} for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"profile": profile, "organization": org, "assets": assets, "assets_count": len(assets)}


@app.post("/api/organization")
def update_organization_api(profile_id: int, org_name: str = "", sector: str = "", compliance: str = ""):
    """Met a jour l'organisation."""
    import src.context_engine as ctx
    profile = ctx.ensure_profile(profile_id=profile_id)
    conn = database.get_db_connection()
    cursor = conn.cursor()
    org_id = profile.get("org_id")

    if not org_id and org_name:
        cursor.execute(
            "INSERT INTO organizations (name, sector, compliance_frameworks) VALUES (%s, %s, %s) RETURNING id",
            (org_name, sector, compliance),
        )
        org_id = cursor.fetchone()[0]
        cursor.execute("UPDATE user_profiles SET org_id = %s WHERE id = %s", (org_id, profile_id))
    elif org_id:
        cursor.execute(
            "UPDATE organizations SET name = %s, sector = %s, compliance_frameworks = %s WHERE id = %s",
            (org_name or profile.get("org_name", ""), sector, compliance, org_id),
        )
    conn.commit()
    cursor.close()
    conn.close()
    return {"org_id": org_id, "name": org_name, "sector": sector}


@app.post("/api/assets/add")
def add_asset_api(profile_id: int, asset_type: str = "product", name: str = "", vendor: str = "", version: str = "", criticality: int = 3):
    """Ajoute un asset a l'inventaire."""
    import src.context_engine as ctx
    profile = ctx.ensure_profile(profile_id=profile_id)
    org_id = profile.get("org_id")
    if not org_id:
        return {"error": "Aucune organisation. Creez-en une d'abord."}
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO asset_inventory (org_id, asset_type, name, vendor, version, criticality)
           VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
        (org_id, asset_type, name[:200], vendor, version, min(max(criticality, 1), 5)),
    )
    asset_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return {"id": asset_id, "added": True}


@app.get("/api/missions")
def get_missions_api(org_id: int | None = None, status: str | None = None, limit: int = 20):
    """Liste les missions avec progression."""
    import src.mission_engine as me
    missions = me.get_missions(org_id=org_id, status=status, limit=limit)
    return {"missions": missions, "count": len(missions)}


@app.get("/api/missions/{mission_id}")
def get_mission_api(mission_id: int):
    """Detail d'une mission avec ses etapes."""
    import src.mission_engine as me
    m = me.get_mission(mission_id)
    if not m:
        return {"error": "Mission introuvable"}
    return m


@app.post("/api/missions")
def create_mission_api(org_id: int, cve_id: str = "", desc: str = "", cvss: float = 0):
    """Cree une mission a partir d'une decision CVE."""
    import src.mission_engine as me
    result = me.create_mission_from_decision(org_id, cve_id, desc, cvss)
    return result


@app.post("/api/missions/{mission_id}/start")
def start_mission_api(mission_id: int):
    """Demarre une mission."""
    import src.mission_engine as me
    return me.start_mission(mission_id)


@app.post("/api/missions/{mission_id}/steps/{step_id}/done")
def complete_step_api(mission_id: int, step_id: int):
    """Marque une etape comme terminee."""
    import src.mission_engine as me
    return me.complete_step(mission_id, step_id)


@app.post("/api/missions/{mission_id}/complete")
def complete_mission_api(mission_id: int):
    """Termine une mission."""
    import src.mission_engine as me
    return me.complete_mission(mission_id)


@app.get("/api/threat-intel")
def threat_intel_api():
    """Threat Intelligence agrege : campagnes actives, tendances, CVE recentes."""
    from src import database
    conn = database.get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cve_id, description, severity, cvss_score, published, weaknesses
        FROM cve_entries
        WHERE weaknesses ILIKE '%%CISA_KEV%%'
        ORDER BY published DESC NULLS LAST
        LIMIT 15
    """)
    kev_cves = [{"cve_id": r[0], "description": (r[1] or "")[:200], "severity": r[2], "cvss_score": r[3], "published": str(r[4]) if r[4] else None} for r in cursor.fetchall()]

    cursor.execute("""
        SELECT cve_id, epss, percentile
        FROM epss_scores
        WHERE epss IS NOT NULL
        ORDER BY epss DESC
        LIMIT 10
    """)
    top_epss = [{"cve_id": r[0], "epss": float(r[1]), "percentile": float(r[2]) if r[2] else 0} for r in cursor.fetchall()]

    cursor.execute("""
        SELECT cve_id, description, severity, cvss_score, published
        FROM cve_entries
        WHERE severity IN ('CRITICAL', 'HIGH') AND published IS NOT NULL
        ORDER BY published DESC NULLS LAST
        LIMIT 15
    """)
    recent_criticals = [{"cve_id": r[0], "description": (r[1] or "")[:200], "severity": r[2], "cvss_score": r[3], "published": str(r[4]) if r[4] else None} for r in cursor.fetchall()]

    cursor.execute("""
        SELECT platform, COUNT(*) as cnt
        FROM exploits
        WHERE platform IS NOT NULL AND platform <> ''
        GROUP BY platform
        ORDER BY cnt DESC
        LIMIT 10
    """)
    top_platforms = [{"platform": r[0], "count": r[1]} for r in cursor.fetchall()]

    cursor.execute("""
        SELECT language, COUNT(*) as cnt
        FROM repositories
        WHERE language IS NOT NULL AND language <> 'Non specifiee'
        GROUP BY language
        ORDER BY cnt DESC
        LIMIT 10
    """)
    top_languages = [{"language": r[0], "count": r[1]} for r in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM cve_entries WHERE weaknesses ILIKE '%%CISA_KEV%%'")
    kev_total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM exploits")
    exploits_total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM cve_entries
        WHERE severity IN ('CRITICAL', 'HIGH') AND published >= NOW() - INTERVAL '30 days'
    """)
    recent_critical_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return {
        "kev": {"total": kev_total, "top": kev_cves},
        "epss": {"top": top_epss},
        "recent_criticals": {"total": recent_critical_count, "cves": recent_criticals},
        "exploit_platforms": {"total_exploits": exploits_total, "top_platforms": top_platforms},
        "stack_languages": top_languages,
    }


@app.get("/api/profile")
def get_profile_api(profile_id: int = 0):
    """Profil utilisateur courant."""
    import src.context_engine as ctx
    return ctx.ensure_profile(profile_id=profile_id)


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


@app.get("/api/cve/{cve_id}/decision")
def cve_decision_api(cve_id: str):
    """Decision Engine appliqué à une CVE spécifique (score, raisons, risque, confiance)."""
    import src.priority_engine as pe
    import src.correlation as corr
    import src.context_engine as ctx
    import src.epss as epss_mod

    detail = corr.get_cve_detail(cve_id)
    if "error" in detail:
        return detail

    stack_kws, _ = ctx.build_user_context()
    epss_data = epss_mod.get_epss_for_cve(cve_id)
    epss_val = (epss_data or {}).get("epss", 0)

    cve_dict = {
        "cve_id": cve_id,
        "description": detail.get("description", ""),
        "severity": detail.get("severity", ""),
        "cvss_score": detail.get("cvss_score"),
        "published": detail.get("published"),
        "weaknesses": detail.get("weaknesses", ""),
        "_tokens": set(),
    }
    decision = pe.score_cve(cve_dict, stack_kws, detail.get("exploits", []), None, 0.0, epss_val)
    return decision


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
@app.get("/api/download/json")
def download_json(_u: str = Depends(src.auth.verify_admin)):
    """Téléchargement de l'export JSON."""
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

