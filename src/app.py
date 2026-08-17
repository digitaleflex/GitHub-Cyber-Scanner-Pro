import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

DATA_DIR = Path("data")
REPORTS_DIR = Path("reports")
LAST_SCAN_FILE = DATA_DIR / "last_scan.json"
SEEN_FILE = DATA_DIR / "seen.json"

app = FastAPI(
    title="CyberScan Dashboard",
    description="Visualisation des scans d'outils cybersecurite GitHub",
    version="2.0.0",
)

FRONTEND_DIR = Path("frontend/dist")
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="frontend_assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cyberbook.eurin.tech",
        "http://cyberbook.eurin.tech",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def get_repos():
    data = load_json(LAST_SCAN_FILE)
    return data if isinstance(data, list) else []


@app.get("/", response_class=HTMLResponse)
def dashboard():
    if FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists():
        return HTMLResponse((FRONTEND_DIR / "index.html").read_text())

    repos = get_repos()
    repos.sort(key=lambda r: r["stars"], reverse=True)

    last_scan = "N/A"
    try:
        mtime = os.path.getmtime(LAST_SCAN_FILE)
        last_scan = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
    except OSError:
        pass

    reports = sorted(
        [f.name for f in REPORTS_DIR.glob("rapport_*.md")],
        reverse=True,
    ) if REPORTS_DIR.exists() else []

    dashboards = sorted(
        [f.name for f in REPORTS_DIR.glob("dashboard_*.html")],
        reverse=True,
    ) if REPORTS_DIR.exists() else []

    top = sorted(repos, key=lambda r: r["stars"], reverse=True)[:5]

    lang_dist = {}
    for r in repos:
        lang = r.get("lang") or "Autre"
        lang_dist[lang] = lang_dist.get(lang, 0) + 1
    top_langs = sorted(lang_dist.items(), key=lambda x: -x[1])[:8]

    lang_bars_html = ""
    if top_langs:
        max_lang = top_langs[0][1]
        lang_colors = ["#6366f1","#10b981","#f59e0b","#ef4444","#06b6d4","#8b5cf6","#ec4899","#14b8a6"]
        for i, (lang, count) in enumerate(top_langs):
            pct = max(5, count / max_lang * 100)
            color = lang_colors[i % 8]
            lang_bars_html += f'<div class="lang-bar"><span style="width:70px;font-size:0.8rem;color:#94a3b8;">{lang}</span><div class="bar-wrap"><div class="bar-fill" style="width:{pct}%;background:{color};"></div></div><span class="count">{count}</span></div>'
    else:
        lang_bars_html = '<div class="empty">Aucun langage</div>'

    top5_html = ""
    if top:
        for r in top:
            top5_html += f'<div class="top-item"><span class="name">★ <a class="repo-link" href="{r["url"]}" target="_blank">{r["name"]}</a></span><span class="stars">{r["stars"]:,}</span></div>'
    else:
        top5_html = '<div class="empty">Pas encore de donnees</div>'

    repos_rows = ""
    if repos:
        for r in repos:
            repos_rows += f'<tr><td><a class="repo-link" href="{r["url"]}" target="_blank">{r["name"]}</a></td><td class="star-val">{r["stars"]:,}</td><td><span class="lang-tag">{r.get("lang") or "?"}</span></td><td style="color:#94a3b8;max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{r.get("desc","")[:100]}</td><td style="color:#64748b;">{r.get("updated","")[:10]}</td></tr>'
    else:
        repos_rows = '<tr><td colspan="5" class="empty">Aucun outil trouve</td></tr>'

    reports_links = ""
    if reports:
        reports_links = " ".join(f'<a class="report-link" href="/reports/{r}" target="_blank">{r}</a>' for r in reports)
    else:
        reports_links = '<span style="color:#64748b;">Aucun rapport genere</span>'

    dashboards_section = ""
    if dashboards:
        dashboards_section = '<h2 style="color:#94a3b8;font-size:1.1rem;font-weight:600;margin:1rem 0 0.75rem;">Dashboards</h2><div>' + " ".join(f'<a class="report-link" href="/dashboards/{d}" target="_blank">{d}</a>' for d in dashboards) + "</div>"

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CyberScan Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Inter',sans-serif; background:#0a0e17; color:#e2e8f0; min-height:100vh; }}
.bg-glow {{ position:fixed; top:-20%; left:-10%; width:60%; height:60%; background:radial-gradient(circle,rgba(99,102,241,0.08),transparent 70%); pointer-events:none; z-index:0; }}
.bg-glow2 {{ position:fixed; bottom:-20%; right:-10%; width:60%; height:60%; background:radial-gradient(circle,rgba(139,92,246,0.08),transparent 70%); pointer-events:none; z-index:0; }}
.wrapper {{ position:relative; z-index:1; max-width:1400px; margin:0 auto; padding:2rem; }}

header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem; flex-wrap:wrap; gap:1rem; }}
h1 {{ font-size:1.75rem; font-weight:800; background:linear-gradient(135deg,#a5b4fc,#6366f1,#8b5cf6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
.header-right {{ display:flex; align-items:center; gap:1rem; color:#94a3b8; font-size:0.9rem; }}
.status-dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; background:#10b981; margin-right:6px; }}

.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:1rem; margin-bottom:2rem; }}
.stat-card {{ background:rgba(17,25,45,0.75); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:1.25rem; backdrop-filter:blur(12px); }}
.stat-card .num {{ font-size:1.75rem; font-weight:700; color:#e2e8f0; }}
.stat-card .label {{ font-size:0.8rem; color:#64748b; margin-top:4px; }}

.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin-bottom:2rem; }}
@media (max-width:768px) {{ .grid2 {{ grid-template-columns:1fr; }} }}

.card {{ background:rgba(17,25,45,0.75); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:1.5rem; backdrop-filter:blur(12px); }}
.card h2 {{ font-size:1.1rem; font-weight:600; margin-bottom:1rem; color:#94a3b8; }}

.top-item {{ display:flex; justify-content:space-between; align-items:center; padding:0.6rem 0; border-bottom:1px solid rgba(255,255,255,0.04); }}
.top-item:last-child {{ border:none; }}
.top-item .name {{ color:#e2e8f0; font-size:0.9rem; }}
.top-item .stars {{ color:#f59e0b; font-weight:600; font-size:0.85rem; }}

.lang-bar {{ display:flex; align-items:center; gap:0.5rem; padding:0.4rem 0; }}
.lang-bar .bar-wrap {{ flex:1; height:6px; background:rgba(255,255,255,0.06); border-radius:3px; overflow:hidden; }}
.lang-bar .bar-fill {{ height:100%; border-radius:3px; transition:width 0.6s ease; }}
.lang-bar .count {{ font-size:0.8rem; color:#64748b; min-width:2rem; text-align:right; }}

.search-bar {{ margin-bottom:1rem; }}
.search-bar input {{ width:100%; padding:0.75rem 1rem; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:8px; color:#e2e8f0; font-size:0.9rem; outline:none; }}
.search-bar input:focus {{ border-color:#6366f1; }}

table {{ width:100%; border-collapse:collapse; font-size:0.85rem; }}
th {{ text-align:left; padding:0.75rem 0.5rem; color:#64748b; font-weight:500; border-bottom:1px solid rgba(255,255,255,0.06); cursor:pointer; user-select:none; }}
th:hover {{ color:#94a3b8; }}
td {{ padding:0.6rem 0.5rem; border-bottom:1px solid rgba(255,255,255,0.03); }}
tr:hover td {{ background:rgba(99,102,241,0.04); }}
.repo-link {{ color:#818cf8; text-decoration:none; }}
.repo-link:hover {{ text-decoration:underline; }}
.star-val {{ color:#f59e0b; }}
.lang-tag {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.75rem; background:rgba(99,102,241,0.15); color:#a5b4fc; }}

.reports-section {{ margin-top:2rem; }}
.report-link {{ display:inline-block; padding:0.5rem 1rem; background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.2); border-radius:6px; color:#a5b4fc; text-decoration:none; font-size:0.85rem; margin:0.25rem; }}
.report-link:hover {{ background:rgba(99,102,241,0.2); }}

.empty {{ text-align:center; padding:3rem; color:#64748b; }}

footer {{ text-align:center; padding:2rem; color:#475569; font-size:0.8rem; }}
</style>
</head>
<body>
<div class="bg-glow"></div>
<div class="bg-glow2"></div>
<div class="wrapper">

<header>
<div><h1>CyberScan Dashboard</h1></div>
<div class="header-right">
<span><span class="status-dot"></span>Dernier scan: {last_scan}</span>
</div>
</header>

<div class="stats">
<div class="stat-card"><div class="num">{total:,}</div><div class="label">Outils trouves</div></div>
<div class="stat-card"><div class="num">{total_stars:,}</div><div class="label">Etoiles totales</div></div>
<div class="stat-card"><div class="num">{languages}</div><div class="label">Langages</div></div>
<div class="stat-card"><div class="num">{len(get_repos()):,}</div><div class="label">Dans la base</div></div>
</div>

<div class="grid2">
<div class="card">
        <h2>Top 5</h2>
{top5_html}
</div>
<div class="card">
<h2>Langages</h2>
{lang_bars_html}
</div>
</div>

<div class="card">
<h2>Tous les outils</h2>
<div class="search-bar"><input type="text" id="search" placeholder="Rechercher par nom, description, langage..." oninput="filterTable()"></div>
<div style="overflow-x:auto;">
<table><thead><tr><th onclick="sortTable(0)">Nom</th><th onclick="sortTable(1)">Stars</th><th onclick="sortTable(2)">Langage</th><th>Description</th><th onclick="sortTable(4)">Mis a jour</th></tr></thead>
<tbody id="repos-tbody">
{repos_rows}
</tbody></table>
</div>
</div>

<div class="reports-section">
<h2 style="color:#94a3b8;font-size:1.1rem;font-weight:600;margin-bottom:0.75rem;">Rapports</h2>
<div>
{reports_links}
</div>
{dashboards_section}
</div>

<footer>Genere par CyberScan Pro</footer>
</div>

<script>
function filterTable() {{
var input = document.getElementById('search').value.toLowerCase();
var rows = document.querySelectorAll('#repos-tbody tr');
rows.forEach(function(row) {{
var text = row.textContent.toLowerCase();
row.style.display = text.includes(input) ? '' : 'none';
}});
}}

function sortTable(col) {{
var tbody = document.getElementById('repos-tbody');
var rows = Array.from(tbody.querySelectorAll('tr'));
var desc = tbody.dataset.sortDir === 'asc' && tbody.dataset.sortCol == col;
tbody.dataset.sortDir = desc ? 'desc' : 'asc';
tbody.dataset.sortCol = col;
rows.sort(function(a,b) {{
var va = a.children[col].textContent.trim();
var vb = b.children[col].textContent.trim();
var na = parseFloat(va.replace(/[^0-9.-]/g,''));
var nb = parseFloat(vb.replace(/[^0-9.-]/g,''));
if (!isNaN(na) && !isNaN(nb)) return desc ? nb - na : na - nb;
return desc ? vb.localeCompare(va) : va.localeCompare(vb);
}});
rows.forEach(function(r) {{ tbody.appendChild(r); }});
}}
</script>
</body>
</html>"""
    return html


@app.get("/api/repos")
def api_repos(q: str = Query(None)):
    repos = get_repos()
    if q:
        ql = q.lower()
        repos = [
            r for r in repos
            if ql in r["name"].lower()
            or ql in r.get("desc", "").lower()
            or ql in (r.get("lang") or "").lower()
        ]
    return {"total": len(repos), "repos": repos}


@app.get("/api/stats")
def api_stats():
    repos = get_repos()
    total = len(repos)
    total_stars = sum(r["stars"] for r in repos)
    languages = len({r["lang"] for r in repos if r.get("lang")})
    lang_dist = {}
    for r in repos:
        lang = r.get("lang") or "Autre"
        lang_dist[lang] = lang_dist.get(lang, 0) + 1
    last_scan = None
    try:
        mtime = os.path.getmtime(LAST_SCAN_FILE)
        last_scan = datetime.fromtimestamp(mtime).isoformat()
    except OSError:
        pass
    return {
        "total_repos": total,
        "total_stars": total_stars,
        "languages": languages,
        "lang_distribution": lang_dist,
        "last_scan": last_scan,
    }


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)
