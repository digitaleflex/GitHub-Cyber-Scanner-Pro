"""Cyber Scanner Pro — main entrypoint."""
import logging
import os

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from src.config import app, SCAN_INTERVAL_SECONDS, DOMAIN, FRONTEND_DIR, REPORTS_DIR
from src.api_routes import *  # noqa
from src.scan_engine import (scanner_status, scan_in_progress, scanner_lock,
                            _run_keyword_miner, scan_cycle, run_scan_once_manual,
                            run_scanner_daemon)
from src import database

import json
import threading
import time
from datetime import datetime
from pathlib import Path

# --- Social Graph Neo4j ---

@app.get("/api/graph/stats")
def graph_stats_api():
    from src.social_graph import get_graph_stats
    return get_graph_stats()


@app.get("/api/graph/query")
def graph_query_api(label: str = "", limit: int = 50):
    from src.social_graph import query_graph
    return query_graph(label, limit)


@app.post("/api/graph/seed")
def graph_seed_api():
    from src.social_graph import init_graph, seed_from_repos, seed_from_cves
    from src import database
    init_graph()
    repos = database.get_repos_frontend()
    seed_from_repos(repos)
    cves_data = database.search_cves(page=1, per_page=500)
    seed_from_cves(cves_data.get("cves", []))
    from src.social_graph import link_collaborations
    collabs = link_collaborations()
    return {"message": "Graph seeded", "repos": len(repos), "cves": len(cves_data.get("cves", [])), "collaborations": collabs}


# --- FRONTEND SERVING (React SPA + Reports) ---

FRONTEND_DIR = Path("frontend/dist")
if FRONTEND_DIR.exists() and (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="frontend_assets")

REPORTS_DIR = Path("reports")


@app.get("/api/reports")
def api_reports():
    if not REPORTS_DIR.exists():
        return {"reports": [], "dashboards": []}
    reports = sorted([f.name for f in REPORTS_DIR.glob("rapport_*.md")], reverse=True)
    dashboards = sorted([f.name for f in REPORTS_DIR.glob("dashboard_*.html")], reverse=True)
    return {"reports": reports, "dashboards": dashboards}


@app.get("/reports/{filename}")
def serve_report(filename: str):
    filepath = REPORTS_DIR / filename
    if filepath.exists() and filepath.suffix in (".md", ".html"):
        return FileResponse(filepath)
    return HTMLResponse("<h1>404</h1>", status_code=404)


@app.get("/dashboards/{filename}")
def serve_dashboard(filename: str):
    filepath = REPORTS_DIR / filename
    if filepath.exists() and filepath.suffix == ".html":
        return FileResponse(filepath)
    return HTMLResponse("<h1>404</h1>", status_code=404)


@app.get("/{path:path}")
def serve_frontend(path: str):
    if path.startswith("api/") or path.startswith("reports/") or path.startswith("dashboards/"):
        return HTMLResponse("<h1>404</h1>", status_code=404)
    index = FRONTEND_DIR / "index.html" if FRONTEND_DIR.exists() else None
    if index and index.exists():
        return HTMLResponse(index.read_text())
    return HTMLResponse("<h1>CyberScan API</h1><p>Frontend non disponible</p>")


def _bootstrap_ontology():
    """Importe l'ontologie MITRE au premier démarrage si la base est vide."""
    try:
        approved = database.get_approved_keywords()
        if len(approved) >= 1000:
            logging.info("🧬 Ontologie déjà chargée (%d termes)", len(approved))
            from nlp_processor import refresh_cyber_terms
            refresh_cyber_terms()
            return
        import ontology_enricher
        count = ontology_enricher.import_ontology_to_db()
        logging.info("🧬 Ontologie bootstrap: %d termes importes", count)
    except Exception as e:
        logging.error(f"❌ Erreur bootstrap ontologie: {e}")


if __name__ == "__main__":
    database.init_db()

    bootstrap_thread = threading.Thread(target=_bootstrap_ontology, daemon=True)
    bootstrap_thread.start()

    def _run_cve_updater():
        import src.cve_importer as cve_importer
        time.sleep(30)
        while True:
            try:
                logging.info("CVE updater: import NVD...")
                cve_importer.import_cve_all()
                logging.info("CVE updater: terminé, prochain dans 24h")
            except Exception as e:
                logging.error(f"CVE updater error: {e}")
            time.sleep(86400)

    cve_thread = threading.Thread(target=_run_cve_updater, daemon=True)
    cve_thread.start()

    from mcp.server.fastmcp import FastMCP
    from src.mcp_server import register_tools

    mcp_app = FastMCP("Cyber Scanner Pro")
    register_tools(mcp_app)

    from mcp.server.sse import SseServerTransport
    from fastapi import Request

    sse_transport = SseServerTransport("/mcp/messages/")

    @app.get("/mcp/sse")
    async def mcp_sse(request: Request):
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp_app.run(streams[0], streams[1])

    @app.post("/mcp/messages/")
    async def mcp_messages(request: Request):
        await sse_transport.handle_post_message(
            request.scope, request.receive, request._send
        )

    logging.info("MCP Server: /mcp/sse (SSE), /mcp/messages/ (POST)")

    def _seed_graph():
        try:
            from src.social_graph import init_graph, seed_from_repos, seed_from_cves, link_collaborations
            if init_graph():
                repos = database.get_repos_frontend()
                r_count = seed_from_repos(repos)
                cves_data = database.search_cves(page=1, per_page=500)
                c_count = seed_from_cves(cves_data.get("cves", []))
                collabs = link_collaborations()
                logging.info("Graph Neo4j seeder: %d repos, %d CVEs, %d collaborations", r_count, c_count, collabs)
        except Exception as e:
            logging.warning("Graph Neo4j non disponible au demarrage: %s", e)

    graph_thread = threading.Thread(target=_seed_graph, daemon=True)
    graph_thread.start()

    daemon_thread = threading.Thread(target=run_scanner_daemon, daemon=True)
    daemon_thread.start()

    import uvicorn
    logging.info("Lancement du serveur Web FastAPI sur le port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
