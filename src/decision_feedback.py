"""Feedback sur les decisions (fondation calibration).

But : rendre la priorisation mesurable et recalibrable. Chaque retour utilisateur
(patche / ignore / faux positif / exploite) est historise avec le score et le risque
de faux positif au moment de la decision. Ces donnees permettent ensuite d'ajuster
les pondérations ou d'entrainer un modele supervise.
"""
import logging
from datetime import datetime, timedelta

from src.database import get_db_connection

VALID_ACTIONS = {"patched", "not_relevant", "ignored", "exploitable", "false_positive"}


def record_feedback(cve_id: str, action: str, decision_score: int | None = None,
                    fp_risk_at_decision: float | None = None, comment: str | None = None,
                    user_ref: str | None = None, applied_patch: bool | None = None,
                    was_exploited: bool | None = None, source: str = "api") -> dict:
    """Enregistre un feedback sur une decision. Retourne {status, id} ou erreur."""
    action = (action or "").strip().lower()
    if not action or action not in VALID_ACTIONS:
        return {"status": "error", "error": f"action invalide, attendu: {sorted(VALID_ACTIONS)}"}
    if not cve_id:
        return {"status": "error", "error": "cve_id requis"}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO decision_feedback
               (cve_id, decision_score, action, comment, user_ref,
                fp_risk_at_decision, applied_patch, was_exploited, source)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (cve_id.upper(), decision_score, action, (comment or "")[:2000],
             (user_ref or "")[:100], fp_risk_at_decision, applied_patch,
             was_exploited, (source or "api")[:50]),
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "ok", "id": row[0] if row else None}
    except Exception as e:
        logging.error(f"decision_feedback: {e}")
        return {"status": "error", "error": str(e)}


def get_feedback_stats(days: int = 30) -> dict:
    """Agregats de feedback pour la calibration (precision observee, actions)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    since = datetime.utcnow() - timedelta(days=days)

    cursor.execute(
        """SELECT action, COUNT(*) FROM decision_feedback
           WHERE created_at >= %s GROUP BY action ORDER BY 2 DESC""",
        (since,),
    )
    by_action = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) FROM decision_feedback WHERE created_at >= %s", (since,))
    row = cursor.fetchone()
    total = row[0] if row else 0

    cursor.execute(
        """SELECT
             COUNT(*) FILTER (WHERE applied_patch),
             COUNT(*) FILTER (WHERE was_exploited)
           FROM decision_feedback WHERE created_at >= %s""",
        (since,),
    )
    row = cursor.fetchone()
    patches = row[0] if row else 0
    exploited = row[1] if row else 0
    cursor.close()
    conn.close()

    fp = by_action.get("false_positive", 0)
    precision = round(1 - (fp / total), 3) if total else None
    return {
        "window_days": days,
        "total": total,
        "by_action": by_action,
        "false_positive_rate": round(fp / total, 3) if total else 0,
        "observed_precision": precision,
        "patched_count": patches,
        "exploited_count": exploited,
        "not_enough_data": total < 10,
    }
