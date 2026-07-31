"""Exporters: Excel, JSON, Markdown/HTML reports."""
import logging
import json
import os
import pandas as pd
from src import database

def export_to_excel():
    """Exporte les dépôts et les livres de Postgres vers un fichier Excel multi-onglets."""
    logging.info("📊 Exportation de la base de données PostgreSQL vers Excel...")
    try:
        conn = database.get_db_connection()

        # 1. Lire les dépôts avec score_qualite et verdict de sécurité
        df_repos = pd.read_sql_query(
            "SELECT full_name, stars, description, html_url, language, updated_at, score_qualite, security_verdict FROM repositories",
            conn
        )

        # 2. Lire les livres avec score_qualite et type_ressource
        df_books = pd.read_sql_query(
            """
            SELECT b.title, b.category, b.type_ressource, r.full_name AS repo_name, 
                   CASE WHEN b.is_dead = 1 THEN 'Hors ligne' 
                        WHEN b.last_checked IS NULL THEN 'Non vérifié'
                        ELSE 'Disponible' END AS status,
                   b.url, b.score_qualite, r.security_verdict 
            FROM books b 
            LEFT JOIN repositories r ON b.repo_id = r.id
            """,
            conn
        )
        conn.close()

        # Formater les dépôts
        if not df_repos.empty:
            df_repos.columns = [
                "Nom du Dépôt", "Étoiles (Stars)", "Description", "Lien GitHub", "Langue Principale", "Dernière Mise à Jour", "Score Qualité (IA)", "Verdict Sécurité"
            ]
            # Trier d'abord par Score Qualité (IA) puis par Étoiles
            df_repos = df_repos.sort_values(by=["Score Qualité (IA)", "Étoiles (Stars)"], ascending=[False, False])
            for col in df_repos.select_dtypes(include=['object']).columns:
                df_repos[col] = df_repos[col].astype(str).str.slice(0, 32000)

        # Formater les livres
        if not df_books.empty:
            df_books.columns = [
                "Titre de la Ressource / Livre", "Catégorie", "Type de Ressource", "Dépôt Source", "Disponibilité", "Lien de Téléchargement", "Score Qualité (IA)", "Sécurité Source"
            ]
            # Trier d'abord par Score Qualité (IA) puis par Type, Catégorie et Titre
            df_books = df_books.sort_values(by=["Score Qualité (IA)", "Type de Ressource", "Catégorie", "Titre de la Ressource / Livre"], ascending=[False, True, True, True])
            for col in df_books.select_dtypes(include=['object']).columns:
                df_books[col] = df_books[col].astype(str).str.slice(0, 32000)

        # Sauvegarder Excel
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            if not df_repos.empty:
                df_repos.to_excel(writer, sheet_name="Dépôts GitHub", index=False)
            if not df_books.empty:
                df_books.to_excel(writer, sheet_name="Livres & Ressources", index=False)

        logging.info(f"💾 Fichier Excel mis à jour avec succès : [{EXCEL_FILE}]")
    except Exception as e:
        logging.error(f"❌ Erreur lors de la génération du fichier Excel : {e}")


def export_to_json():
    """Exporte les dépôts et leurs livres associés de Postgres vers un fichier JSON structuré."""
    logging.info("📂 Exportation de la base de données PostgreSQL vers JSON...")
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()

        # Récupérer tous les dépôts avec score_qualite et verdict de sécurité
        cursor.execute("SELECT id, full_name, stars, description, html_url, language, updated_at, score_qualite, security_verdict FROM repositories ORDER BY score_qualite DESC, stars DESC")
        repos_rows = cursor.fetchall()

        data_dict = {}
        for r in repos_rows:
            repo_id = r[0]
            data_dict[repo_id] = {
                "Nom du Dépôt": r[1],
                "Étoiles (Stars)": r[2],
                "Description": r[3],
                "Lien GitHub": r[4],
                "Langue Principale": r[5],
                "Dernière Mise à Jour": r[6],
                "Score Qualité (IA)": r[7],
                "Verdict Sécurité": r[8],
                "Ressources": []
            }

        # Récupérer tous les livres avec score_qualite et type_ressource
        cursor.execute(
            """
            SELECT repo_id, title, category, type_ressource, 
                   CASE WHEN is_dead = 1 THEN 'Hors ligne'
                        WHEN last_checked IS NULL THEN 'Non vérifié'
                        ELSE 'Disponible' END AS status,
                   url, score_qualite 
            FROM books
            ORDER BY score_qualite DESC, title ASC
            """
        )
        books_rows = cursor.fetchall()
        conn.close()

        for b in books_rows:
            repo_id = b[0]
            if repo_id in data_dict:
                data_dict[repo_id]["Ressources"].append({
                    "Titre de la Ressource / Livre": b[1],
                    "Catégorie": b[2],
                    "Type de Ressource": b[3],
                    "Disponibilité": b[4],
                    "Lien de Téléchargement": b[5],
                    "Score Qualité (IA)": b[6]
                })

        # Pour trier le dictionnaire par score_qualite des dépôts
        sorted_data = dict(sorted(data_dict.items(), key=lambda item: item[1]["Score Qualité (IA)"], reverse=True))

        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted_data, f, indent=4, ensure_ascii=False)

        logging.info(f"💾 Fichier JSON mis à jour avec succès : [{JSON_FILE}]")
    except Exception as e:
        logging.error(f"❌ Erreur lors de la génération du fichier JSON : {e}")


def export_reports():
    """Génère le rapport Markdown et le dashboard HTML du scan depuis la base."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM repositories")
        total_repos = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(stars), 0) FROM repositories")
        total_stars = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT language) FROM repositories WHERE language IS NOT NULL AND language != 'Non specifiee'")
        total_langs = cursor.fetchone()[0]

        cursor.execute("""
            SELECT full_name, stars, description, html_url, language, updated_at, security_verdict
            FROM repositories ORDER BY stars DESC LIMIT 10
        """)
        top_repos = cursor.fetchall()

        cursor.execute("""
            SELECT language, COUNT(*) FROM repositories
            WHERE language IS NOT NULL AND language != 'Non specifiee'
            GROUP BY language ORDER BY COUNT(*) DESC LIMIT 10
        """)
        lang_dist = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM repositories WHERE security_verdict = 'Critique'")
        critique_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM repositories WHERE security_verdict = 'Suspect'")
        suspect_count = cursor.fetchone()[0]

        cursor.execute("SELECT full_name, security_verdict FROM repositories WHERE security_verdict IN ('Critique', 'Suspect') ORDER BY security_scan_date DESC NULLS LAST LIMIT 10")
        flagged_repos = cursor.fetchall()

        cursor.execute("SELECT full_name, stars FROM repositories ORDER BY stars DESC LIMIT 5")
        top5 = cursor.fetchall()

        cursor.close()
        conn.close()

        now = datetime.now()
        date_str = now.strftime("%d/%m/%Y %H:%M")
        file_date = now.strftime("%Y%m%d_%H%M%S")
        reports_dir = REPORTS_DIR
        reports_dir.mkdir(parents=True, exist_ok=True)

        verdict_badge = {"Critique": "🔴", "Suspect": "🟡", "Sain": "🟢"}

        md_lines = [
            "# CyberScan — Rapport de Scan",
            f"**{date_str}**\n",
            "## Résumé",
            f"- Total dépôts : **{total_repos:,}**",
            f"- Total étoiles : **{total_stars:,}**",
            f"- Langages distincts : **{total_langs}**",
            f"- Dépôts critique : **{critique_count}**",
            f"- Dépôts suspect : **{suspect_count}**",
            "",
            "## Top 5 par étoiles",
        ]
        for i, (name, stars) in enumerate(top5, 1):
            md_lines.append(f"{i}. ★ **{stars:,}** — {name}")

        md_lines.extend(["", "## Top 10", ""])
        for i, (name, stars, desc, url, lang, updated, verdict) in enumerate(top_repos, 1):
            badge = verdict_badge.get(verdict, "⚪")
            md_lines.append(f"### {i}. [{name}]({url})")
            md_lines.append(f"★ {stars:,} | {lang or '?'} | {updated[:10] if updated else 'N/A'} | {badge} {verdict or 'Non analysé'}")
            md_lines.append("")
            if desc:
                md_lines.append(f"> {desc[:200]}")
                md_lines.append("")

        if flagged_repos:
            md_lines.extend(["## Alertes Sécurité", ""])
            for name, verdict in flagged_repos:
                badge = verdict_badge.get(verdict, "⚪")
                md_lines.append(f"- {badge} **{verdict}** — {name}")
            md_lines.append("")

        md_lines.extend(["## Distribution par Langage", ""])
        for lang, count in lang_dist:
            md_lines.append(f"- **{lang}** : {count}")
        md_lines.append("")

        md_lines.append("---")
        md_lines.append(f"*Généré automatiquement par CyberScan Pro — {date_str}*")

        md_report = "\n".join(md_lines)
        md_filename = reports_dir / f"rapport_{file_date}.md"
        md_filename.write_text(md_report, encoding="utf-8")
        logging.info(f"📄 Rapport Markdown généré : [{md_filename}]")

        lang_rows = ""
        if lang_dist:
            max_lang = lang_dist[0][1]
            colors = ["#6366f1","#10b981","#f59e0b","#ef4444","#06b6d4","#8b5cf6","#ec4899","#14b8a6","#f97316","#84cc16"]
            for i, (lang, count) in enumerate(lang_dist):
                pct = max(5, count / max_lang * 100)
                lang_rows += f'<div class="lang-bar"><span style="width:80px;font-size:0.85rem;color:#94a3b8;">{lang}</span><div class="bar-wrap"><div class="bar-fill" style="width:{pct}%;background:{colors[i % 10]};"></div></div><span class="count">{count}</span></div>'

        flag_rows = ""
        if flagged_repos:
            for name, verdict in flagged_repos:
                color = "#ef4444" if verdict == "Critique" else "#eab308"
                flag_rows += f'<tr><td style="color:{color};font-weight:600;">{verdict}</td><td>{name}</td></tr>'

        top_rows = ""
        for i, (name, stars, _desc, url, lang, updated, verdict) in enumerate(top_repos, 1):
            color = {"Critique": "#ef4444", "Suspect": "#eab308", "Sain": "#22c55e"}.get(verdict, "#64748b")
            badge = verdict or "N/A"
            top_rows += f"""<tr>
                <td>{i}</td>
                <td><a href="{url}" target="_blank" style="color:#818cf8;text-decoration:none;">{name}</a></td>
                <td style="color:#f59e0b;">★{stars:,}</td>
                <td><span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.75rem;background:rgba(99,102,241,0.15);color:#a5b4fc;">{lang or '?'}</span></td>
                <td style="color:{color};font-weight:600;">{badge}</td>
                <td style="color:#94a3b8;font-size:0.8rem;">{(updated or '')[:10]}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CyberScan — Rapport {file_date}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Inter',sans-serif; background:#0a0e17; color:#e2e8f0; min-height:100vh; }}
.wrapper {{ max-width:1200px; margin:0 auto; padding:2rem; }}
h1 {{ font-size:1.75rem; font-weight:800; background:linear-gradient(135deg,#a5b4fc,#6366f1,#8b5cf6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:0.5rem; }}
.subtitle {{ color:#64748b; font-size:0.9rem; margin-bottom:2rem; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:1rem; margin-bottom:2rem; }}
.stat-card {{ background:rgba(17,25,45,0.75); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:1.25rem; backdrop-filter:blur(12px); }}
.stat-card .num {{ font-size:1.5rem; font-weight:700; color:#e2e8f0; }}
.stat-card .label {{ font-size:0.8rem; color:#64748b; margin-top:4px; }}
.card {{ background:rgba(17,25,45,0.75); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:1.5rem; margin-bottom:1.5rem; }}
.card h2 {{ font-size:1.1rem; font-weight:600; margin-bottom:1rem; color:#94a3b8; }}
table {{ width:100%; border-collapse:collapse; font-size:0.85rem; }}
th {{ text-align:left; padding:0.75rem 0.5rem; color:#64748b; font-weight:500; border-bottom:1px solid rgba(255,255,255,0.06); }}
td {{ padding:0.6rem 0.5rem; border-bottom:1px solid rgba(255,255,255,0.03); }}
tr:hover td {{ background:rgba(99,102,241,0.04); }}
a:hover {{ text-decoration:underline !important; }}
.lang-bar {{ display:flex; align-items:center; gap:0.5rem; padding:0.3rem 0; }}
.lang-bar .bar-wrap {{ flex:1; height:6px; background:rgba(255,255,255,0.06); border-radius:3px; overflow:hidden; }}
.lang-bar .bar-fill {{ height:100%; border-radius:3px; }}
.lang-bar .count {{ font-size:0.8rem; color:#64748b; min-width:2rem; text-align:right; }}
.footer {{ text-align:center; padding:2rem 0; color:#475569; font-size:0.8rem; }}
</style>
</head>
<body>
<div class="wrapper">
<h1>CyberScan — Rapport de Scan</h1>
<p class="subtitle">{date_str}</p>
<div class="stats">
<div class="stat-card"><div class="num">{total_repos:,}</div><div class="label">Dépôts</div></div>
<div class="stat-card"><div class="num">{total_stars:,}</div><div class="label">Étoiles</div></div>
<div class="stat-card"><div class="num">{total_langs}</div><div class="label">Langages</div></div>
<div class="stat-card"><div class="num" style="color:#ef4444;">{critique_count}</div><div class="label">Critique</div></div>
<div class="stat-card"><div class="num" style="color:#eab308;">{suspect_count}</div><div class="label">Suspect</div></div>
</div>

<div class="card">
<h2>Top 10</h2>
<table><thead><tr><th>#</th><th>Nom</th><th>Stars</th><th>Langage</th><th>Sécurité</th><th>Mis à jour</th></tr></thead>
<tbody>{top_rows}</tbody></table>
</div>

<div class="card">
<h2>Distribution par Langage</h2>
{lang_rows}
</div>

{'<div class="card"><h2 style="color:#ef4444;">Alertes Sécurité</h2><table><thead><tr><th>Verdict</th><th>Dépôt</th></tr></thead><tbody>' + flag_rows + '</tbody></table></div>' if flag_rows else ''}

<footer class="footer">Généré par CyberScan Pro — {date_str}</footer>
</div>
</body>
</html>"""

        html_filename = reports_dir / f"dashboard_{file_date}.html"
        html_filename.write_text(html, encoding="utf-8")
        logging.info(f"📊 Dashboard HTML généré : [{html_filename}]")

    except Exception as e:
        logging.error(f"❌ Erreur lors de la génération des rapports : {e}")
