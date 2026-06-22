"""
Genere un dashboard HTML pour visualiser les donnees du scan.
Usage: python scripts/dashboard.py
"""

import json
import os
from datetime import datetime


def load_data():
    try:
        with open("data/last_scan.json") as f:
            return json.load(f)
    except:
        return []


def generate_html(repos):
    repos.sort(key=lambda r: r["stars"], reverse=True)

    rows = ""
    for r in repos:
        rows += f"""
        <tr>
            <td><a href="{r['url']}" target="_blank">{r['name']}</a></td>
            <td>{r['stars']}</td>
            <td>{r['lang'] or '?'}</td>
            <td>{r['desc'][:80]}</td>
            <td>{r['updated'][:10]}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberScan Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }}
        h1 {{ color: #58a6ff; margin-bottom: 10px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ background: #161b22; padding: 15px 25px; border-radius: 8px; border: 1px solid #30363d; }}
        .stat .number {{ font-size: 28px; font-weight: bold; color: #58a6ff; }}
        .stat .label {{ color: #8b949e; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: #161b22; border-radius: 8px; overflow: hidden; }}
        th {{ background: #21262d; padding: 12px; text-align: left; color: #58a6ff; }}
        td {{ padding: 10px 12px; border-top: 1px solid #30363d; }}
        tr:hover {{ background: #1c2128; }}
        a {{ color: #58a6ff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .empty {{ text-align: center; padding: 40px; color: #8b949e; }}
    </style>
</head>
<body>
    <h1>CyberScan Dashboard</h1>
    <p style="color: #8b949e;">Dernier scan : {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    
    <div class="stats">
        <div class="stat">
            <div class="number">{len(repos)}</div>
            <div class="label">Nouveaux outils</div>
        </div>
        <div class="stat">
            <div class="number">{sum(r['stars'] for r in repos)}</div>
            <div class="label">Etoiles totales</div>
        </div>
        <div class="stat">
            <div class="number">{len(set(r['lang'] for r in repos if r['lang']))}</div>
            <div class="label">Langages</div>
        </div>
    </div>

    {"<table><tr><th>Repository</th><th>Stars</th><th>Langage</th><th>Description</th><th>Mis a jour</th></tr>" + rows + "</table>" if repos else '<div class="empty">Pas de donnees. Lance le scan d\'abord.</div>'}
</body>
</html>"""

    os.makedirs("reports", exist_ok=True)
    filename = f"reports/dashboard_{datetime.now().strftime('%Y%m%d')}.html"
    with open(filename, "w") as f:
        f.write(html)
    print(f"Dashboard genere: {filename}")


if __name__ == "__main__":
    repos = load_data()
    generate_html(repos)
