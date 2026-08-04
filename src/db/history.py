import json
import logging
import src.db.connection as _conn


def record_snapshot(cve_id: str, score: int, level: str, factors: dict,
                    profile_id: int | None = None):
    """Enregistre un snapshot de decision (appele depuis priority/cves)."""
    conn = _conn.get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO decision_history (cve_id, score, level, factors, profile_id)
           VALUES (%s, %s, %s, %s, %s)""",
        (cve_id.upper(), score, level, json.dumps(factors or {}), profile_id),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_history(cve_id: str, days: int = 30):
    """Retourne l'historique des scores d'une CVE sur N jours."""
    conn = _conn.get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT score, level, snapshot_at
           FROM decision_history WHERE cve_id = %s
             AND snapshot_at >= NOW() - INTERVAL '%s days'
           ORDER BY snapshot_at ASC""",
        (cve_id.upper(), days),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"score": r[0], "level": r[1], "at": r[2].isoformat() if r[2] else None} for r in rows]


def get_org_risk_trend(profile_id: int, days: int = 30):
    """Score de risque agrege par jour pour une organisation."""
    conn = _conn.get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT DATE(snapshot_at) AS day, AVG(score)::INT AS avg_score,
                  COUNT(*) AS cves_tracked
           FROM decision_history
           WHERE profile_id = %s AND snapshot_at >= NOW() - INTERVAL '%s days'
           GROUP BY day ORDER BY day ASC""",
        (profile_id, days),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {
        "trend": [{"day": str(r[0]), "score": r[1], "cves": r[2]} for r in rows],
        "current": rows[-1][1] if rows else None,
        "previous": rows[-2][1] if len(rows) > 1 else None,
    }
