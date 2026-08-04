import logging
import src.db.connection as _conn


def save_analysis(cve_id: str, analysis: dict, model: str = ""):
    """Persiste l'analyse IA d'une CVE dans la table dediee cve_analysis."""
    conn = _conn.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO cve_analysis
                (cve_id, summary, impact, recommendation, patched_in, exploitation_likelihood, audience, model)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cve_id) DO UPDATE SET
                summary = EXCLUDED.summary,
                impact = EXCLUDED.impact,
                recommendation = EXCLUDED.recommendation,
                patched_in = EXCLUDED.patched_in,
                exploitation_likelihood = EXCLUDED.exploitation_likelihood,
                audience = EXCLUDED.audience,
                model = EXCLUDED.model,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                cve_id,
                (analysis.get("summary") or "")[:4000],
                (analysis.get("impact") or "")[:4000],
                (analysis.get("recommendation") or "")[:4000],
                (analysis.get("patched_in") or "")[:200] or None,
                (analysis.get("exploitation_likelihood") or "")[:20] or None,
                (analysis.get("audience") or "")[:100] or None,
                model or None,
            ),
        )
        conn.commit()
    except Exception as e:
        logging.error(f"Erreur save analysis {cve_id}: {e}")
    finally:
        cursor.close()
        conn.close()


def get_analysis(cve_id: str):
    conn = _conn.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT summary, impact, recommendation, patched_in,
                   exploitation_likelihood, audience, model, created_at
            FROM cve_analysis WHERE cve_id = %s
            """,
            (cve_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "cve_id": cve_id,
            "summary": row[0],
            "impact": row[1],
            "recommendation": row[2],
            "patched_in": row[3],
            "exploitation_likelihood": row[4],
            "audience": row[5],
            "model": row[6],
            "created_at": str(row[7]) if row[7] else None,
        }
    except Exception as e:
        logging.error(f"Erreur get analysis {cve_id}: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def count_analysis():
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cve_analysis")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return -1
