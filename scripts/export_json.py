"""
Export JSON complet de TOUTES les tables de contenu du Cyber-Scanner-Pro.

Usage:
    python scripts/export_json.py                    # -> data/exports/cyber_export_<stamp>.json
    python scripts/export_json.py /chemin/export.json

Fonctionne aussi via: docker exec cyber_github_scanner python scripts/export_json.py
"""

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, "/app")

import src.database as database

# Tables de contenu exportees. etag_cache (metadata de cache HTTP) est exclu.
TABLES = [
    "repositories",
    "cve_entries",
    "discovered_keywords",
    "resources",
    "resource_chunks",
    "security_intel",
    "sources",
    "books",
    "repo_commits",
    "repo_issues",
]


def export_all(output_path: str) -> dict:
    conn = database.get_db_connection()
    cursor = conn.cursor()
    payload = {"data": {}}
    for table in TABLES:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
            for row in rows:
                for k, v in list(row.items()):
                    if hasattr(v, "isoformat"):
                        row[k] = v.isoformat()
                    elif isinstance(v, bytes):
                        row[k] = v.decode("utf-8", errors="replace")
            payload["data"][table] = rows
        except Exception as e:
            print(f"⚠️  Table {table} ignorée: {e}")
            payload["data"][table] = []
    cursor.close()
    conn.close()

    payload["exported_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload["counts"] = {t: len(rows) for t, rows in payload["data"].items()}
    payload["total_rows"] = sum(payload["counts"].values())

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return payload


if __name__ == "__main__":
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    default = f"/app/data/exports/cyber_export_{stamp}.json"
    path = sys.argv[1] if len(sys.argv) > 1 else default
    payload = export_all(path)
    print(f"✅ Export JSON complet: {path}")
    for t, n in payload["counts"].items():
        if n:
            print(f"   {t}: {n}")
    print(f"   TOTAL: {payload['total_rows']} lignes")
