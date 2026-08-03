import logging
import src.db.connection as _conn



def save_cve_entries(entries):
    if not entries:
        return 0
    conn = _conn.get_db_connection()
    cursor = conn.cursor()
    count = 0
    for e in entries:
        cve_id = e.get("cve_id")
        if not cve_id:
            continue
        try:
            cursor.execute(
                """
                INSERT INTO cve_entries
                    (cve_id, description, published, last_modified, severity, cvss_score, references_urls, weaknesses)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (cve_id) DO UPDATE SET
                    description = COALESCE(EXCLUDED.description, cve_entries.description),
                    published = COALESCE(EXCLUDED.published, cve_entries.published),
                    last_modified = COALESCE(EXCLUDED.last_modified, cve_entries.last_modified),
                    severity = COALESCE(EXCLUDED.severity, cve_entries.severity),
                    cvss_score = COALESCE(EXCLUDED.cvss_score, cve_entries.cvss_score),
                    references_urls = COALESCE(EXCLUDED.references_urls, cve_entries.references_urls),
                    weaknesses = COALESCE(EXCLUDED.weaknesses, cve_entries.weaknesses)
                """,
                (
                    cve_id,
                    e.get("description", "")[:8000],
                    e.get("published"),
                    e.get("last_modified"),
                    e.get("severity"),
                    e.get("cvss_score"),
                    e.get("references_urls", ""),
                    e.get("weaknesses", ""),
                )
            )
            if cursor.rowcount > 0:
                count += 1
        except Exception as ex:
            logging.error(f"Erreur save CVE {cve_id}: {ex}")
    conn.commit()
    cursor.close()
    conn.close()
    return count

def search_cves(q: str = "", severity: str = "", page: int = 1, per_page: int = 20):
    conn = _conn.get_db_connection()
    cursor = conn.cursor()
    conditions = []
    params = []
    if q:
        conditions.append(
            "(cve_id ILIKE %s OR description ILIKE %s OR weaknesses ILIKE %s)"
        )
        like = f"%{q}%"
        params.extend([like, like, like])
    if severity:
        conditions.append("severity = %s")
        params.append(severity)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    count_sql = f"SELECT COUNT(*) FROM cve_entries {where}"
    cursor.execute(count_sql, params)
    total = cursor.fetchone()[0]
    offset = (page - 1) * per_page
    data_sql = f"""
        SELECT cve_id, description, published, last_modified, severity, cvss_score, weaknesses
        FROM cve_entries {where}
        ORDER BY published DESC NULLS LAST, cvss_score DESC NULLS LAST
        LIMIT %s OFFSET %s
    """
    cursor.execute(data_sql, params + [per_page, offset])
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    cves = [
        {
            "cve_id": r[0],
            "description": (r[1][:500] + "...") if r[1] and len(r[1]) > 500 else (r[1] or ""),
            "published": str(r[2]) if r[2] else None,
            "last_modified": str(r[3]) if r[3] else None,
            "severity": r[4] or "",
            "cvss_score": r[5],
            "weaknesses": (r[6] or "").split(",") if r[6] else [],
        }
        for r in rows
    ]
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, (total + per_page - 1) // per_page),
        "cves": cves,
    }
