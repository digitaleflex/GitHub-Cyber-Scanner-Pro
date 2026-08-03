"""Mission Engine — transforme les decisions en missions tracables avec progression."""
import logging
from datetime import datetime, timezone

from src import database


def create_mission_from_decision(org_id: int, cve_id: str, cve_desc: str = "", cvss: float = 0, reasons: list | None = None) -> dict:
    """Cree une mission a partir d'une decision du Decision Engine."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    title = f"Corriger {cve_id}"
    objective = f"Reduire le risque lie a {cve_id}"
    if cvss >= 9:
        title = f"Urgence : {cve_id}"
        objective = f"Eliminer la menace critique {cve_id}"

    est_min = 15
    if cvss >= 9:
        est_min = 30
    elif cvss < 7:
        est_min = 60

    risk_reduction = min(int(cvss * 5), 40)

    cursor.execute(
        """INSERT INTO missions (org_id, title, description, objective, status, progress,
           estimated_minutes, risk_reduction_percent, cve_ids, responsible)
           VALUES (%s, %s, %s, %s, 'active', 0, %s, %s, %s, 'devsecops')
           RETURNING id""",
        (org_id, title, cve_desc[:500], objective, est_min, risk_reduction, cve_id),
    )
    mission_id = cursor.fetchone()[0]

    steps = _generate_steps(cve_id, cvss)
    for i, step in enumerate(steps):
        cursor.execute(
            """INSERT INTO mission_steps (mission_id, step_order, title, description, status, action_type, estimated_minutes)
               VALUES (%s, %s, %s, %s, 'pending', %s, %s)""",
            (mission_id, i + 1, step["title"], step.get("desc", ""), step.get("action_type", "patch"), step.get("est", 5)),
        )

    conn.commit()
    cursor.close()
    conn.close()
    return {"mission_id": mission_id, "title": title, "steps": len(steps), "risk_reduction": risk_reduction}


def _generate_steps(cve_id: str, cvss: float) -> list[dict]:
    steps = [
        {"title": f"Verifier l'impact de {cve_id}", "desc": "Identifier les actifs concernes", "action_type": "assess", "est": 5},
        {"title": f"Consulter l'avis de securite pour {cve_id}", "desc": "NVD + bulletin editeur", "action_type": "research", "est": 5},
    ]
    if cvss >= 7:
        steps.append({"title": f"Appliquer le correctif pour {cve_id}", "desc": "Mettre a jour les systemes concernes", "action_type": "patch", "est": 10})
    else:
        steps.append({"title": f"Planifier le correctif pour {cve_id}", "desc": "Programmer dans le cycle de maintenance", "action_type": "schedule", "est": 5})
    steps.append({"title": f"Verifier la correction de {cve_id}", "desc": "Scanner pour confirmer la resolution", "action_type": "verify", "est": 5})
    return steps


def get_missions(org_id: int | None = None, status: str | None = None, limit: int = 20) -> list[dict]:
    conn = database.get_db_connection()
    cursor = conn.cursor()
    query = """SELECT id, title, description, objective, status, progress, estimated_minutes,
                      risk_reduction_percent, cve_ids, responsible, created_at, started_at, completed_at
               FROM missions WHERE 1=1"""
    params = []
    if org_id:
        query += " AND org_id = %s"
        params.append(org_id)
    if status:
        if "," in status:
            statuses = [s.strip() for s in status.split(",")]
            query += f" AND status = ANY(%s)"
            params.append(statuses)
        else:
            query += " AND status = %s"
            params.append(status)
    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_row_to_mission(r) for r in rows]


def get_mission(mission_id: int) -> dict | None:
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, title, description, objective, status, progress, estimated_minutes,
                  risk_reduction_percent, cve_ids, responsible, created_at, started_at, completed_at
           FROM missions WHERE id = %s""",
        (mission_id,),
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return None
    mission = _row_to_mission(row)
    cursor.execute(
        "SELECT id, step_order, title, description, status, action_type, estimated_minutes, completed_at FROM mission_steps WHERE mission_id = %s ORDER BY step_order",
        (mission_id,),
    )
    mission["steps"] = [_step_to_dict(r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return mission


def start_mission(mission_id: int) -> dict:
    conn = database.get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc)
    cursor.execute("UPDATE missions SET status = 'in_progress', started_at = %s WHERE id = %s AND status = 'active'", (now, mission_id))
    updated = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return {"started": updated > 0}


def complete_step(mission_id: int, step_id: int) -> dict:
    conn = database.get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc)
    cursor.execute(
        "UPDATE mission_steps SET status = 'done', completed_at = %s WHERE id = %s AND mission_id = %s AND status = 'pending'",
        (now, step_id, mission_id),
    )
    updated = cursor.rowcount
    if updated:
        cursor.execute("SELECT COUNT(*) FROM mission_steps WHERE mission_id = %s", (mission_id,))
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM mission_steps WHERE mission_id = %s AND status = 'done'", (mission_id,))
        done = cursor.fetchone()[0]
        progress = int(done / total * 100) if total > 0 else 0
        cursor.execute("UPDATE missions SET progress = %s WHERE id = %s", (progress, mission_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"step_done": updated > 0}


def complete_mission(mission_id: int) -> dict:
    conn = database.get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc)
    cursor.execute(
        "UPDATE missions SET status = 'completed', progress = 100, completed_at = %s WHERE id = %s",
        (now, mission_id),
    )
    updated = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return {"completed": updated > 0}


def _row_to_mission(row) -> dict:
    return {
        "id": row[0], "title": row[1], "description": row[2] or "", "objective": row[3] or "",
        "status": row[4], "progress": row[5], "estimated_minutes": row[6],
        "risk_reduction_percent": row[7], "cve_ids": row[8] or "", "responsible": row[9] or "",
        "created_at": str(row[10]) if row[10] else None, "started_at": str(row[11]) if row[11] else None,
        "completed_at": str(row[12]) if row[12] else None,
    }


def _step_to_dict(row) -> dict:
    return {
        "id": row[0], "step_order": row[1], "title": row[2], "description": row[3] or "",
        "status": row[4], "action_type": row[5] or "", "estimated_minutes": row[6],
        "completed_at": str(row[7]) if row[7] else None,
    }
