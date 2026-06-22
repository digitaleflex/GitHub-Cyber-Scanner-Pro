"""
Genere le rapport hebdomadaire en markdown.
"""

import json
import os
from datetime import datetime


def generate():
    try:
        with open("data/last_scan.json") as f:
            repos = json.load(f)
    except:
        print("Pas de donnees. Lance scan.py d'abord.")
        return

    repos.sort(key=lambda r: r["stars"], reverse=True)

    now = datetime.now()
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)
    filename = f"{report_dir}/rapport_{now.strftime('%Y%m%d')}.md"

    lines = []
    lines.append(f"# CyberScan — Rapport Hebdomadaire")
    lines.append(f"**{now.strftime('%d %B %Y')}**\n")
    lines.append(f"## Resume")
    lines.append(f"- Nouveaux outils decouverts : **{len(repos)}**")
    lines.append(f"- Etoiles totales : **{sum(r['stars'] for r in repos)}**")
    lines.append(f"")

    # Top 10
    lines.append(f"## Top 10\n")
    for i, r in enumerate(repos[:10], 1):
        lines.append(f"### {i}. [{r['name']}]({r['url']})")
        lines.append(f"★ {r['stars']} | {r['lang'] or '?'} | Mis a jour: {r['updated'][:10]}")
        lines.append(f"")
        lines.append(f">{r['desc']}")
        lines.append(f"")

    # Par langue
    langs = {}
    for r in repos:
        lang = r["lang"] or "Inconnu"
        langs[lang] = langs.get(lang, 0) + 1

    lines.append(f"## Par langage\n")
    for lang, count in sorted(langs.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"- **{lang}** : {count} outils")

    lines.append(f"\n---")
    lines.append(f"*Genere automatiquement par CyberScan*")

    report = "\n".join(lines)

    with open(filename, "w") as f:
        f.write(report)

    print(report)
    print(f"\nRapport sauvegarde: {filename}")


if __name__ == "__main__":
    generate()
